import csv
from datetime import datetime
import os

import pytest

from overdrive_reconcile.utils import (
    is_reserve_id,
    counted,
    count_rows,
    save2csv,
    create_dst_csv_fh,
    date_subdirectory,
    dst_main_directory,
)


def test_counted():
    @counted
    def some_func():
        return None

    some_func()
    some_func()
    assert some_func.calls == 2


def test_count_rows():
    assert count_rows("tests/for-deletion-sample.csv") == 3


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("0e90d7a5-30b8-4d07-9d13-df0e02ea631e", True),
        ("92080423-8690-4580-A5AE-BCFCD3191CFB", True),
        ("14319803-7346-4454-934b-790eb8b24e23", True),
        ("EBL120658", False),
        ("Unowned Dawsonera PDA title", False),
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


@pytest.mark.parametrize("arg", ["BPL", "NYPL"])
def test_dst_main_directory(arg):
    assert dst_main_directory(arg) == f"./files/{arg}"


@pytest.mark.parametrize("arg", ["BPL", "NYPL"])
def test_date_subdirectory(test_main_dir, mock_main_dir, arg):
    today = datetime.now().date()
    assert date_subdirectory(arg) == f"{test_main_dir}/{today}"
    assert os.path.exists(f"{test_main_dir}/{today}")


def test_create_dst_csv_fh(test_main_dir, mock_main_dir):
    today = datetime.now().date()
    subdir = f"{test_main_dir}/{today}"
    assert create_dst_csv_fh("BPL", "foo") == f"{subdir}/BPL-foo.csv"
