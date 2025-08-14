import csv
import os

import pandas as pd

from . import overdrive_session
from .utils import create_dst_csv_fh, is_reserve_id, save2csv


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

    with open(src_fh, "r") as csvfile:
        reader = csv.reader(csvfile)
        reader.__next__()
        for row in reader:
            if len(row[1]) == 36:
                save2csv(dst_validated_fh, row)
            else:
                ids = [i.replace('"', "") for i in row[1].split(";")]
                for i in ids:
                    if is_reserve_id(i):
                        save2csv(dst_validated_fh, [row[0], i])
                    else:
                        save2csv(dst_rejected_fh, [row[0], i])


def overdrive2csv(library: str) -> None:
    """
    Retrieves OverDrive Reserve IDs from Overdrive Discovery APIs
    and saves the results to a csv file.

    Args:
        library: library system 'NYPL' or 'BPL'
    """
    out = create_dst_csv_fh(library, "api-reserve-ids")
    inventory = overdrive_session.get_inventory(library=library)
    df = pd.DataFrame(inventory)
    df.to_csv(out, index=False, header=False)
