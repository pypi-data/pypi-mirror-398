from io import BytesIO
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from .pdb_client import pdb_Client
import gzip
from .parse_mmcif import _parse_mmcif
from .parse_pdb import _parse_pdb
from .parse import parse
from .load import load
from .fetch import fetch_text, fetch_raw, fetch

__all__ = ["fetch", "fetch_raw", "fetch_text", "load", "parse"]