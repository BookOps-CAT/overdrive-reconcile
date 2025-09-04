"""Functions that allow for interactions with Overdrive Discovery APIs"""

import os

import yaml
from bookops_overdrive import OverdriveAccessToken, OverdriveSession


def get_overdrive_api_creds(library: str) -> dict[str, str]:
    """
    Retrieves Overdrive API credentials for 'NYPL' or 'BPL' library
    Args:
        library: 'NYPL' or 'BPL'
    Returns:
        API credentials for the given library as a dictionary
    """
    if library.upper() == "NYPL":
        fh = ".cred/.overdrive/nyp_overdrive_api.yaml"
    elif library.upper() == "BPL":
        return NotImplemented
    else:
        raise ValueError("Invalid library code passed")
    with open(os.path.join(os.environ["USERPROFILE"], fh), "r") as f:
        data = yaml.safe_load(f)
        return data


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
