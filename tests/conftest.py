import pytest

from overdrive_reconcile import utils


class MockOSError:
    def __init__(self, *args, **kwargs):
        raise OSError


@pytest.fixture
def mock_os_error(monkeypatch):
    monkeypatch.setattr("os.remove", MockOSError)


@pytest.fixture
def test_main_dir(tmpdir):
    return tmpdir.join("LIB_CODE")


@pytest.fixture
def mock_main_dir(monkeypatch, test_main_dir):
    def _patch(*args, **kwargs):
        return test_main_dir

    monkeypatch.setattr(utils, "dst_main_directory", _patch)
