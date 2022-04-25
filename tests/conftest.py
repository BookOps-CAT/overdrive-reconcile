from datetime import datetime
import os

import pytest
import yaml

from overdrive_reconcile import marc_file


@pytest.fixture
def test_dst(tmpdir):
    today = datetime.now().date()
    return tmpdir.join(f"TEST-reserve-ids-{today}.csv")


@pytest.fixture
def mock_dst_fh(monkeypatch, test_dst):
    def _patch(*args, **kwargs):
        return test_dst

    monkeypatch.setattr(marc_file, "create_dst_fh", _patch)


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
