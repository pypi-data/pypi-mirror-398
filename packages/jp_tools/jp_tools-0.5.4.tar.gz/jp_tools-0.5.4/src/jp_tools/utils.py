import importlib.util
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from tqdm import tqdm


def download(url: str, filename: str, verify: bool = True) -> None:
    """
    Pulls a file from a URL and saves it in the filename. Used by the class to pull external files.

    Parameters
    ----------
    url: str
        The URL to pull the file from.
    filename: str
        The filename to save the file to.
    verify: bool
        If True, verifies the SSL certificate. If False, does not verify the SSL certificate.

    Returns
    -------
    None
    """
    if os.path.exists(filename):
        return None

    chunk_size = 10 * 1024 * 1024

    with requests.get(url, stream=True, verify=verify) as response:
        total_size = int(response.headers.get("content-length", 0))

        with tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc="Downloading",
        ) as bar:
            with open(filename, "wb") as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file.write(chunk)
                        bar.update(
                            len(chunk)
                        )  # Update the progress bar with the size of the chunk


def parse_download(url: str, filename: str, verify: bool = True) -> None:
    """
    Downloads a CSV file from a given URL, parses it with Polars, and saves it as a Parquet file.

    This function first downloads the CSV file to a temporary location using the `download` function.
    It then reads the CSV into a Polars DataFrame, verifies that the file is not empty, and writes
    the data to the specified output path in Parquet format.

    Parameters
    ----------
    url : str
        The URL of the CSV file to download.
    filename : str
        The destination file path where the Parquet file will be saved.
    verify : bool, optional
        Whether to verify the SSL certificate during the download (default is True).

    Raises
    ------
    ModuleNotFoundError
        If the `polars` library is not installed.
    ValueError
        If the downloaded file is empty or failed to parse correctly.

    Returns
    -------
    None
        The function saves the parsed Parquet file and does not return any value.
    """
    if importlib.util.find_spec("polars") is None:
        raise ModuleNotFoundError("need to install extra packages (polars)")

    import polars as pl

    temp_filename = f"{tempfile.gettempdir()}/{hash(filename)}.csv"
    download(url=url, filename=temp_filename, verify=verify)
    df = pl.read_csv(temp_filename, ignore_errors=True)
    if df.is_empty():
        print(filename)
        raise ValueError("File Did not download correctly")
    df.write_parquet(filename)


def batch_download(
    file_map: dict, max_workers: int = 4, verify: bool = True, parse: bool = False
):
    """
    Downloads multiple files concurrently. Uses `parse_download` if `parse=True`.

    Parameters
    ----------
    file_map : dict
        A mapping of URL -> filename.
    max_workers : int
        Number of parallel threads.
    verify : bool
        Whether to verify SSL certificates.
    parse : bool
        If True, downloads and parses CSV files into Parquet.
    """
    if parse:
        if importlib.util.find_spec("polars") is None:
            raise ModuleNotFoundError("need to install extra packages (polars)")
        download_func = parse_download
    else:
        download_func = download

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(download_func, url, filename, verify): (url, filename)
            for url, filename in file_map.items()
        }

        for future in as_completed(futures):
            url, filename = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Failed to download {url}: {e}")
