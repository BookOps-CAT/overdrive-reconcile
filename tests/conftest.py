import pytest

from overdrive_reconcile import utils


@pytest.fixture
def test_main_dir(monkeypatch, tmpdir):
    main_dir = tmpdir.join("LIB_CODE")

    def _patch(*args, **kwargs):
        return main_dir

    monkeypatch.setattr(utils, "dst_main_directory", _patch)
    return main_dir


@pytest.fixture
def test_for_deletion_csv(mocker):
    lines = [
        "b112411101,9cbb451f-2d23-478a-96d0-3b0c7ae3a588,http://digitalbooks.brooklynpubliclibrary.org/ContentDetails.htm?ID=9cbb451f-2d23-478a-96d0-3b0c7ae3a588",
        "b112467027,8543242e-b134-4024-8229-f969b0072901,http://digitalbooks.brooklynpubliclibrary.org/ContentDetails.htm?ID=8543242e-b134-4024-8229-f969b0072901",
    ]
    mock_file = mocker.mock_open(read_data="\n".join(lines))
    mocker.patch("builtins.open", mock_file)
