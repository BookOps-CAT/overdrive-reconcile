import gzip
import shutil


def unzip(source: str, output: str) -> None:
    """
    Unpacks .gz file into a csv file
    """
    with gzip.open(source, "r") as fin, open(output, "wb") as fout:
        shutil.copyfileobj(fin, fout)


if __name__ == "__main__":
    source = "./files/202203_nypl_overdrive_ids.csv.gz"
    output = "./files/202203_nypl_overdrive_ids.csv"

    unzip(source, output)
