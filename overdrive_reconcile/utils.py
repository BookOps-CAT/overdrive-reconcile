import csv
import re


P = re.compile(r"^.{8}-.{4}-.{4}-.{4}-.{12}")


def is_reserve_id(i: str) -> bool:
    """
    Identifies if passed string is a OverDrive Reserve ID or not

    Args:
        i:                  id string to be evaluated

    Returns:
        bool
    """
    if re.match(P, i):
        return True
    else:
        return False


def save2csv(dst_fh, row):
    """
    Appends a list with data to a dst_fh csv
    args:
        dst_fh: str, output file
        row: list, list of values to write in a row
    """

    with open(dst_fh, "a", encoding="utf-8") as csvfile:
        out = csv.writer(
            csvfile,
            delimiter=",",
            lineterminator="\n",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        out.writerow(row)
