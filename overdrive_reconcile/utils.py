import csv
import os
import re
from datetime import datetime

P = re.compile(r"^.{8}-.{4}-.{4}-.{4}-.{12}")
URL_NYPL = "http://ebooks.nypl.org/ContentDetails.htm?ID="
URL_BPL = "http://digitalbooks.brooklynpubliclibrary.org/ContentDetails.htm?ID="


def count_rows(fh: str) -> int:
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


def create_dst_csv_fh(library: str, name: str) -> str:
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


def save2csv(dst_fh: str, row: list[str]) -> None:
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


def logger_dict_config() -> dict:
    """Create a dictionary to configure logger."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "basic": {
                "format": "%(app)s-%(asctime)s-%(filename)s-%(lineno)d-%(levelname)s-%(message)s",  # noqa: E501
                "defaults": {"app": "overdrive_reconcile"},
            },
        },
        "handlers": {
            "stream": {
                "class": "logging.StreamHandler",
                "formatter": "basic",
                "level": "DEBUG",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "basic",
                "level": "DEBUG",
                "filename": "overdrive_reconcile.log",
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
            },
        },
        "loggers": {
            "overdrive_reconcile": {
                "handlers": ["stream", "file"],
                "level": "DEBUG",
                "propagate": True,
            },
        },
    }
