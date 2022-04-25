import os

import pytest
import yaml
from sqlalchemy import create_engine, text
from sqlalchemy.engine.row import LegacyRow


sql_stmn = """
    SELECT i.identifier FROM identifiers i 
    JOIN licensepools lp ON i.id=lp.identifier_id 
    WHERE lp.licenses_owned > 0 AND i.type='Overdrive ID'
    LIMIT 2
"""


@pytest.mark.local
def test_bpl_conn(local_bpl_connection):
    engine = create_engine(local_bpl_connection)
    with engine.connect() as conn:
        results = conn.execute(text(sql_stmn))
        for r in results:
            assert isinstance(r, LegacyRow)
            assert isinstance(r[0], str)
            assert len(r[0]) == 36


@pytest.mark.local
def test_nypl_conn(local_nypl_connection):
    engine = create_engine(local_nypl_connection)
    with engine.connect() as conn:
        results = conn.execute(text(sql_stmn))
        for r in results:
            assert isinstance(r, LegacyRow)
            assert isinstance(r[0], str)
            assert len(r[0]) == 36
