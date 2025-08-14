import pandas as pd

from overdrive_reconcile.reconcile import dedup_on_reserve_id
from overdrive_reconcile.utils import date_subdirectory


def test_dedup_on_reserve_id():
    subdir = date_subdirectory("BPL")
    d = {"bib_no": ["b1", "b2", "b2", "b3"], "reserve_id": [1, 2, 2, 1]}
    df = pd.DataFrame(data=d)
    dedup_on_reserve_id("BPL", df, subdir)
