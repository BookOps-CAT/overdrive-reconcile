"""
Scrape Overdrive website for license data to validate list of resources to be deleted.
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


def scrape(library: str, src_fh: str, start: int = 0) -> None:
    """
    Launches web scraping of OverDrive catalog from `reconcile` `webscrape` command.

    Args:
        library: 'NYPL' or 'BPL'
        src_fh: path to file containing reserve IDs to be verified.
        start: the first row within `src_fh` containing the ID to be verified

    Returns:
        None. Reserve IDs for records to be deleted from Sierra is written to
        '{library}-FINAL-for-deletion-verified-resources.csv' and records which were
        falsely identified are written to '{library}-false-positives-for-deletion.csv'.
    """
    with open(src_fh, "r") as count:
        total = sum(1 for line in count)
    dst_fh = create_dst_csv_fh(library, "FINAL-for-deletion-verified-resources")
    reject_fh = create_dst_csv_fh(library, "false-positives-for-deletion")

    with open(src_fh, "r") as src:
        reader = csv.reader(src)

        n = 1
        for row in reader:
            if n >= start:
                url = row[2]
                page = get_html(url, n, total)
                if not page:
                    row.append("removed")
                    save2csv(dst_fh, row)
                else:
                    status = get_ebook_status(page)
                    if status.for_removal is True:
                        row.append("expired")
                        save2csv(dst_fh, row)
                    else:
                        save2csv(reject_fh, row)
            n += 1
            time.sleep(0.5)


def get_ebook_status(html: bytes) -> EbookStatus:
    """
    Parses HTML to determine whether the resource is still available.

    The parser first searches for a significant portion of metadata in the document
    head before interpreting other portions of the html to determine whether the
    resource is still available or should be deleted.

    Args:
        html: `bytes` object from `requests.Response.content`

    Returns:
        `EbookStatus` object containing significant metadata for resource.
    """

    ebook_status = EbookStatus()
    soup = BeautifulSoup(html, "html.parser", from_encoding="utf-8")
    scripts = soup.find_all("script")
    for s in scripts:
        m = P.match(str(s))
        if m:
            return update_status(m.group(1), ebook_status)
    ebook_status.for_removal = True
    return ebook_status


def get_html(
    url: str, n: int, total: int, agent: str = "bookops/NYPL"
) -> Optional[bytes]:
    """
    Retrieves HTML for a given url.

    Args:
        url:
            URL to be requested
        n:
            The sequence number for the resource (ie. the row number from the input csv)
            to be used in a log message.
        total:
            The total number of resources to be requested (ie. the total number of rows
            in the input csv) to be used in a log message.
        agent:
            agent to be added to the header of the request. Default is 'bookops/NYPL'

    Returns:
        HTML data as a `bytes` object from the `requests.Response.content` attribute
        if the request is successful. Returns `None` if the request returns a 4xx
        response.

    Raises:
        `requests.exceptions.Timeout` if the request times out.
    """

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
    Searches for significant data within a string extracted from HTML head.script
    tag to determine the current status of an eBook. A resource should not have its
    record deleted from Sierra if its HTML contains '"availabilityType":"always"',
    '"isPreReleaseTitle":true', or '"ownedCopies":' with a value greater than zero.

    Args:
        metadata:
            a string extracted from the HTML head.script tag to be parsed for
            significant metadata
        ebook_status: `EbookStatus` object

    Returns:
        An `EbookStatus` object
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
