import csv

import pytest


from overdrive_reconcile.utils import is_reserve_id, save2csv


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("0e90d7a5-30b8-4d07-9d13-df0e02ea631e", True),
        ("12345", False),
        ("12345678-1234", False),
    ],
)
def test_is_reserve_id(arg, expectation):
    assert is_reserve_id(arg) == expectation


def test_save2csv(tmpdir):
    # check if rows appended and if proper quoting is used
    out = tmpdir.join("test_csv.csv")
    row = ["foo", "bar", "spam,baz"]
    save2csv(out, row)
    row = ["foo2", "bar2", "spam2,baz2"]
    save2csv(out, row)

    with open(out, "r") as f:
        assert f.read().strip() == 'foo,bar,"spam,baz"\nfoo2,bar2,"spam2,baz2"'
