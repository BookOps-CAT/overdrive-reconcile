"""
The main module that runs the reconciliation process.
"""
from datetime import datetime

from pandas import DataFrame

from .prep import prep_reserve_ids_in_sierra_export, date_subdirectory


def dedup_on_reserve_id(df: DataFrame, library: str, subdir: str):
    # deduplicate reserve ids just in case
    # the newest bibs remain
    df["dup"] = df.duplicated(subset=["reserve_id"], keep="last")
    ddf = df[df["dup"] == True]
    ddf.to_csv(
        f"{subdir}/{library}-FINAL-duplicate-reserveid-sierra.csv",
        index=False,
        header=None,
    )
    udf = df[df["dup"] == False]
    udf.to_csv(
        f"{subdir}/{library}-FINAL-unique-reserveid-sierra.csv",
        index=False,
    )


def reconcile(library: str, sierra_export_fh: str):
    """
    Launches recoinciliation process
    """

    # prepare data from Sierra
    prep_reserve_ids_in_sierra_export(sierra_export_fh, library)

    # prepare data from SimplyE
    simplye2csv(library)

    # reports directory
    subdir = date_subdirectory(library)

    # merge both datasets
    # retireve Sierra data
    today = datetime.now().date()
    df = pd.read_csv(
        f"{library}-sierra-prepped-reserve-ids.csv", names=["bib_no", "reserve_id"]
    )
    dedup_on_reserve_id(df, library, subdir)

    # use deduped sierra reserve ids for analysis
