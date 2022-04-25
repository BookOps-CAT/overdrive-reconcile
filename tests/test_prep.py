from datetime import datetime
import os

import pytest

from overdrive_reconcile.prep import create_dst_fh, extract_reserve_ids_from_marc


def test_create_dst_fh():
    today = datetime.now().date()
    assert (
        create_dst_fh("NYPL")
        == f"./overdrive_reconcile/files/NYPL-reserve-ids-{today}.csv"
    )


def test_extract_reserve_ids(test_dst, mock_dst_fh):
    out = test_dst
    extract_reserve_ids("BPL", "./tests/sample.mrc")

    with open(out, "r") as f:
        assert f.read().strip() == "0e90d7a5-30b8-4d07-9d13-df0e02ea631e"


def test_extract_reserve_ids_invalid_library():
    with pytest.raises(ValueError):
        extract_reserve_ids("FOO", "foo.mrc")


@pytest.mark.parametrize("arg", [1, None, ""])
def test_extract_reserve_ids_invalid_marc_fh(arg):
    with pytest.raises(ValueError):
        extract_reserve_ids("BPL", arg)
