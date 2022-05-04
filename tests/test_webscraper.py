import pytest

from overdrive_reconcile.webscraper import scrape


def test_scrape(mock_main_dir, test_main_dir):
    src = "tests/for-deletion-sample.csv"
    scrape("BPL", src)
