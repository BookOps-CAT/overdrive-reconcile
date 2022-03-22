import pytest

from overdrive_reconcile.prep_sierra_export import is_reserve_id


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("92080423-8690-4580-A5AE-BCFCD3191CFB", True),
        ("14319803-7346-4454-934b-790eb8b24e23", True),
        ("EBL120658", False),
        ("Unowned Dawsonera PDA title", False),
    ],
)
def test_is_reserve_id(arg, expectation):
    assert is_reserve_id(arg) == expectation
