from functools import reduce
from importlib.resources import files
import json
import sys

# from aldepyde.biomolecule_old import dna, rna, amino_acid, Residue

class _DataSingleton(type):
    _instance = {}
    def __call__(cls, *args, singleton=True, **kwargs):
        if singleton:
            return super(_DataSingleton, cls).__call__(*args, **kwargs)
        if cls not in cls._instance:
            cls._instance[cls] = super(_DataSingleton, cls).__call__(*args, **kwargs)
        return cls._instance[cls]


class Data(metaclass=_DataSingleton):
    # Map paths
    _map = ("map", ("map",))
    _dna_map = ("dna_map", ("map", "dna"))
    _rna_map = ("rna_map", ("map", "rna"))
    _amino_map = ("amino_map", ("map", "amino_acid"))

    def __init__(self, json_location = None):
        if json_location is None:
            ###### If something breaks, you can use this as a backup way to access the data ######
            # base = os.path.dirname(os.path.abspath(__file__))
            # json_location = os.path.join(base, "json", "chemistry.json")
            json_location = files("aldepyde.json").joinpath("chemistry.json")
        self.json_location = json_location
        self._loaded = {}


    # Technically, this is the only function we need.
    # You get the rest because I care <3
    def load_values(self, *args, store_as: str = None):
        with open(self.json_location) as js:
            if args in self._loaded:
                return self.__dict__[self._loaded[args]]
            j_data = reduce(lambda d, key: d[key], args, json.load(js))
            if store_as is not None and args not in self._loaded:
                self._loaded[args] = store_as
                setattr(self, store_as, j_data)
                self.__dict__[store_as]['_key'] = args
            return j_data

    def unload(self, attr_name: str) -> bool:
        if attr_name not in self.__dict__.keys():
            return False
        try:
            item = self.__dict__.pop(attr_name)['_key']
            self._loaded.pop(item)
        except KeyError:
            # This really shouldn't occur unless you're trying
            raise KeyError(f'An error occured while attempting to remove {attr_name} from the data object.'
                     f' Are you sure you are attempting to unload a loaded value?')
        return True

    # TODO check if something is already loaded
    def GrabParent(self, *args):
        pass

    # Cute lil' recursive method that shows the structure of a loaded json. Maybe not so practical
    # at runtime, but helpful for debugging and planning your loads
    def reveal(self, *args, indent="  ") -> str:
        j_data = self.load_values(*args, store_as=None)
        return self._reveal_helper(j_data, indent, indent)

    def _reveal_helper(self, js: dict, indent, adder, ret_str="") -> str:
        for key in js:
            if not isinstance(js[key], dict):
                continue
            ret_str += indent+key + "\n"
            ret_str = self._reveal_helper(js[key], indent+adder, adder, ret_str)
        return ret_str

    def Map(self, residue: str|None, *args, store_as: str|None =_map[0], residue_type: str ='amino_acid') -> None|str:
        if args == ():
            args = self._map[1]
            if store_as is None:
                store_as = self._map[0]
        residue_type = residue_type.lower()
        if residue_type.lower() not in ["dna", "rna", "amino_acid", "element"]:
            print("Allowed residue_type mappins are 'dna', 'rna', 'amino_acid', and 'element'", file=sys.stderr)
        map = self.load_values(*args, store_as=store_as)
        if residue is None: # Just initialize self.map
            return None
        return map[residue_type][residue.lower()]


    # # These three could probably be condensed
    # def CheckDNA(self, value: str, *args) -> bool:
    #     if args == ():
    #         args = self._dna_map[1]
    #     map = self.load_values(*args, store_as=None)
    #     if value in map['dna'].keys():
    #         return True
    #     return False
    #
    #
    # def CheckRNA(self, value: str, *args) -> bool:
    #     if args == ():
    #         args = self._map[1]
    #     map = self.load_values(*args, store_as=None)
    #     if value in map['dna'].keys():
    #         return True
    #     return False
    #
    # def CheckAA(self, value: str, *args) -> bool:
    #     if args == ():
    #         args = self._map[1]
    #     map = self.load_values(*args, store_as=None)
    #     if value in map['dna'].keys():
    #         return True
    #     return False
    #
    # def CheckResidue(self, value: str, *args) -> bool:
    #     if args == ():
    #         args = self._map[1]
    #     if self.CheckAA(value, *args):
    #         return True
    #     if self.CheckDNA(value, *args):
    #         return True
    #     if self.CheckRNA(value, *args):
    #         return True
    #     return False
    #
    # # This method determines if something is DNA, RNA, or an amino acid.
    # # Don't be cheeky with this. If you aren't following the IUPAC naming schemes,
    # # you're gonna have a bad time.
    # #
    # # RNA has exclusively 1-letter codes: A, C, T, G, etc.
    # # DNA has exclusively 2-letter codes: DA, DC, DT, DG, etc.
    # # Amino acids have exclusively 3-letter codes
    # # def ExtrapolateResidueType(self, value: str) -> object:
    # #     if self.CheckRNA(value):
    # #         return rna
    # #     if self.CheckDNA(value):
    # #         return dna
    # #     if self.CheckAA(value):
    # #         return amino_acid
    # #     return Residue

data = Data()



