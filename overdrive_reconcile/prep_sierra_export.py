"""
Finds in exported Sierra data multiple Reserve IDs in 037$a
The script splits them into separate rows, preserving their bib #
"""

import csv
import re

if __name__ == "__main__":
    from utils import save2csv
else:
    from .utils import save2csv


P = re.compile(r"^.{8}-.{4}-.{4}-.{4}-.{12}")


def is_reserve_id(i: str) -> bool:
    """
    Identifies if passed string is a reserve id or not
    """
    if re.match(P, i):
        return True
    else:
        return False


def prep(source: str, report: str) -> None:
    """
    Finds rows in csv file that include multiple Reserve IDs
    """
    with open(source, "r") as csvfile:
        reader = csv.reader(csvfile)
        reader.__next__()
        for row in reader:
            if len(row[1]) == 36:
                save2csv(report, row)
            else:
                ids = [i.replace('"', "") for i in row[1].split(";")]
                for i in ids:
                    if is_reserve_id(i):
                        save2csv(report, [row[0], i])
                    else:
                        save2csv("./files/rejected_non-overdrive-ids.cvs", [row[0], i])


if __name__ == "__main__":
    fh = "./files/nypl-20220321-all.txt"
    out = "./files/nypl-20220321-all-prepped.csv"

    prep(fh, out)
