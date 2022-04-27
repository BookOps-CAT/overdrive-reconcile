from datetime import datetime
import os

import pytest

from overdrive_reconcile.prep import (
    create_dst_fh,
    date_subdirectory,
    dst_main_directory,
    extract_reserve_ids_from_backdated_file,
    fresh_start,
    prep_reserve_ids_in_sierra_export,
    simplye2csv,
)


@pytest.mark.parametrize("arg", ["BPL", "NYPL"])
def test_dst_main_directory(arg):
    assert dst_main_directory(arg) == f"./files/{arg}"


@pytest.mark.parametrize("arg", ["BPL", "NYPL"])
def test_date_subdirectory(test_main_dir, mock_main_dir, arg):
    today = datetime.now().date()
    assert date_subdirectory(arg) == f"{test_main_dir}/{today}"
    assert os.path.exists(f"{test_main_dir}/{today}")


def test_extract_reserve_ids_from_backdated_file(test_main_dir, mock_main_dir):
    today = datetime.now().date()
    out = f"{test_main_dir}/{today}/BPL-backdated-reserve-ids.csv"
    extract_reserve_ids_from_backdated_file("BPL", "./tests/sample.mrc")

    with open(out, "r") as f:
        assert f.read().strip() == "0e90d7a5-30b8-4d07-9d13-df0e02ea631e"


def test_extract_reserve_ids_from_backdated_file_invalid_library():
    with pytest.raises(ValueError):
        extract_reserve_ids_from_backdated_file("FOO", "foo.mrc")


@pytest.mark.parametrize("arg", [1, None, ""])
def test_extract_reserve_ids_from_backdated_file_invalid_marc_fh(arg):
    with pytest.raises(ValueError):
        extract_reserve_ids_from_backdated_file("BPL", arg)


def test_fresh_start(tmpdir):
    f1 = tmpdir.join("foo.csv")
    f1.write("spam")
    f2 = tmpdir.join("bar.csv")
    f2.write("spam")

    # make sure files are created
    assert os.path.exists(f1)
    assert os.path.exists(f2)

    fresh_start([f1, f2])

    assert os.path.exists(f1) is False
    assert os.path.exists(f2) is False


def test_fresh_start_exception(tmpdir, mock_os_error):
    f = tmpdir.join("foo.csv")
    f.write("spam")
    assert os.path.exists(f)

    with pytest.raises(OSError):
        fresh_start([f])


def test_prep_reserve_ids_in_sierra_export(test_main_dir, mock_main_dir):
    today = datetime.now().date()
    prep_reserve_ids_in_sierra_export("NYPL", "tests/sierra-export-sample.txt")
    with open(f"{test_main_dir}/{today}/NYPL-sierra-prepped-reserve-ids.csv", "r") as f:
        assert (
            f.read()
            == "b170902584,5E7A6766-4D4A-4564-86F2-481DE9473CD0\nb202116244,B49B38E7-D896-46B7-B625-818538AA0892\nb202116244,B8369000-10C2-4922-B59B-A0D440FD7033\n"
        )


def test_prep_reserve_ids_in_sierra_export_no_overdrive_ids(
    test_main_dir, mock_main_dir
):
    today = datetime.now().date()
    prep_reserve_ids_in_sierra_export(
        "NYPL", "tests/sierra-export-sample-no-overdrive-id.txt"
    )
    with open(
        f"{test_main_dir}/{today}/NYPL-sierra-rejected-not-overdrive-ids.csv", "r"
    ) as f:
        assert f.read() == "b202231288,0012252617\n"


@pytest.mark.local
def test_simplye2csv(test_main_dir, mock_main_dir):
    today = datetime.now().date()
    simplye2csv("BPL")
    with open(f"{test_main_dir}/{today}/BPL-simplye-reserve-ids.csv", "r") as f:
        assert len(f.read().strip()) > 0
