from datetime import datetime
import csv
import os

import pandas as pd
from pymarc import MARCReader


from .utils import save2csv, is_reserve_id
from .simplye import RESERVE_ID_QUERY, get_simplye_creds, simplye_connection


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


def create_dst_fh(library: str, name: str):
    """
    Creates csv file handle

    Args:
        library:                library code to prefix file handle
        name:                   file name
    """

    dst_dir = date_subdirectory(library)
    out = f"{dst_dir}/{library}-{name}.csv"
    return out


def extract_reserve_ids_from_backdated_file(library: str, marc_fh: str) -> None:
    """
    Parses OverDrive backdated MarcExpress records and outputs
    found Reserve IDs to a file.
    May produce invalid results if used for MARC records exported from
    Sierra (multiple 037s, etc.)

    Args:
        library:                'BPL' or 'NYPL'
        marc_fh:                file handle of MARC21 file to be processed

    """
    if library.upper() not in ("BPL", "NYPL"):
        raise ValueError("Invalid library argument passed. Must be 'BPL' or 'NYPL'")

    if not isinstance(marc_fh, str) or not marc_fh:
        raise ValueError("Invalid or missing source MARC file passed.")

    out = create_dst_fh(library, "backdated-reserve-ids")
    fresh_start([out])

    with open(marc_fh, "rb") as marcfile:
        reader = MARCReader(marcfile)
        for bib in reader:
            reserve_id = bib["037"]["a"].lower()
            save2csv(out, [reserve_id])


def fresh_start(files: list[str]) -> None:
    """
    Cleans up any duplicate files in the 'files' directory resulting
    from pervious jobs

    Args:
        files:              list of file paths to be deleted
    """
    for file in files:
        if os.path.exists(file):
            try:
                os.remove(file)
            except OSError:
                print(f"Unable to remove {file}")
                raise


def prep_reserve_ids_in_sierra_export(library: str, src_fh: str) -> None:
    """
    Filters and prepares OverDrive Reserve IDs exported to text file
    from Sierra for further analyis

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
    dst_validated_fh = create_dst_fh(library, "sierra-prepped-reserve-ids")
    dst_rejected_fh = create_dst_fh(library, "sierra-rejected-not-overdrive-ids")

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


def simplye2csv(library: str):
    """
    Retrieves OverDrive Reserve IDs from given SimplyE database
    and saves the results to a csv file.

    Args:
        library:                SimplyE library database code: 'NYPL' or 'BPL'
    """
    out = create_dst_fh(library, "simplye-reserve-ids")
    engine = simplye_connection(library)
    df = pd.read_sql_query(RESERVE_ID_QUERY, con=engine)
    df.to_csv(out, index=False, header=None)
