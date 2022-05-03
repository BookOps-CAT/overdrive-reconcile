"""
Methods to interact with SimplyE databases
"""
import os

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
import yaml


RESERVE_ID_QUERY = """
    SELECT i.identifier FROM identifiers i 
    JOIN licensepools lp ON i.id=lp.identifier_id 
    WHERE lp.licenses_owned > 0 AND i.type='Overdrive ID'
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
