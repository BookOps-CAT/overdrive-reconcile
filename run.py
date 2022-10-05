import argparse
import sys

from overdrive_reconcile.reconcile import reconcile
from overdrive_reconcile.utils import date_subdirectory, count_rows
from overdrive_reconcile.webscraper import scrape, check_status


def main(args: list) -> None:

    # process: str: library: str, src_fh: str)

    parser = argparse.ArgumentParser(
        prog="Overdrive-Reconcile",
        description="Sets of scripts reconciling records between Sierra and OverDrive platform.",
    )

    parser.add_argument(
        "action",
        help=(
            "'reconcile' runs entire set of scripts | "
            "'webscrape' runs only webscraping of OverDrive catalog | "
            "'check-overdrive' runs scraping for a single resource"
        ),
        type=str,
        choices=["reconcile", "webscrape", "check-overdrive"],
    )
    parser.add_argument(
        "library", help="'BPL' or 'NYPL'", type=str, choices=["BPL", "NYPL"]
    )
    parser.add_argument(
        "source",
        help="Sierra export or csv for webscraping source file handle",
        type=str,
    )

    parser.add_argument(
        "start",
        help="Starting row of data to be verified.",
        type=int,
        nargs="?",
        default=0,
    )

    pargs = parser.parse_args(args)

    if pargs.action == "reconcile":
        reconcile(pargs.library, pargs.source)
    if pargs.action == "webscrape":
        if pargs.source == "default":
            # assume today's file
            work_dir = date_subdirectory(pargs.library)
            src_fh = (
                f"{work_dir}/{pargs.library}-for-deletion-verification-required.csv"
            )
            total = count_rows(src_fh) - 1
            scrape(pargs.library, src_fh, total, pargs.start)
        else:
            total = count_rows(pargs.source) - 1
            scrape(pargs.library, pargs.source, total, pargs.start)

    if pargs.action == "check-overdrive":
        print(f"Checking status of {pargs.source} on OverDrive platform...")
        check_status(pargs.source, pargs.library)


if __name__ == "__main__":
    main(sys.argv[1:])
