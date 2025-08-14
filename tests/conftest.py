import pytest

from overdrive_reconcile import utils


class MockOSError:
    def __init__(self, *args, **kwargs):
        raise OSError


@pytest.fixture
def mock_os_error(monkeypatch):
    monkeypatch.setattr("os.remove", MockOSError)


@pytest.fixture
def test_main_dir(monkeypatch, tmpdir):
    main_dir = tmpdir.join("LIB_CODE")

    def _patch(*args, **kwargs):
        return main_dir

    monkeypatch.setattr(utils, "dst_main_directory", _patch)
    return main_dir
