import argparse
import logging
import logging.config
import sys

from overdrive_reconcile.reconcile import reconcile
from overdrive_reconcile.utils import date_subdirectory, logger_dict_config
from overdrive_reconcile.webscraper import scrape


def main(args: list) -> None:
    config = logger_dict_config()
    logging.config.dictConfig(config)

    parser = argparse.ArgumentParser(
        prog="Overdrive-Reconcile",
        description="Sets of scripts reconciling records between Sierra "
        "and OverDrive platform.",
    )

    parser.add_argument(
        "action",
        help=(
            "'reconcile' runs entire set of scripts | "
            "'webscrape' runs only webscraping of OverDrive catalog | "
        ),
        type=str,
        choices=["reconcile", "webscrape"],
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
            scrape(pargs.library, src_fh, pargs.start)
        else:
            scrape(pargs.library, pargs.source, pargs.start)


if __name__ == "__main__":
    main(sys.argv[1:])
