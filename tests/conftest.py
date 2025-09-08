import pandas as pd
import pytest
from requests.exceptions import Timeout

from overdrive_reconcile import utils


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
        content = ""
        for k, v in self.stub_json.items():
            if isinstance(v, bool):
                v = str(v).lower()
            content += f'"{k}":{v},'
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
def mock_webscrape(monkeypatch):
    def mock_html(*args, **kwargs):
        return MockHTTPResponse({"isAvailable": False}, url=args[0])

    monkeypatch.setattr("overdrive_reconcile.webscraper.requests.get", mock_html)


@pytest.fixture
def mock_webscrape_404(monkeypatch):
    def mock_html(*args, **kwargs):
        return MockHTTPResponse({}, url=args[0], status_code=404)

    monkeypatch.setattr("overdrive_reconcile.webscraper.requests.get", mock_html)


@pytest.fixture
def mock_webscrape_timeout(monkeypatch):
    def mock_timeout(*args, **kwargs):
        raise Timeout

    monkeypatch.setattr("overdrive_reconcile.webscraper.requests.get", mock_timeout)


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
