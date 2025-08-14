import os

import pytest
import yaml

from overdrive_reconcile import simplye, utils


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


def get_creds(library: str):
    fh = f".cred/.simplyE/{library.lower()}_simply_e.yaml"

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


@pytest.fixture
def mock_simplye_sql(monkeypatch):
    def _patch(*args, **kwargs):
        return """
            SELECT i.identifier FROM identifiers i 
                JOIN licensepools lp ON i.id=lp.identifier_id
                JOIN editions e ON lp.presentation_edition_id = e.id
            WHERE lp.licenses_owned > 0 AND i.type = 'Overdrive ID' AND e.medium != 'Video' LIMIT 5;
        """

    monkeypatch.setattr(simplye, "get_reserve_id_query", _patch)
