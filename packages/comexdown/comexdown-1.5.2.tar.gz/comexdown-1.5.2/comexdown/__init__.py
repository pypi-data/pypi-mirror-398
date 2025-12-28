"""Brazil's foreign trade data downloader"""

from pathlib import Path

from comexdown import download, fs, urls

__version__ = "1.5.2"


def get_year(path: Path, year: int, exp=False, imp=False, mun=False):
    """Download trade data

    Parameters
    ----------
    path : Path
        Destination path to save downloaded data.
    year : int
        Year to download
    exp : bool, optional
        If True, download exports data.
    imp : bool, optional
        If True, download imports data.
    mun : bool, optional
        If True, download municipality data.
    """
    directions = []
    if exp:
        directions.append("exp")
    if imp:
        directions.append("imp")

    for direction in directions:
        url = urls.trade(direction=direction, year=year, mun=mun)
        file_path = fs.path_trade(root=path, direction=direction, year=year, mun=mun)
        download.download_file(url, file_path)


def get_year_nbm(path: Path, year: int, exp=False, imp=False):
    """Download older trade data (NBM)

    Parameters
    ----------
    path : Path
        Destination path to save downloaded data.
    year : int
        Year to download
    exp : bool, optional
        If True, download export data.
    imp : bool, optional
        If True, download import data.
    """
    directions = []
    if exp:
        directions.append("exp")
    if imp:
        directions.append("imp")

    for direction in directions:
        url = urls.trade(direction=direction, year=year, nbm=True)
        file_path = fs.path_trade_nbm(root=path, direction=direction, year=year)
        download.download_file(url, file_path)


def get_complete(path: Path, exp=False, imp=False, mun=False):
    """Download complete trade data

    Parameters
    ----------
    path : Path
        Destination path to save downloaded data.
    exp : bool, optional
        If True, download complete export data.
    imp : bool, optional
        If True, download complete import data.
    mun : bool, optional
        If True, download complete municipality trade data.
    """
    directions = []
    if exp:
        directions.append("exp")
    if imp:
        directions.append("imp")

    for direction in directions:
        url = urls.complete(direction=direction, mun=mun)
        # Note: 'complete' files might have different naming conventions
        # The original code relied on download.exp_complete which hardcoded the filename.
        # fs.path_trade generates paths like .../exp/EXP_2020.csv, which isn't right for complete zip files.
        # We need to handle the output path for complete files.
        # The original code did: path / filename (where filename is separate).
        # We need to replicate that logic or add it to fs.py.
        # Let's simple determine the filename from the URL for now as the original did.
        filename = url.split("/")[-1]
        file_path = path / filename

        # Original code for complete files saved directly to `path` (or `path` was a directory).
        # The original implementation for complete files: `filepath = path / filename`.
        # So we expect `path` to be a directory.
        download.download_file(url, file_path)


def get_table(path: Path, table: str):
    """Download auxiliary code tables

    Parameters
    ----------
    path : Path
        Destination path to save downloaded code table directory.
    table : str
        Name of auxiliary code table to download
    """
    url = urls.table(table)
    file_path = fs.path_aux(root=path, name=table)
    download.download_file(url, file_path)
