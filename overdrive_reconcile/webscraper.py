"""
Use to validate Sierra-SimplyE deletions
"""
from collections import namedtuple
import csv
import re
import time

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, Timeout

from overdrive_reconcile.utils import save2csv, create_dst_csv_fh


# regex patterns for significant pieces of info
P = re.compile(r".*window.OverDrive.mediaItems = (\{.*\}\});.*", re.DOTALL)
P_AVAILABLE = re.compile(r'.*"isAvailable":(true|false),".*', re.DOTALL)
P_OWNED = re.compile(r'.*"isOwned":(true|false),".*', re.DOTALL)
P_AVAILABLE_COPIES = re.compile(r'.*"availableCopies":(\d{1,}),".*', re.DOTALL)
P_ALWAYS_AVAILABLE = re.compile(r'.*"availabilityType":"always".*', re.DOTALL)
P_OWNED_COPIES = re.compile(r'.*"ownedCopies":(\d{1,}),".*', re.DOTALL)


# ebook status data construct
EbookStatus = namedtuple(
    "EbookStatus",
    [
        "available",
        "owned",
        "always_available",
        "copies_available",
        "copies_owned",
        "for_removal",
    ],
)
EbookStatus.__new__.__defaults__ = (None, None, None, None, None, None)


def scrape(library: str, src_fh: str, total: int) -> None:
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
        next(reader)  # skip header

        n = 0
        for row in reader:
            n += 1
            bib_no = row[0]
            url = row[2]
            page = get_html(url, n, total)
            if not page:
                row.append("removed")
                save2csv(dst_fh, row)
            else:
                status = get_ebook_status(None, bib_no, page)
                if is_purgable(status):
                    row.append("expired")
                    save2csv(dst_fh, row)
                else:
                    save2csv(reject_fh, row)


def get_ebook_status(oid, bid, html):
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


def make_request(url, n, total, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(
            f"({n} of {total}) Requested page: {response.url} == {response.status_code}"
        )
        return response
    except Timeout:
        print("Server timed out. Restarting in 15 sec...")
        time.sleep(15)
        make_request(url, headers)


def get_html(url: str, n: int, total: int, agent: str = "bookops/NYPL") -> bytes:
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

    response = make_request(url, n, total, headers)

    if response.status_code == requests.codes.ok:
        return response.content
    else:
        return None


def is_purgable(ebook_status: EbookStatus) -> bool:
    """
    Checks if status or own copies elements indicate the resource
    can be deleted or not.

    Args:
        ebook_status:               named tuple with status data

    Returns:
        bool
    """
    if ebook_status.always_available is True:
        return False
    elif ebook_status.copies_owned:
        try:
            copies = int(ebook_status.copies_owned)
            if not copies:
                return True
            else:
                return False
        except ValueError:
            return True
        except TypeError:
            return True
    else:
        return True


def update_status(metadata, ebook_status):
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
        available = match_availability.group(1)
        if available == "true":
            available = True
        elif available == "false":
            available = False
        else:
            available = None
        ebook_status = ebook_status._replace(available=available)

    # title owned
    match_owned = P_OWNED.match(metadata)
    if match_owned:
        owned = match_owned.group(1)
        if owned == "true":
            owned = True
        elif owned == "false":
            owned = False
        else:
            owned = None
        ebook_status = ebook_status._replace(owned=owned)

    # always available
    match_always_available = P_ALWAYS_AVAILABLE.match(metadata)
    if match_always_available:
        ebook_status = ebook_status._replace(always_available=True)

    # copies available
    match_copies_available = P_AVAILABLE_COPIES.match(metadata)
    if match_copies_available:
        ebook_status = ebook_status._replace(
            copies_available=match_copies_available.group(1)
        )

    # copies owned
    match_copies_owned = P_OWNED_COPIES.match(metadata)
    if match_copies_owned:
        ebook_status = ebook_status._replace(copies_owned=match_copies_owned.group(1))

    for_removal = is_purgable(ebook_status)
    ebook_status = ebook_status._replace(for_removal=for_removal)

    return ebook_status


if __name__ == "__main__":
    import sys

    scrape(sys.argv[1], sys.argv[2], sys.argv[3])
