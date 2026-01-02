from abc import ABC, abstractmethod
import gzip
import requests
import os
from typing import Tuple, BinaryIO
from io import TextIOWrapper

class streamable_database(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def fetch(self, url):
        pass

    @abstractmethod
    def fetch_code(self, codes):
        pass

    @abstractmethod
    def parse(self, text):
        pass

    @staticmethod
    def open_stream(source:str) -> Tuple[BinaryIO, int] | None:
        if source.startswith('http://') or source.startswith('https://'):
            resp = requests.get(source, stream=True)
            resp.raise_for_status()
            length = resp.headers.get("Content-Length")
            return resp.raw, int(length) if length else None
        else:
            size = os.path.getsize(source)
            return open(source, 'rb'), size



    # Yes, I know the first conditionals do the same thing

    def __call__(self):
        pass

class local_database(ABC):

    def __init__(self, filepath=None, as_fp=False):
        self.fp = None
        self.as_fp = as_fp
        self.size = None
        self.load_path(filepath)

    def refresh(self):
        if self.fp is not None:
            self.fp.seek(0)

    def load_path(self, filepath):
        self.filepath = filepath

    def get_pointer(self):
        return self.fp

    def __enter__(self):
        self.fp, self.size = local_database.open_stream(self.filepath)
        if self.as_fp:
            return self.fp
        else:
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fp is not None:
            self.fp.close()
        self.fp = None

    @staticmethod
    def open_stream(source:str) -> Tuple[BinaryIO, int] | None:
        size = os.path.getsize(source)
        return open(source, 'rb'), size