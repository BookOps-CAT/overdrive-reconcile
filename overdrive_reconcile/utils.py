import csv
from datetime import datetime
import os
import re


P = re.compile(r"^.{8}-.{4}-.{4}-.{4}-.{12}")
URL_NYPL = "http://ebooks.nypl.org/ContentDetails.htm?ID="
URL_BPL = "http://digitalbooks.brooklynpubliclibrary.org/ContentDetails.htm?ID="


def counted(f):
    def wrapped(*args, **kwargs):
        wrapped.calls += 1
        return f(*args, **kwargs)

    wrapped.calls = 0
    return wrapped


def count_rows(fh: str):
    with open(fh, "r") as f:
        return sum(1 for line in f)


def dst_main_directory(library: str) -> str:
    """
    Main directory for report files resulting from
    the reconciliation process.
    """
    return f"./files/{library}"


def date_subdirectory(library: str) -> str:
    today = datetime.now().date()

    main_dir = dst_main_directory(library)

    date_dir = f"{main_dir}/{today}"

    if not os.path.exists(date_dir):
        os.makedirs(date_dir)

    return date_dir


def create_dst_csv_fh(library: str, name: str):
    """
    Creates csv file handle

    Args:
        library:                library code to prefix file handle
        name:                   file name
    """

    dst_dir = date_subdirectory(library)
    out = f"{dst_dir}/{library}-{name}.csv"
    return out


def is_reserve_id(i: str) -> bool:
    """
    Identifies if passed string is a OverDrive Reserve ID or not

    Args:
        i:                  id string to be evaluated

    Returns:
        bool
    """
    if re.match(P, i):
        return True
    else:
        return False


def save2csv(dst_fh, row):
    """
    Appends a list with data to a dst_fh csv
    args:
        dst_fh: str, output file
        row: list, list of values to write in a row
    """

    with open(dst_fh, "a", encoding="utf-8") as csvfile:
        out = csv.writer(
            csvfile,
            delimiter=",",
            lineterminator="\n",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        out.writerow(row)
