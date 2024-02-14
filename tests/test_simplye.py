import pytest

from sqlalchemy.engine.base import Engine

from overdrive_reconcile.simplye import (
    get_cred_fh,
    get_simplye_creds,
    simplye_connection,
)


@pytest.mark.parametrize(
    "arg, expectation",
    [
        ("NYPL", ".cred/.simplyE/nyp_simply_e.yaml"),
        ("BPL", ".cred/.simplyE/bpl_simply_e.yaml"),
    ],
)
def test_get_cred_fh(arg, expectation):
    assert get_cred_fh(arg) == expectation


def test_get_cred_fh_exception():
    with pytest.raises(ValueError):
        get_cred_fh(None)


@pytest.mark.local
@pytest.mark.parametrize("arg", ["BPL", "NYPL"])
def test_simplye_creds(arg):
    result = get_simplye_creds(arg)

    assert isinstance(result, dict)
    assert result is not {}
    assert sorted(result.keys()) == ["DATABASE", "HOST", "PASSWORD", "USER"]


@pytest.mark.local
def test_simplye_connection():
    result = simplye_connection("NYPL")
    assert isinstance(result, Engine)
