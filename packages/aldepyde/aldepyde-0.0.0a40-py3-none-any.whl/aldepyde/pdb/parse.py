from typing import Optional
from ..biomolecule.structure import Structure
from .parse_pdb import _parse_pdb
from .parse_mmcif import _parse_mmcif
from .sniff import is_mmcif

# This could grow, so alone it goes!
def parse(text:str) -> Optional[Structure]:
    if is_mmcif(text):
        return _parse_mmcif(text)
    else:
        return _parse_pdb(text)
