import os

import pandas as pd
import pytest

from overdrive_reconcile.overdrive_session import (
    get_batches,
    get_inventory,
    get_overdrive_api_creds,
    verify_missing_resources,
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


def test_get_overdrive_api_creds_expired_coll_token(
    mock_expired_coll_token, mock_session_response
):
    get_overdrive_api_creds("nypl")
    assert os.environ["NYPL_COLL_TOKEN_EXPIRATION"] == "2025-07-01"


def test_get_inventory(mock_session_response, test_main_dir):
    get_inventory("NYPL")
    with open(
        f"{test_main_dir}/2025-01-01/NYPL-overdrive-api-reserve-ids.csv", "r"
    ) as f:
        assert (
            f.read()
            == "00000000-0000-0000-0000-000000000000\n11111111-1111-1111-1111-111111111111\n"
        )


def test_verify_missing_resources(mock_session_response, test_main_dir, caplog):
    df = pd.DataFrame(
        data={
            "reserve_id": [
                "00000000-0000-0000-0000-000000000000" for i in range(0, 1111)
            ]
        }
    )
    mdf = verify_missing_resources("NYPL", df)
    assert "Checking ids 1-50 of 1111." in caplog.text
    assert mdf.columns == ["reserve_id"]
    assert mdf["reserve_id"].iloc[0] == "00000000-0000-0000-0000-000000000000"


def test_get_batches():
    full_list = list(range(1, 201))
    batches = get_batches(full_list, 20)
    assert len([i for i in batches]) == 10
