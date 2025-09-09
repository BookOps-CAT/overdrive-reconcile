"""Functions that prepare Sierra export files for reconciliation."""

import logging
import os

import pandas as pd

from .utils import create_dst_csv_fh

logger = logging.getLogger(__name__)


def fresh_start(files: list[str]) -> None:
    """
    Cleans up any duplicate files in the 'files' directory resulting
    from pervious jobs

    Args:
        files:              list of file paths to be deleted
    """
    for file in files:
        if os.path.exists(file):
            os.remove(file)


def prep_reserve_ids_in_sierra_export(library: str, src_fh: str) -> None:
    """
    Validates OverDrive Reserve IDs exported from Sierra for further analysis.

    It's common to see print orders attached to e-resource bib records and these
    records must be filtered out in order to ensure they are not included in the
    reconciliation.

    See 'Step 2. Sierra list creation & export' in this package's README for the
    required format of the Sierra export file.

    The 'files/{library}/{date}' directory is cleaned up removing any existing files
    named '{library}-sierra-prepped-reserve-ids.csv' or
    '{library}-sierra-rejected-not-overdrive-ids.csv' resulting from previous jobs
    before outputing the validated and rejected reserve IDs to their respective files.

    Args:
        src_fh: file handle of Sierra .txt export
        library: 'NYPL' or 'BPL'

    Returns:
        None. Reserve IDs are written to csvs containing valid IDs (eg.
        'NYPL-sierra-prepped-reserve-ids.csv') and rejected IDs (eg.
        'NYPL-sierra-rejected-not-overdrive-ids.csv')
    """
    dst_validated_fh = create_dst_csv_fh(library, "sierra-prepped-reserve-ids")
    dst_rejected_fh = create_dst_csv_fh(library, "sierra-rejected-not-overdrive-ids")

    # cleanup any previous jobs
    fresh_start([dst_validated_fh, dst_rejected_fh])
    df = pd.read_csv(src_fh, dtype=str, names=["bib_id", "reserve_id"])

    df["reserve_id"] = df["reserve_id"].str.replace('"', "")
    df["reserve_id"] = df["reserve_id"].str.split(";")
    df = df.explode("reserve_id")

    valid_reserve_id = df["reserve_id"].str.fullmatch(r"^.{8}-.{4}-.{4}-.{4}-.{12}")

    df[valid_reserve_id].to_csv(dst_validated_fh, index=False, header=False)
    df[~valid_reserve_id].to_csv(dst_rejected_fh, index=False, header=False)
