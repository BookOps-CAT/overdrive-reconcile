"""Functions that allow for interactions with Overdrive Discovery APIs"""

import datetime
import logging
import os
from typing import Generator

import pandas as pd
import yaml
from bookops_overdrive import OverdriveAccessToken, OverdriveSession

from overdrive_reconcile.utils import create_dst_csv_fh

logger = logging.getLogger(__name__)


def get_overdrive_api_creds(library: str) -> None:
    """
    Retrieves Overdrive API credentials for the given library.

    Args:
        library: 'NYPL' or 'BPL'

    Returns:
        None. Credentials are loaded into environment variables.
    """
    library = library.upper()
    if library == "NYPL":
        fh = ".cred/.overdrive/nyp_overdrive_api.yaml"
        os.environ["OVERDRIVE_URL"] = "http://ebooks.nypl.org/ContentDetails.htm?ID="
    elif library == "BPL":
        os.environ["OVERDRIVE_URL"] = (
            "http://digitalbooks.brooklynpubliclibrary.org/ContentDetails.htm?ID="
        )
        return NotImplemented
    else:
        raise ValueError("Invalid library code passed")
    with open(os.path.join(os.environ["USERPROFILE"], fh), "r") as f:
        data = yaml.safe_load(f)
    if expired_coll_token(data["COLL_TOKEN_EXPIRATION"]):
        data = refresh_collection_token(
            creds=data, cred_file=os.path.join(os.environ["USERPROFILE"], fh)
        )
    for k, v in data.items():
        os.environ[f"{library}_{k}"] = v


def get_inventory(library: str) -> None:
    """
    Retrieves a list of registry IDs from the Overload Digital Inventory API
    representing the given library's entire digital collection. The results
    are saved to a csv (eg. 'NYPL-overdrive-api-reserve-ids.csv').
    Args:
        library: 'NYPL' or 'BPL'
    Returns:
        None
    """
    out_file = create_dst_csv_fh(library, "overdrive-api-reserve-ids")
    token = OverdriveAccessToken(
        key=os.environ[f"{library}_CLIENT_KEY"],
        secret=os.environ[f"{library}_CLIENT_SECRET"],
    )
    out = []
    with OverdriveSession(authorization=token) as session:
        coll_token = os.environ[f"{library}_COLL_TOKEN"]
        response = session.get_collection_inventory(collectionToken=coll_token)
        inventory = session.get(response.json()["files"][0]["fileUrl"])
        out.extend(inventory.json()["reserveIds"])
    out = [i.lower() for i in out]
    df = pd.DataFrame(out)
    df.to_csv(out_file, index=False, header=False)


def refresh_collection_token(creds: dict[str, str], cred_file: str) -> dict[str, str]:
    """
    Retrieve a new collection token for a given library and write the collection token
    to a yaml file containing that library's API credentials.

    Args:
        creds: the library's API credentials as a dictionary
        cred_file: the file name where the credentials should be written

    Returns:
        the library's API credentials as a dictionary with a new collection token
        and collection token expiration
    """
    token = OverdriveAccessToken(key=creds["CLIENT_KEY"], secret=creds["CLIENT_SECRET"])
    with OverdriveSession(authorization=token) as session:
        response = session.get_library_account_info(int(creds["LIBRARY_ID"]))
    creds["COLL_TOKEN"] = response.json()["collectionToken"]
    new_expiration = datetime.datetime.now() + datetime.timedelta(days=30)
    creds["COLL_TOKEN_EXPIRATION"] = new_expiration.strftime("%Y-%m-%d")
    with open(cred_file, "w") as fh:
        yaml.dump(creds, fh, default_flow_style=False)
    return creds


def expired_coll_token(token_expire: str) -> bool:
    """Check whether a collection token has expired."""
    today = datetime.datetime.now()
    if datetime.datetime.strptime(token_expire, "%Y-%m-%d") >= today:
        return False
    return True


def get_batches(iterable: list[str], size: int) -> Generator[list[str], None, None]:
    """Divide list of IDs into chunks to allow for batch API queries."""
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


def verify_missing_resources(library: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Query the Overdrive Metadata API to confirm the availability of titles whose reserve
    IDs have been identified as lacking records in Sierra.

    This check is conducted using the list of reserve IDs representing titles missing
    records in Sierra. The list is created from the outer merge of reserve IDs in
    Overdrive records exported from Sierra and reserve IDs retrieved from the Overdrive
    Digital Inventory API. This check is necessary in order to confirm that a record
    should be imported into Sierra because the library has an active license for the
    title.

    Args:
        library: 'NYPL' or 'BPL'
        df: a `pandas.DataFrame` object containing a list of reserve IDs to be checked
    Returns:
        a `pandas.DataFrame` object containing only those reserve IDs from the input
        that have active licenses.
    """
    token = OverdriveAccessToken(
        key=os.environ[f"{library}_CLIENT_KEY"],
        secret=os.environ[f"{library}_CLIENT_SECRET"],
    )
    ids_to_check = df["reserve_id"].to_list()
    available_ids = []
    with OverdriveSession(authorization=token) as session:
        id_count = len(ids_to_check)
        for i, chunk in enumerate(get_batches(ids_to_check, 50), start=1):
            logger.debug(
                f"Checking ids {i * 50 - 49}-{(i - 1) * 50 + len(chunk)} of {id_count}."
            )
            coll_token = os.environ[f"{library}_COLL_TOKEN"]
            response = session.get_bulk_metadata(coll_token, chunk)
            available_ids.extend(
                [
                    i.get("id")
                    for i in response.json()["metadata"]
                    if i.get("isOwnedByCollections")
                ]
            )
    return pd.DataFrame(data={"reserve_id": available_ids})
