from .sniff import _detect_gz
from .parse import parse
import gzip


def load(filepath):
    if _detect_gz(filepath):
        with gzip.open(filepath, 'rb') as gz:
            text = gz.read().decode('utf-8')
    else:
        with open(filepath, 'r') as fp:
            text = fp.read()
    return parse(text)
