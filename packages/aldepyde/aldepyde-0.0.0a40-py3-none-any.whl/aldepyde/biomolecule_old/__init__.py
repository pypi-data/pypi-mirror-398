from ._amino_acid import *
from ._Atom import *
from ._AtomFactory import *
from ._dna import *
from ._pdb import *
# from .Residue import * # This probably doesn't need to be revealed to the user
from ._rna import *

__all__ =  list(set(_amino_acid.__all__.copy()) |
           set(_Atom.__all__.copy()) |
           set(_AtomFactory.__all__.copy()) |
           set(_dna.__all__.copy()) |
           set(_pdb.__all__.copy()) |
           set(_rna.__all__.copy()))

import sys

sys.stderr.write("Note that the `biomolecule_old` submodule is not yet fully tested and may be unstable")