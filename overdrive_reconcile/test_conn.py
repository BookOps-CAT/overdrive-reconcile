import os

import yaml
from sqlalchemy import create_engine, text

def get_creds(library: str):
    fh = None
    if library == "BPL":
        fh = ".simplyE/bpl_simply_e.yaml"
    elif library == "NYPL":
        fh = ".simplyE/nyp_simply_e.yaml"
    
    with open(os.path.join(os.environ["USERPROFILE"], fh), "r") as f:
        data = yaml.safe_load(f)
        return data

def connection(creds: dict):
    conn = f"postgresql://{creds['USER']}:{creds['PASSWORD']}@{creds['HOST']}/{creds['DATABASE']}"
    return conn

def test_conn(connection: str):
    engine = create_engine(connection)
    with engine.connect() as conn:
        results = conn.execute(
            text(
                """
                SELECT i.identifier FROM identifiers i 
                JOIN licensepools lp ON i.id=lp.identifier_id 
                WHERE lp.licenses_owned > 0 AND i.type='Overdrive ID'
                LIMIT 5
                """
            ))
        print(len(results))
        for r in results:
            print(r)


if __name__ == "__main__":
    creds = get_creds("NYPL")
    conn = connection(creds)
    test_conn(conn)

