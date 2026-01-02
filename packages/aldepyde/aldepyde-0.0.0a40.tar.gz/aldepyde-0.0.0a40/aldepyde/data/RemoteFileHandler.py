from io import BytesIO
import requests
import gzip
from urllib.request import urlopen
import aldepyde


class RemoteFileHandler():
    @staticmethod
    def fetch_file_from_pdb(url: str, name) -> BytesIO:
        cache = aldepyde.get_cache()
        if cache.in_cache(name):
            return cache.extract_from_cache(name)
        # Return a requested file as a BytesIO stream from a URL or the cache
        response = requests.get(url)
        response.raise_for_status()
        stream_io = BytesIO(response.content)
        aldepyde.get_cache().save_to_cache(stream_io, name)
        return stream_io

    @staticmethod
    def fetch_file(url: str) -> BytesIO:
        response = urlopen(url)
        return BytesIO(response.read())

    @staticmethod
    def is_gzip(stream: BytesIO) -> bool:
        magic_start = stream.read(2)
        stream.seek(0)
        return magic_start == b'\x1f\x8b'

    @staticmethod
    def unpack_tar_gz_bio(stream: BytesIO) -> BytesIO:
        with gzip.open(stream, "r") as gz:
            return BytesIO(gz.read())


