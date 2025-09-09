"""The main module that runs the reconciliation process."""

import logging
import os

import pandas as pd

from .overdrive_session import (
    get_inventory,
    get_overdrive_api_creds,
    verify_missing_resources,
)
from .prep import prep_reserve_ids_in_sierra_export
from .utils import date_subdirectory
from .webscraper import scrape

logger = logging.getLogger(__name__)


def dedup_on_reserve_id(library: str, df: pd.DataFrame, subdir: str) -> None:
    """
    Deduplicates given dataframe on reserve ID leaving the latest record.
    Does not consider the situation where a single bib record contains duplicate
    reserve IDs.

    Args:
        library: 'NYPL' or 'BPL'
        df: `pandas.DataFrame` object to deduplicate
        subdir: directory where output .csv files will be written

    Returns:
        None. Bib IDs for records containing duplicate reserve IDs are written to
        '{library}-FINAL-duplicate-reserveid-sierra.csv'. Unique reserve IDs are
        written to '{library}-unique-reserveid-sierra.csv'.
    """
    dups_fh = f"{subdir}/{library}-FINAL-duplicate-reserveid-sierra.csv"
    unique_fh = f"{subdir}/{library}-unique-reserveid-sierra.csv"

    ddf = df[df.duplicated(subset=["reserve_id"], keep="last")]
    ddf.to_csv(dups_fh, index=False, header=False, columns=["bib_no", "reserve_id"])
    logger.info(
        f"Identified {ddf.shape[0]} duplicate record(s) in Sierra export. "
        f"Report saved to: {dups_fh}"
    )

    udf = df.drop_duplicates(subset=["reserve_id"], keep="last")
    udf.to_csv(unique_fh, index=False, header=False, columns=["bib_no", "reserve_id"])
    logger.info(
        f"Identified {udf.shape[0]} unique reserve ID(s) in Sierra export. "
        f"Report saved to: {unique_fh}"
    )


def reconcile(library: str, sierra_export_fh: str) -> None:
    """
    Launches reconciliation process for `reconcile` command in `run.py`.

    Args:
        library:
            'NYPL' or 'BPL'
        sierra_export_fh:
            path to .txt file containing bib IDs and reserve IDs exported from Sierra

    Returns:
        None. Output is written to .csv files in 'files/{library}/{date}/'.
    """
    # load api creds into envars
    get_overdrive_api_creds(library=library)

    # create directory for output files
    subdir = date_subdirectory(library)
    logger.debug(f"All output reports will be saved to {subdir}.")

    avail_fh = f"{subdir}/{library}-FINAL-available-resources.csv"
    miss_fh = f"{subdir}/{library}-FINAL-for-import-missing-resources.csv"
    del_fh = f"{subdir}/{library}-for-deletion-verification-required.csv"
    import_fh = f"{subdir}/{library}-for-import-verification-required.csv"

    url = os.environ["OVERDRIVE_URL"]

    logger.debug("Launching reconciliation process.")

    # prepare data from Sierra
    logger.debug("Parsing Sierra Export data.")
    prep_reserve_ids_in_sierra_export(library, sierra_export_fh)

    # retrieve data from Overdrive Digital Inventory API
    logger.debug(f"Retrieving data from Overdrive Digital Inventory API for {library}.")
    get_inventory(library)

    # read prepped Sierra export data and deduplicate reserve IDs
    logger.debug("Deduplicating Sierra export data on reserve ID.")
    df = pd.read_csv(
        f"{subdir}/{library}-sierra-prepped-reserve-ids.csv",
        names=["bib_no", "reserve_id"],
    )
    dedup_on_reserve_id(library, df, subdir)

    # use deduped sierra reserve ids for analysis
    logger.debug("Launching analysis.")
    sdf = pd.read_csv(
        f"{subdir}/{library}-unique-reserveid-sierra.csv",
        names=["bib_no", "reserve_id"],
    )
    sdf["reserve_id"] = sdf["reserve_id"].str.lower()
    edf = pd.read_csv(
        f"{subdir}/{library}-overdrive-api-reserve-ids.csv", names=["reserve_id"]
    )
    edf["reserve_id"] = edf["reserve_id"].str.lower()

    # create inner join representing available resources (ie. IDs present in both sets)
    logger.debug("Merging Sierra and Overdrive API sets.")
    adf = pd.merge(sdf, edf, on="reserve_id")
    adf["url"] = url + adf["reserve_id"].astype(str)

    adf.to_csv(
        avail_fh, index=False, header=False, columns=["bib_no", "reserve_id", "url"]
    )
    logger.info(
        f"Identified {adf.shape[0]} available resource(s). Report saved to: {avail_fh}"
    )

    # create full union of both sets
    logger.debug("Creating full union of both sets.")
    fdf = pd.merge(sdf, edf, on="reserve_id", how="outer", indicator=True)

    # find missing resources (ie. IDs only present in Overdrive export)
    logger.debug("Identifying reserve IDs missing from Sierra.")
    cdf = fdf[fdf["_merge"] == "right_only"].copy()
    cdf.to_csv(import_fh, index=False, header=False, columns=["reserve_id"])

    # verify that missing resources have active licenses
    mdf = verify_missing_resources(library=library, df=cdf)
    mdf["url"] = url + mdf["reserve_id"].astype(str)
    mdf.to_csv(miss_fh, index=False, header=False, columns=["reserve_id", "url"])
    logger.info(
        f"Identified {mdf.shape[0]} missing resource(s). Report saved to: {miss_fh}"
    )

    # find resources to be deleted (ie. IDs only present in Sierra export)
    logger.debug("Finding resources to be deleted from Sierra.")
    ddf = fdf[fdf["_merge"] == "left_only"].copy()
    ddf["url"] = url + ddf["reserve_id"].astype(str)
    ddf.to_csv(
        del_fh, index=False, header=False, columns=["bib_no", "reserve_id", "url"]
    )
    logger.info(
        f"Identified {ddf.shape[0]} resource(s) that can be deleted from Sierra. "
        f"Report saved to: {del_fh}"
    )

    logger.debug("Verifying records for deletion via web scraping OverDrive platform.")
    scrape(library, del_fh)

    logger.info("Reconciliation complete.")
