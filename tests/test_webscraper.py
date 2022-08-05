from datetime import datetime

import pytest

from overdrive_reconcile.webscraper import scrape


@pytest.mark.local
def test_scrape(mock_main_dir, test_main_dir):
    src = "tests/for-deletion-sample.csv"
    scrape("BPL", src, 2)

    today = datetime.now().date()
    with open(
        f"{test_main_dir}/{today}/BPL-FINAL-for-deletion-verified-resources.csv", "r"
    ) as f:
        assert len(f.read().strip()) > 0
