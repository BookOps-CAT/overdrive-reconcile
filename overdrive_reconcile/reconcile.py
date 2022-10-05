"""
The main module that runs the reconciliation process.
"""
from datetime import datetime

import pandas as pd

from .prep import prep_reserve_ids_in_sierra_export, simplye2csv
from .utils import URL_NYPL, URL_BPL, date_subdirectory
from .webscraper import scrape


def dedup_on_reserve_id(library: str, df: pd.DataFrame, subdir: str):
    """
    Deduplicates given dataframe on reserve ID leaving the latest record.
    Does not consiter situation where duplicate reserve ID is present on the
    same record.

    Args:
        library:                    'NYPL' or 'BPL' library  code
        df:                         pandas.DataFrame instance
        subdir:                     directory to output reports
    """
    print("Deduplication of Sierra dataset on Reserve ID...")
    dups_fh = f"{subdir}/{library}-FINAL-duplicate-reserveid-sierra.csv"
    unique_fh = f"{subdir}/{library}-unique-reserveid-sierra.csv"

    df["dup"] = df.duplicated(subset=["reserve_id"], keep="last")
    ddf = df[df["dup"] == True]
    ddf.to_csv(
        dups_fh,
        index=False,
        header=None,
        columns=["bib_no", "reserve_id"],
    )
    print(
        f"Identified {ddf.shape[0]} duplicate records in Sierra export. Report saved to: {dups_fh}"
    )

    udf = df[df["dup"] == False]
    udf.to_csv(
        unique_fh,
        index=False,
        columns=["bib_no", "reserve_id"],
    )
    print(
        f"Identified {udf.shape[0]} unique Reserve IDs in Sierra export. Report saved to: {unique_fh}"
    )


def reconcile(library: str, sierra_export_fh: str):
    """
    Launches recoinciliation process
    """

    # reports directory
    subdir = date_subdirectory(library)
    print(f"All output reports will be saved to {subdir}.")

    avail_fh = f"{subdir}/{library}-FINAL-available-resources.csv"
    miss_fh = f"{subdir}/{library}-FINAL-for-import-missing-resources.csv"
    del_fh = f"{subdir}/{library}-for-deletion-verification-required.csv"

    if library == "NYPL":
        url = URL_NYPL
    elif library == "BPL":
        url = URL_BPL
    else:
        ValueError("Invalid library code provided.")

    print("Launching reconciliation process...")

    # prepare data from Sierra
    print("Parsing Sierra Export data...")
    prep_reserve_ids_in_sierra_export(library, sierra_export_fh)

    # prepare data from SimplyE
    print(f"Retrieving data from {library} SimplyE DB...")
    simplye2csv(library)

    # merge both datasets
    # retireve Sierra data
    print("Merging Sierra and SimplyE sets...")
    today = datetime.now().date()
    df = pd.read_csv(
        f"{subdir}/{library}-sierra-prepped-reserve-ids.csv",
        names=["bib_no", "reserve_id"],
    )
    dedup_on_reserve_id(library, df, subdir)

    # use deduped sierra reserve ids for analysis
    print("Normalizing Sierra and SimplyE Reserve IDs...")
    sdf = pd.read_csv(
        f"{subdir}/{library}-unique-reserveid-sierra.csv",
        names=["bib_no", "reserve_id"],
    )
    sdf["reserve_id"] = sdf["reserve_id"].str.lower()
    edf = pd.read_csv(
        f"{subdir}/{library}-simplye-reserve-ids.csv", names=["reserve_id"]
    )
    edf["reserve_id"] = edf["reserve_id"].str.lower()

    print("Launching analysis...")
    # find inner joint (available - present in both sets)
    adf = pd.merge(sdf, edf, on="reserve_id")
    adf["url"] = url + adf["reserve_id"].astype(str)

    adf.to_csv(avail_fh, index=False, columns=["bib_no", "reserve_id", "url"])
    print(f"Identified {df.shape[0]} resources available. Report saved to: {avail_fh}")

    # create full union of both sets
    print("Creating full union of both sets...")
    fdf = pd.merge(sdf, edf, on="reserve_id", how="outer", indicator=True)

    # find missing resources
    print("Identifying missing in Sierra Reserve IDs...")
    mdf = fdf[fdf["_merge"] == "right_only"]
    mdf["url"] = url + mdf["reserve_id"].astype(str)
    mdf.to_csv(miss_fh, index=False, header=False, columns=["reserve_id", "url"])
    print(f"Identified {mdf.shape[0]} missing resources. Report saved to: {miss_fh}")

    # find resources for deletion
    print("Finding resources to be deleted in Sierra...")
    ddf = fdf[fdf["_merge"] == "left_only"]
    ddf["url"] = url + ddf["reserve_id"].astype(str)
    ddf.to_csv(
        del_fh, index=False, header=False, columns=["bib_no", "reserve_id", "url"]
    )
    print(
        f"Identified {ddf.shape[0]} resources that can be deleted from Sierra. Report saved to: {del_fh}"
    )

    print("Veryfying records for deletion via web scraping OverDrive platform...")
    print("<go get your coffee - this may take a while>")
    total = ddf.shape[0] - 1
    scrape(library, del_fh, total)

    print("RECONCILIATION COMPLETE...")
