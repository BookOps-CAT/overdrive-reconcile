"""
Use to validate Sierra-Overdrive API deletions
"""

import csv
import logging
import re
import time
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup
from requests.exceptions import Timeout

from overdrive_reconcile.utils import create_dst_csv_fh, save2csv

logger = logging.getLogger(__name__)
# regex patterns for significant pieces of info
P = re.compile(r".*window.OverDrive.mediaItems = (\{.*\}\});.*", re.DOTALL)
P_IS_PRERELEASE = re.compile(r'.*"isPreReleaseTitle":true,".*', re.DOTALL)
P_AVAILABLE = re.compile(r'.*"isAvailable":true,".*', re.DOTALL)
P_ALWAYS_AVAILABLE = re.compile(r'.*"availabilityType":"always".*', re.DOTALL)
P_OWNED_COPIES = re.compile(r'.*"ownedCopies":(\d{1,}),".*', re.DOTALL)


@dataclass
class EbookStatus:
    always_available: Optional[bool] = None
    available: Optional[bool] = None
    copies_owned: str = ""
    for_removal: Optional[bool] = None
    prerelease: Optional[bool] = None


def scrape(library: str, src_fh: str, total: int, start: int = 0) -> None:
    """
    Launches web scraping of OverDrive catalog

    Args:
        library:                library code
        src_fh:                 source data file handle
        total:                  number of total resources to check
    """
    dst_fh = create_dst_csv_fh(library, "FINAL-for-deletion-verified-resources")
    reject_fh = create_dst_csv_fh(library, "false-positives-for-deletion")

    with open(src_fh, "r") as src:
        reader = csv.reader(src)

        n = 1
        for row in reader:
            if n >= start:
                bib_no = row[0]
                url = row[2]
                page = get_html(url, n, total)
                if not page:
                    row.append("removed")
                    save2csv(dst_fh, row)
                else:
                    status = get_ebook_status(bib_no, page)
                    if status.for_removal is True:
                        row.append("expired")
                        save2csv(dst_fh, row)
                    else:
                        save2csv(reject_fh, row)
            n += 1


def get_ebook_status(bid: str, html: bytes) -> EbookStatus:
    """
    parses HTML, finds significant portion of metadata in document head, and
    interprets important bits, such as availability of ebook, ownership,
    available copies, and own copies by the library

    args:
        html: response.content
    returns:
        (available, owned, copies_available, copies_owned): namedtuple
    """

    ebook_status = EbookStatus()
    found = False
    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script")
    for s in scripts:
        m = P.match(str(s))
        if m:
            metadata = m.group(1)
            found = True
            break
    if found:
        ebook_status = update_status(metadata, ebook_status)
    else:
        with open("./temp/missing/{}.html".format(bid), "w") as file:
            file.write(str(html))
    return ebook_status


def get_html(
    url: str, n: int, total: int, agent: str = "bookops/NYPL"
) -> Optional[bytes]:
    """
    retrieves html code from given url
    args:
        url:                    URL of a page to be requested
        agent:                  agent header of the request
        n:                      resource sequence #
        total:                  total number of resources to request
    returns:
        page
    """
    # slow things down a bit
    time.sleep(0.5)

    headers = {"user-agent": agent}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        logger.debug(
            f"({n} of {total}) Requested page: {response.url} == {response.status_code}"
        )
    except Timeout:
        raise

    if response.status_code == requests.codes.ok:
        return response.content
    else:
        return None


def update_status(metadata: str, ebook_status: EbookStatus) -> EbookStatus:
    """
    finds significant data in html.head.script
    args:
        html_head_script: str
        ebook_status: namedtuple

    returns:
        updated ebook_status
    """

    # title availability
    match_availability = P_AVAILABLE.match(metadata)
    if match_availability:
        ebook_status.available = True
    else:
        ebook_status.available = False
    # always available
    match_always_available = P_ALWAYS_AVAILABLE.match(metadata)
    if match_always_available:
        ebook_status.always_available = True

    # copies owned
    match_copies_owned = P_OWNED_COPIES.match(metadata)
    if match_copies_owned:
        ebook_status.copies_owned = match_copies_owned.group(1)

    # prerelease
    match_prerelease = P_IS_PRERELEASE.match(metadata)
    if match_prerelease:
        ebook_status.prerelease = True

    if ebook_status.always_available is True:
        ebook_status.for_removal = False
        return ebook_status
    if ebook_status.copies_owned.isnumeric() and int(ebook_status.copies_owned) > 0:
        ebook_status.for_removal = False
        return ebook_status
    if ebook_status.prerelease:
        ebook_status.for_removal = False
    else:
        ebook_status.for_removal = True
    return ebook_status
