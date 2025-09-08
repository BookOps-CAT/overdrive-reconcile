import os

import pytest

from overdrive_reconcile.overdrive_session import (
    get_overdrive_api_creds,
)


def test_get_overdrive_api_creds_nypl(mock_creds):
    get_overdrive_api_creds("nypl")

    assert "NYPL_CLIENT_KEY" in os.environ.keys()
    assert "NYPL_CLIENT_SECRET" in os.environ.keys()
    assert "NYPL_LIBRARY_ID" in os.environ.keys()
    assert "NYPL_COLL_TOKEN" in os.environ.keys()
    assert "NYPL_COLL_TOKEN_EXPIRATION" in os.environ.keys()


def test_get_overdrive_api_creds_bpl():
    result = get_overdrive_api_creds("bpl")
    assert result == NotImplemented


def test_get_overdrive_api_creds_other():
    with pytest.raises(ValueError) as exc:
        get_overdrive_api_creds("foo")
    assert str(exc.value) == "Invalid library code passed"
