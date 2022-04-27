from datetime import datetime
import os

import pytest
import yaml

from overdrive_reconcile import prep


class MockOSError:
    def __init__(self, *args, **kwargs):
        raise OSError


@pytest.fixture
def mock_os_error(monkeypatch):
    monkeypatch.setattr("os.remove", MockOSError)


@pytest.fixture
def test_main_dir(tmpdir):
    today = datetime.now().date()
    return tmpdir.join(f"LIB_CODE")


@pytest.fixture
def mock_main_dir(monkeypatch, test_main_dir):
    def _patch(*args, **kwargs):
        return test_main_dir

    monkeypatch.setattr(prep, "dst_main_directory", _patch)


def get_creds(library: str):
    fh = None
    if library == "BPL":
        fh = ".simplyE/bpl_simply_e.yaml"
    elif library == "NYPL":
        fh = ".simplyE/nyp_simply_e.yaml"

    with open(os.path.join(os.environ["USERPROFILE"], fh), "r") as f:
        data = yaml.safe_load(f)
        return data


@pytest.fixture
def local_bpl_connection():
    creds = get_creds("BPL")
    conn = f"postgresql://{creds.get('USER')}:{creds.get('PASSWORD')}@{creds.get('HOST')}/{creds.get('DATABASE')}"
    return conn


@pytest.fixture
def local_nypl_connection():
    creds = get_creds("NYPL")
    conn = f"postgresql://{creds.get('USER')}:{creds.get('PASSWORD')}@{creds.get('HOST')}/{creds.get('DATABASE')}"
    return conn
