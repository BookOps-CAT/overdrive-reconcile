import os

import pandas as pd

from overdrive_reconcile.reconcile import dedup_on_reserve_id, reconcile
from overdrive_reconcile.utils import date_subdirectory


def test_dedup_on_reserve_id():
    subdir = date_subdirectory("BPL")
    d = {"bib_no": ["b1", "b2", "b2", "b3"], "reserve_id": [1, 2, 2, 1]}
    df = pd.DataFrame(data=d)
    dedup_on_reserve_id("BPL", df, subdir)


def test_reconcile(
    mock_session_response, test_main_dir, caplog, mock_webscrape, tmp_path
):
    sierra_dir = tmp_path / "SIERRA_IN"
    sierra_dir.mkdir()
    sierra_in = sierra_dir / "sierra-export.txt"
    sierra_in.write_text(
        '"RECORD #(BIBLIO)","037|a"\n"b100000001","00000000-0000-0000-0000-000000000000"\n"b100000023","22222222-2222-2222-2222-222222222222"\n"b100000023","33333333-3333-3333-3333-333333333333"',
        encoding="utf-8",
    )
    reconcile("NYPL", sierra_in)
    file_list = os.listdir(f"{test_main_dir}/2025-01-01/")
    log_msgs = [i.msg for i in caplog.records]
    assert log_msgs[0].startswith("All output reports will be saved to ")
    assert log_msgs[1] == "Launching reconciliation process."
    assert log_msgs[2] == "Parsing Sierra Export data."
    assert (
        log_msgs[3] == "Retrieving data from Overdrive Digital Inventory API for NYPL."
    )
    assert log_msgs[4] == "Deduplicating Sierra export data on reserve ID."
    assert log_msgs[5].startswith("Identified 0 duplicate record(s) in Sierra export.")
    assert log_msgs[6].startswith("Identified 3 unique reserve ID(s) in Sierra export.")
    assert log_msgs[7] == "Launching analysis."
    assert log_msgs[8] == "Merging Sierra and Overdrive API sets."
    assert log_msgs[9].startswith("Identified 1 available resource(s).")
    assert log_msgs[10] == "Creating full union of both sets."
    assert log_msgs[11] == "Identifying reserve IDs missing from Sierra."
    assert log_msgs[12] == "Checking ids 1-1 of 1."
    assert log_msgs[13].startswith("Identified 1 missing resource(s)")
    assert log_msgs[14] == "Finding resources to be deleted from Sierra."
    assert log_msgs[15].startswith("Identified 2 resource(s) that can be deleted")
    assert log_msgs[16].startswith("Verifying records for deletion via web scraping")
    assert log_msgs[17].startswith("(1 of 2) Requested page: http://ebooks.nypl.org/")
    assert log_msgs[18].startswith("(2 of 2) Requested page: http://ebooks.nypl.org/")
    assert log_msgs[19] == "Reconciliation complete."
    assert sorted(file_list) == [
        "NYPL-FINAL-available-resources.csv",
        "NYPL-FINAL-duplicate-reserveid-sierra.csv",
        "NYPL-FINAL-for-deletion-verified-resources.csv",
        "NYPL-FINAL-for-import-missing-resources.csv",
        "NYPL-for-deletion-verification-required.csv",
        "NYPL-for-import-verification-required.csv",
        "NYPL-overdrive-api-reserve-ids.csv",
        "NYPL-sierra-prepped-reserve-ids.csv",
        "NYPL-sierra-rejected-not-overdrive-ids.csv",
        "NYPL-unique-reserveid-sierra.csv",
    ]
