"""
Methods to interact with SimplyE databases
"""

import os

import yaml
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine


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
        return ".cred/.simplyE/bpl_simply_e.yaml"
    elif library == "NYPL":
        return ".cred/.simplyE/nyp_simply_e.yaml"
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
