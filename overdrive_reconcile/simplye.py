"""
Methods to interact with SimplyE databases
"""
import os

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
import yaml


def get_reserve_id_query() -> str:
    return """
        SELECT i.identifier FROM identifiers i
            JOIN licensepools lp ON i.id = lp.identifier_id
            JOIN editions e ON lp.presentation_edition_id = e.id
        WHERE lp.licenses_owned > 0 AND i.type = 'Overdrive ID' AND e.medium != 'Video';
    """


def get_cred_fh(library: str) -> str:
    """
    Determines correct SimplyE credential file
    """
    if library == "BPL":
        return ".simplyE/bpl_simply_e.yaml"
    elif library == "NYPL":
        return ".simplyE/nyp_simply_e.yaml"
    else:
        raise ValueError("Invalid library code passsed")


def get_simplye_creds(library: str) -> dict:
    """
    Retrieves SimplyE database credentials for 'NYPL' or 'BPL' library

    Args:
        library:                'NYPL' or 'BPL'
    """
    fh = get_cred_fh(library)

    with open(os.path.join(os.environ["USERPROFILE"], fh), "r") as f:
        data = yaml.safe_load(f)
        return data


def simplye_connection(library: str) -> Engine:
    """
    Creates sqlalchemy connectable object (engine) to be used
    to query SimplyE database

    Args:
        library:                'NYPL' or 'BPL'
    """
    creds = get_simplye_creds(library)
    conn = f"postgresql://{creds.get('USER')}:{creds.get('PASSWORD')}@{creds.get('HOST')}/{creds.get('DATABASE')}"
    engine = create_engine(conn)
    return engine


def get_reserve_id(library: str, reserve_id: str) -> None:
    from sqlalchemy import text

    engine = simplye_connection(library)
    stmn = text(
        """
    SELECT * FROM identifiers i
    JOIN licensepools lp ON i.id=lp.identifier_id
    WHERE i.type='Overdrive ID' AND i.identifier=:reserve_id
    """
    )
    stmn = stmn.bindparams(reserve_id=reserve_id)
    with engine.connect() as conn:
        result = conn.execute(stmn).all()

        for row in result:
            # print(row)
            for k, v in row._mapping.items():
                print(k, v)

        print(f"found {len(result)} results.")


def get_reserve_id_excluding_video(library: str, reserve_id: str) -> None:
    from sqlalchemy import text

    engine = simplye_connection(library)
    stmt = text(
        """
        SELECT i.identifier
        FROM identifiers i
            JOIN licensepools lp ON i.id = lp.identifier_id
            JOIN editions e ON lp.presentation_edition_id = e.id
        WHERE i.type = 'Overdrive ID' AND i.identifier=:reserve_id AND e.medium != 'Video';
        """
    )
    stmt = stmt.bindparams(reserve_id=reserve_id)
    with engine.connect() as conn:
        result = conn.execute(stmt).all()

        print(f"found {len(result)} results.")

        for row in result:
            for k, v in row._mapping.items():
                print(k, v)
