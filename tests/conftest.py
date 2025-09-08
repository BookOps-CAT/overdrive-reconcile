import datetime
import os

import pandas as pd
import pytest
from bookops_overdrive import OverdriveSession
from requests.exceptions import Timeout

from overdrive_reconcile import utils


@pytest.fixture(autouse=True)
def set_caplog_level(caplog):
    caplog.set_level("DEBUG")


@pytest.fixture
def test_main_dir(monkeypatch, tmp_path):
    main_dir = tmp_path / "LIB_CODE"

    def _patch(*args, **kwargs):
        return main_dir

    monkeypatch.setattr(utils, "dst_main_directory", _patch)
    return main_dir


@pytest.fixture
def test_csv(mocker):
    lines = [
        "b100000001,00000000-0000-0000-0000-000000000000,http://ebooks.nypl.org/ContentDetails.htm?ID=00000000-0000-0000-0000-000000000000",
        "b100000012,11111111-1111-1111-1111-111111111111,http://ebooks.nypl.org/ContentDetails.htm?ID=11111111-1111-1111-1111-111111111111",
    ]
    mock_file = mocker.mock_open(read_data="\n".join(lines))
    mocker.patch("overdrive_reconcile.webscraper.open", mock_file)


class MockHTTPResponse:
    def __init__(self, stub_json: dict, status_code: int = 200, url: str = ""):
        self.status_code = status_code
        self.stub_json = stub_json
        self.url = url

    @property
    def content(self):
        if "content" in self.stub_json:
            content = self.stub_json["content"]
        else:
            content = "".join([f'"{k}":"{v}"' for k, v in self.stub_json.items()])
        return bytes(content, encoding="utf-8")

    @property
    def ok(self):
        if self.status_code == 200:
            return True
        return False

    def json(self):
        return self.stub_json

    def raise_for_status(self):
        pass


@pytest.fixture
def mock_now(monkeypatch) -> None:
    class MockNow(datetime.datetime):
        @classmethod
        def now(cls, tzinfo=None) -> "MockNow":
            return cls(2025, 1, 1, 1, 0, 0, 0, tzinfo=None)

    monkeypatch.setattr(datetime, "datetime", MockNow)
    monkeypatch.setattr("overdrive_reconcile.utils.datetime", MockNow)


@pytest.fixture
def mock_expired_coll_token(monkeypatch, mock_creds) -> None:
    class MockNow(datetime.datetime):
        @classmethod
        def now(cls, tzinfo=None) -> "MockNow":
            return cls(2025, 6, 1, 1, 0, 0, 0, tzinfo=None)

    monkeypatch.setattr(
        "overdrive_reconcile.overdrive_session.datetime.datetime", MockNow
    )


@pytest.fixture
def mock_creds(mocker, mock_now):
    env_dict = {"USERPROFILE": "test"}
    creds = {
        "CLIENT_KEY": "NYPL",
        "CLIENT_SECRET": "foo",
        "COLL_TOKEN": "bar",
        "COLL_TOKEN_EXPIRATION": f"{(datetime.datetime.now() + datetime.timedelta(days=5)).strftime('%Y-%m-%d')}",
        "LIBRARY_ID": "1",
    }
    yaml_string = ""
    for k, v in creds.items():
        env_dict[f"NYPL_{k}"] = v
        yaml_string += f"{k}: '{v}'\n"
    m = mocker.mock_open(read_data=yaml_string)
    mocker.patch("overdrive_reconcile.overdrive_session.open", m)
    mocker.patch.dict(os.environ, env_dict)


@pytest.fixture
def mock_webscrape(monkeypatch, mock_now):
    content = (
        '<script>window.OverDrive.mediaItems = {"1":{"isAvailable":true,}};</script>'
    )

    def mock_html(*args, **kwargs):
        return MockHTTPResponse({"content": content}, url=args[0])

    monkeypatch.setattr("overdrive_reconcile.webscraper.requests.get", mock_html)


@pytest.fixture
def mock_webscrape_404(monkeypatch, mock_now):
    def mock_html(*args, **kwargs):
        return MockHTTPResponse({}, url=args[0], status_code=404)

    monkeypatch.setattr("overdrive_reconcile.webscraper.requests.get", mock_html)


@pytest.fixture
def mock_webscrape_timeout(monkeypatch, mock_now):
    def mock_timeout(*args, **kwargs):
        raise Timeout

    monkeypatch.setattr("overdrive_reconcile.webscraper.requests.get", mock_timeout)


@pytest.fixture
def mock_webscrape_false_positive(monkeypatch, mock_now):
    content = '<script></script><script>window.OverDrive.mediaItems = {"1":{"availabilityType":"always"}};</script>'

    def mock_html(*args, **kwargs):
        return MockHTTPResponse({"content": content}, url=args[0])

    monkeypatch.setattr("overdrive_reconcile.webscraper.requests.get", mock_html)


@pytest.fixture
def mock_webscrape_no_match(monkeypatch, mock_now):
    def mock_html(*args, **kwargs):
        return MockHTTPResponse({"content": "<script></script>"}, url=args[0])

    monkeypatch.setattr("overdrive_reconcile.webscraper.requests.get", mock_html)


@pytest.fixture
def mock_session_response(monkeypatch, mock_creds):
    reserve_ids = [
        "00000000-0000-0000-0000-000000000000",
        "11111111-1111-1111-1111-111111111111",
    ]

    def mock_access_token_response(*args, **kwargs):
        return MockHTTPResponse({"access_token": "foo", "expires_in": 100})

    def mock_account_info(*args, **kwargs):
        return MockHTTPResponse({"collectionToken": "foo"})

    def mock_bulk_metadata(*args, **kwargs):
        return MockHTTPResponse(
            {"metadata": [{"isOwnedByCollections": True, "id": reserve_ids[0]}]}
        )

    def mock_inventory(*args, **kwargs):
        return MockHTTPResponse({"files": [{"fileUrl": "foo.bar"}]})

    def mock_reserve_id_files(*args, **kwargs):
        return MockHTTPResponse({"reserveIds": reserve_ids})

    monkeypatch.setattr(OverdriveSession, "get_library_account_info", mock_account_info)
    monkeypatch.setattr(OverdriveSession, "get_bulk_metadata", mock_bulk_metadata)
    monkeypatch.setattr(OverdriveSession, "get_collection_inventory", mock_inventory)
    monkeypatch.setattr("requests.Session.get", mock_reserve_id_files)
    monkeypatch.setattr("requests.post", mock_access_token_response)


@pytest.fixture
def test_sierra_export(monkeypatch):
    def mock_read_csv(*args, **kwargs):
        df = pd.DataFrame(
            data={
                "bib_no": ["b170902584", "b202116244"],
                "reserve_id": [
                    "5E7A6766-4D4A-4564-86F2-481DE9473CD0",
                    '"B49B38E7-D896-46B7-B625-818538AA0892";"B8369000-10C2-4922-B59B-A0D440FD7033"',
                ],
            }
        )
        return df

    monkeypatch.setattr("overdrive_reconcile.prep.pd.read_csv", mock_read_csv)


@pytest.fixture
def test_sierra_export_no_overdrive_ids(monkeypatch):
    def mock_read_csv(*args, **kwargs):
        df = pd.DataFrame(data={"bib_no": ["b202231288"], "reserve_id": ["0012252617"]})
        return df

    monkeypatch.setattr(pd, "read_csv", mock_read_csv)
