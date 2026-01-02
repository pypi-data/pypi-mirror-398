from ._dna import dna
from ._rna import rna
from ._amino_acid import amino_acid
from .Residue import Residue

# These three could probably be condensed
def CheckDNA(self, value: str, *args) -> bool:
    if args == ():
        args = self._dna_map[1]
    map = self.load_values(*args, store_as=None)
    if value in map['dna'].keys():
        return True
    return False


def CheckRNA(self, value: str, *args) -> bool:
    if args == ():
        args = self._map[1]
    map = self.load_values(*args, store_as=None)
    if value in map['dna'].keys():
        return True
    return False


def CheckAA(self, value: str, *args) -> bool:
    if args == ():
        args = self._map[1]
    map = self.load_values(*args, store_as=None)
    if value in map['dna'].keys():
        return True
    return False


def CheckResidue(self, value: str, *args) -> bool:
    if args == ():
        args = self._map[1]
    if self.CheckAA(value, *args):
        return True
    if self.CheckDNA(value, *args):
        return True
    if self.CheckRNA(value, *args):
        return True
    return False


# This method determines if something is DNA, RNA, or an amino acid.
# Don't be cheeky with this. If you aren't following the IUPAC naming schemes,
# you're gonna have a bad time.
#
# RNA has exclusively 1-letter codes: A, C, T, G, etc.
# DNA has exclusively 2-letter codes: DA, DC, DT, DG, etc.
# Amino acids have exclusively 3-letter codes
def ExtrapolateResidueType(self, value: str) -> object:
    if self.CheckRNA(value):
        return rna
    if self.CheckDNA(value):
        return dna
    if self.CheckAA(value):
        return amino_acid
    return Residue