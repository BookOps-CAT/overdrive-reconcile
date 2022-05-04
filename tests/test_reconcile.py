from datetime import datetime

import pandas as pd
import pytest

from overdrive_reconcile.utils import date_subdirectory
from overdrive_reconcile.reconcile import dedup_on_reserve_id


def test_dedup_on_reserve_id(mock_main_dir):
    today = datetime.now().date()
    subdir = date_subdirectory("BPL")
    d = {"bib_no": ["b1", "b2", "b2", "b3"], "reserve_id": [1, 2, 2, 1]}
    df = pd.DataFrame(data=d)
    dedup_on_reserve_id("BPL", df, subdir)
