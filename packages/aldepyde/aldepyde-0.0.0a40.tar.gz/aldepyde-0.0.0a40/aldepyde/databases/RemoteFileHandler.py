import zlib
from io import BytesIO
import urllib.request
import gzip
from aldepyde import get_cache


GZIP = b"\x1f\x8b"
ZIP = b"\x50\x4B\x03\x04"

class RemoteFileHandler():
    @staticmethod
    def stream_url(url, chunk_size=8192):
        response = urllib.request.urlopen(url)
        head = response.read(4)
        mode = RemoteFileHandler.determine_ftype(head)
        if mode == 'gzip':
            decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
            yield decompressor.decompress(head)
            while stream := response.read(chunk_size):
                if not stream:
                    break
                yield decompressor.decompress(stream)
            yield decompressor.flush()

    @staticmethod
    def fetch_url(url: str) -> BytesIO:
        response = urllib.request.urlopen(url)
        return BytesIO(response.read())

    @staticmethod
    def determine_ftype(head:bytes) -> str:
        if head.startswith(GZIP):
            return "gzip"
        elif head.startswith(ZIP):
            return "zip"


    @staticmethod
    def is_gzip(stream: BytesIO) -> bool:
        magic_start = stream.read(2)
        stream.seek(0)
        return magic_start == b'\x1f\x8b'

    @staticmethod
    def unpack_tar_gz_bio(stream: BytesIO) -> BytesIO:
        with gzip.open(stream, "r") as gz:
            return BytesIO(gz.read())


