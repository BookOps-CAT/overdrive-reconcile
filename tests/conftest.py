import pytest
from requests.exceptions import Timeout

from overdrive_reconcile import utils


@pytest.fixture
def test_main_dir(monkeypatch, tmpdir):
    main_dir = tmpdir.join("LIB_CODE")

    def _patch(*args, **kwargs):
        return main_dir

    monkeypatch.setattr(utils, "dst_main_directory", _patch)
    return main_dir


@pytest.fixture
def test_for_deletion_csv(mocker):
    lines = [
        "b112411101,9cbb451f-2d23-478a-96d0-3b0c7ae3a588,http://digitalbooks.brooklynpubliclibrary.org/ContentDetails.htm?ID=9cbb451f-2d23-478a-96d0-3b0c7ae3a588",
        "b112467027,8543242e-b134-4024-8229-f969b0072901,http://digitalbooks.brooklynpubliclibrary.org/ContentDetails.htm?ID=8543242e-b134-4024-8229-f969b0072901",
    ]
    mock_file = mocker.mock_open(read_data="\n".join(lines))
    mocker.patch("builtins.open", mock_file)


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
