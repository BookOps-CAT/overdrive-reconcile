from datetime import datetime

import pytest
from requests.exceptions import Timeout

from overdrive_reconcile.webscraper import EbookStatus, get_html, scrape, update_status


@pytest.mark.local
def test_scrape_local(test_csv, test_main_dir):
    scrape("BPL", "for-deletion-sample.csv", 2)

    today = datetime.now().date()
    with open(
        f"{test_main_dir}/{today}/BPL-FINAL-for-deletion-verified-resources.csv", "r"
    ) as f:
        assert len(f.read().strip()) > 0


@pytest.mark.parametrize(
    "metadata, attr, remove",
    [
        ('"isAvailable":true,"', "available", True),
        ('"availabilityType":"always"', "always_available", False),
        ('"isPreReleaseTitle":true,"', "prerelease", False),
        ('"isAvailable":true,"isPreReleaseTitle":false,"', "available", True),
    ],
)
def test_update_status(metadata, attr, remove):
    status = EbookStatus()
    updated = update_status(metadata=metadata, ebook_status=status)
    assert getattr(updated, attr) is True
    assert updated.for_removal == remove


@pytest.mark.parametrize(
    "metadata, copies, remove",
    [
        ('"ownedCopies":2,"', "2", False),
        ('"ownedCopies":0,"', "0", True),
        ('"ownedCopies":"foo","', "", True),
    ],
)
def test_update_status_owned_copies(metadata, copies, remove):
    status = EbookStatus()
    updated = update_status(metadata=metadata, ebook_status=status)
    assert updated.copies_owned == copies
    assert updated.for_removal == remove


def test_get_html(mock_webscrape, caplog):
    caplog.set_level("DEBUG")
    url = "http://ebooks.nypl.org/ContentDetails.htm?ID=1"
    data = get_html(url, 1, 2)
    assert (
        "(1 of 2) Requested page: http://ebooks.nypl.org/ContentDetails.htm?ID=1 == 200"
        in caplog.text
    )
    assert data == b'"isAvailable":false,'


def test_get_html_404(mock_webscrape_404, caplog):
    caplog.set_level("DEBUG")
    url = "http://ebooks.nypl.org/ContentDetails.htm?ID=1"
    data = get_html(url, 1, 2)
    assert (
        "(1 of 2) Requested page: http://ebooks.nypl.org/ContentDetails.htm?ID=1 == 404"
        in caplog.text
    )
    data is None


def test_get_html_timeout(mock_webscrape_timeout):
    url = "http://ebooks.nypl.org/ContentDetails.htm?ID=1"
    with pytest.raises(Timeout):
        get_html(url, 1, 2)


def test_scrape(test_csv, test_main_dir, mock_webscrape):
    scrape("NYPL", "for-deletion-sample.csv", 2)

    with open(
        f"{test_main_dir}/2025-01-01/NYPL-FINAL-for-deletion-verified-resources.csv",
        "r",
    ) as f:
        assert len(f.read().strip()) > 0


def test_scrape_404(test_csv, test_main_dir, mock_webscrape_404):
    scrape("NYPL", "for-deletion-sample.csv", 2)

    with open(
        f"{test_main_dir}/2025-01-01/NYPL-FINAL-for-deletion-verified-resources.csv",
        "r",
    ) as f:
        assert len(f.read().strip()) > 0
