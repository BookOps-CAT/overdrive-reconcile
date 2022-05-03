import sys

from overdrive_reconcile.reconcile import reconcile


def main(library: str, sierra_export_fh: str) -> None:

    if library not in "BPL,NYPL":
        raise ValueError("Invalid library argument.")
    if not isinstance(sierra_export_fh, str):
        raise ValueError("Invalid type of sierra_export_fh. Must be str.")

    reconcile(library, sierra_export_fh)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
