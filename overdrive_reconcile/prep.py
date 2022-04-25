from datetime import datetime
import csv
import os

from pymarc import MARCReader


from .utils import save2csv, is_reserve_id


def create_dst_fh(library: str):
    """
    Creates csv file handle

    Args:
        library:                library code to prefix file handle
    """
    today = datetime.now().date()
    out = f"./overdrive_reconcile/files/{library}-reserve-ids-{today}.csv"
    return out


def extract_reserve_ids_from_marc(library: str, marc_fh: str, out: str = None) -> None:
    """
    Parses OverDrive backdated MarcExpress records and outputs
    found Reserve IDs to a file.
    May produce invalid results if used for MARC records exported from
    Sierra (multiple 037s, etc.)

    Args:
        library:                'BPL' or 'NYPL'
        marc_fh:                file handle of MARC21 file to be processed
        out:                    file handle of the destination csv file

    """
    if library.upper() not in ("BPL", "NYPL"):
        raise ValueError("Invalid library argument passed. Must be 'BPL' or 'NYPL'")

    if not isinstance(marc_fh, str) or not marc_fh:
        raise ValueError("Invalid or missing source MARC file passed.")

    if not isinstance(out, str):
        out = create_dst_fh(library)

    with open(marc_fh, "rb") as marcfile:
        reader = MARCReader(marcfile)
        for bib in reader:
            reserve_id = bib["037"]["a"].lower()
            save2csv(out, [reserve_id])


def prep_reserve_ids_in_sierra_txt(src_fh: str) -> None:
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
    """
    today = datetime.now().date()
    dst_validated_fh = f"./overdrive_reconcile/files/{today}-prepped-reserve-ids.csv"
    dst_rejected_fh = f"./overdrvive_reconcile/files/{today}-rejected-ids.csv"

    # cleanup any previous jobs
    if os.path.exists(dst_validated_fh):
        os.remove(dst_validated_fh)
    if os.path.exists(dst_rejected_fh):
        os.remove(dst_rejected_fh)

    with open(src, "r") as csvfile:
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
