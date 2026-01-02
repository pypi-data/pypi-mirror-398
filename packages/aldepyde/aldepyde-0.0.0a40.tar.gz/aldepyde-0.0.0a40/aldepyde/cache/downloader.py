from io import BytesIO, TextIOWrapper
import requests
import gzip


def _fetch_file_from_pdb(url: str, filename: str) -> BytesIO:
    # Return a requested file as a BytesIO stream from a URL or the cache
    response = requests.get(url)
    response.raise_for_status()
    stream_io = BytesIO(response.content)
    return stream_io


