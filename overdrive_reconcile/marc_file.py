from datetime import datetime

from pymarc import MARCReader


from .utils import save2csv


def create_dst_fh(library: str):
    """
    Creates csv file handle

    Args:
        library:                library code to prefix file handle
    """
    today = datetime.now().date()
    out = f"./overdrive_reconcile/files/{library}-reserve-ids-{today}.csv"
    return out


def extract_reserve_ids(library: str, marc_fh: str, out: str = None) -> None:
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
