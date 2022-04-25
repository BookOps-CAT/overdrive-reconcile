from datetime import datetime

import pytest

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
