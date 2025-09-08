"""Functions that allow for interactions with Overdrive Discovery APIs"""

import datetime
import os
from typing import Generator

import yaml
from bookops_overdrive import OverdriveAccessToken, OverdriveSession


def get_overdrive_api_creds(library: str) -> None:
    """
    Retrieves Overdrive API credentials for 'NYPL' or 'BPL' library
    Args:
        library: 'NYPL' or 'BPL'
    Returns:
        API credentials for the given library as a dictionary
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


def get_inventory(library: str) -> list[str]:
    """
    Retrieves a list of registry IDs from the Overload Digital Inventory API
    representing the given library's entire digital collection.
    Args:
        library: 'NYPL' or 'BPL'
    Returns:
        a list of registry IDs
    """
    creds = get_overdrive_api_creds(library=library)
    token = OverdriveAccessToken(key=creds["CLIENT_KEY"], secret=creds["CLIENT_SECRET"])
    out = []
    with OverdriveSession(authorization=token) as session:
        coll_token_resp = session.get_library_account_info(int(creds["LIBRARY_ID"]))
        coll_token = coll_token_resp.json()["collectionToken"]
        response = session.get_collection_inventory(collectionToken=coll_token)
        inventory = session.get(response.json()["files"][0]["fileUrl"])
        out.extend(inventory.json()["reserveIds"])
    return out


def refresh_collection_token(creds: dict[str, str], cred_file: str) -> dict[str, str]:
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
    today = datetime.datetime.now()
    if datetime.datetime.strptime(token_expire, "%Y-%m-%d") >= today:
        return False
    return True


def get_batches(iterable: list[str], size: int) -> Generator[list[str], None, None]:
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]
