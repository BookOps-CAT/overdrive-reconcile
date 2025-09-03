import logging
import os

import pandas as pd

from . import overdrive_session
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
    Filters and prepares OverDrive Reserve IDs exported to text file
    from Sierra for further analysis.
    It's common to see print orders attached to e-resource bib. It is important
    to make sure the list from Sierra does not include any mistakenly included
    records!

    Sierra export configuration:
        fields: "RECORD #(BIBLIO)","037|a"
        field delimiter: ,
        repeated field delimiter: ;
        text qualifier: "
        maximum field lenght: <none>

    Args:
        src_fh:                 file handle of Sierra text export
        library:                library code: 'NYPL' or 'BPL'
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


def overdrive2csv(library: str) -> None:
    """
    Retrieves OverDrive Reserve IDs from Overdrive Discovery APIs
    and saves the results to a csv file.

    Args:
        library: library system 'NYPL' or 'BPL'
    """
    out = create_dst_csv_fh(library, "overdrive-api-reserve-ids")
    inventory = overdrive_session.get_inventory(library=library)
    df = pd.DataFrame(inventory)
    df.to_csv(out, index=False, header=False)
