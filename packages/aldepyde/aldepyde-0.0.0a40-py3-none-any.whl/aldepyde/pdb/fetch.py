from io import BytesIO
from .pdb_client import pdb_Client
from .parse import parse
import gzip


def fetch_text(code, extension='mmcif') -> str:
    client = pdb_Client()
    raw_gz = client.fetch(code=code, extension=extension)
    with gzip.GzipFile(fileobj=raw_gz) as gz:
        return gz.read().decode('utf-8')

def fetch_raw(code, extension='mmcif') -> BytesIO:
    client = pdb_Client()
    return client.fetch(code=code, extension=extension)

def fetch(code, extension='mmcif'):
    return parse(fetch_text(code=code, extension=extension))