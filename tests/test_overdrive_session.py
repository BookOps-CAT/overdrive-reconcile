import pytest

from overdrive_reconcile.overdrive_session import (
    get_inventory,
    get_metadata,
    get_overdrive_api_creds,
)


@pytest.mark.local
def test_get_overdrive_api_creds_nypl():
    result = get_overdrive_api_creds("nypl")
    assert sorted(result.keys()) == [
        "CLIENT_KEY",
        "CLIENT_SECRET",
        "ILS_NAME",
        "LIBRARY_ID",
        "WEBSITE_ID",
    ]


@pytest.mark.local
def test_get_overdrive_api_creds_bpl():
    result = get_overdrive_api_creds("bpl")
    assert result == NotImplemented


@pytest.mark.local
def test_get_overdrive_api_creds_other():
    with pytest.raises(ValueError) as exc:
        get_overdrive_api_creds("foo")
    assert str(exc.value) == "Invalid library code passed"


@pytest.mark.local
def test_get_inventory():
    result = get_inventory("NYPL")
    assert isinstance(result, list)
    assert len(result) >= 100000


@pytest.mark.local
def test_get_title_metadata():
    result = get_metadata("NYPL", "0001123d-0bd2-4021-935f-ba6dc94ae052")
    assert result == {}
