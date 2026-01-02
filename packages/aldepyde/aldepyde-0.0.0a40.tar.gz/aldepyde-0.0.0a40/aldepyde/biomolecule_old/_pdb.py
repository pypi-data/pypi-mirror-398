# Submodule for reading, writing, and fetching PDB/mmcif files
from aldepyde.configurable import Configurable
from aldepyde.data import RemoteFileHandler
from ._AtomFactory import *
from ._Atom import Atom
from aldepyde import cache
from enum import Enum
import urllib.request
import requests
import gzip
from io import BytesIO
import os
from pathlib import Path

__all__ = ['PDB']


#TODO Basically rewrite this whole thing
class PDB(Configurable):
    class Mode(Enum):
        AUTO = 0
        PDB = 1
        CIF = 2

    def __init__(self):
        self._current = BytesIO()
        self._mode = self.Mode.AUTO


    def SetCurrent(self, stream: BytesIO) -> None:
        self._current = stream

    def Get(self) -> BytesIO:
        return self._current

    def ToString(self) -> str:
        return self._current.read().decode()

    def clear(self) -> 'PDB':
        return self.Clear()

    def Clear(self) -> 'PDB':
        self._current = BytesIO()
        return self

    def auto(self):
        self._mode = self.Mode.AUTO

    def pdb(self):
        self._mode = self.Mode.PDB

    def cif(self):
        self._mode = self.Mode.CIF


    def UpdateSettings(self):
        pass

    # Enabling bad behavior
    def fetch(self, code: str, extension: str="mmCIF") -> 'PDB':
        return self.Fetch(code, extension=extension)

    # Fetches a file directly from the PDB
    def Fetch(self, code: str, extension: str="mmCIF") -> 'PDB':
        code = code.lower().strip()
        if "pdb" in extension.lower():
            filepath = f"pdb/{code[1:3]}/pdb{code}.ent.gz"
            name = f"pdb{code}.ent.gz"
        else:
            filepath = f"mmCIF/{code[1:3]}/{code}.cif.gz"
            name = f"{code}.cif.gz"
        fetch_url = f"https://files.rcsb.org/pub/pdb/data/structures/divided/{filepath}"
        # stream = cache.grab_url(fetch_url, name)
        stream = RemoteFileHandler.fetch_file_from_pdb(fetch_url, name) # TODO Why is this only a tar file on first download?
        if RemoteFileHandler.is_gzip(stream):
            stream = RemoteFileHandler.unpack_tar_gz_bio(stream)
        # print(stream.getvalue())
        self.SetCurrent(stream)
        return self

    def Load(self, file: str) -> 'PDB':
        if file.endswith(".gz"):
            with gzip.open(file, "r") as gz:
                stream = BytesIO(gz.read())
        else:
            with open(file, "rb") as fp:
                stream = BytesIO()
                stream.write(fp.read())
        self.SetCurrent(stream)
        return self


    #Currently only works for PDB files
    # Fetches a file from the PDB or cache and saves it to a location
    def SaveFetch(self, code: str, path: str, extension: str="mmCIF") -> bool:
        stream = self.Fetch(code, extension, save=False).Get()
        try:
            with open(path, "wb") as fp:
                fp.write(stream.read())
        except:
            return False

    def Construct(self, data: str|None = None):
        if os.path.exists(data):
            pass



    # TODO Everything below here :)


    # This function does too much.
    def Read(self, file: str|BytesIO):
        # Whatever we have, convert it to a list of string-lines
        if isinstance(file, str) and len(file) == 4: # We have a code
            lines = self.Fetch(file, extension='pdb', as_string=True).split('\n')
        elif isinstance(file, str): # We have a stringline
            pass
        elif isinstance(file, str) and os.path.exists(file): # Path to a file
            # Get file type
            # Read accordingly
            pass
        elif isinstance(file, BytesIO): # File stream
            pass
        else:
            raise ValueError("Data to read must be a PDB 4-letter code, a file as a string, a path to a file,"
                             "or a fetched file.")
        for line in lines:
            if line[0:6] == "ATOM  " or line[0:6] == "HETATM":
                print(line)
                atom = self._parse_atom_pdb(line)
                print(atom)
        # print(lines)

    def ParsePDB(self, lines):
        for line in lines:
            if line[0:6] == "ATOM  " or line[0:6] == "HETATM":
                print(line)
                atom = self._parse_atom_pdb(line)
                print(atom)

    def ParseCIF(self):
        pass

    # I guess people may want this?
    def ParseXML(self):
        pass

    def _prepare_file(self, file: str|BytesIO) -> list:
        if isinstance(file, str):
            file = file.strip()
        if isinstance(file, str) and len(file) == 4: # Try reading as a pdb code
            lines = self.Fetch(file, extension='pdb', as_string=True).split('\n')
        elif isinstance(file, str) and os.path.exists(file): # Path to a file
            lines = self.Load(file).split('\n')
        elif isinstance(file, str): # We have a stringline
            lines = file.split('\n')
        elif isinstance(file, BytesIO): # File stream
            lines = file.read().decode().split('\n')
        else:
            raise ValueError("Unable to process file.")
        return lines

    def _parse_atom_cif(self, line: str) -> Atom:
        pass

    def _parse_atom_pdb(self, line: str) -> Atom:
        record_name = line[0:6]
        serial = line[6:11]
        name = line[12:16]
        altLoc = line[16]
        resName = line[17:20]
        chainID = line[21]
        resSeq = line[22:26]
        iCode = line[26]
        x = line[30:38]
        y = line[38:46]
        z = line[46:54]
        occupancy = line[54:60]
        tempFactor = line[60:66]
        element = line[76:78]
        charge = line[78:80]
        return AtomFactory.EnforcedAtom(
            record_name=record_name,
            serial=serial,
            name=name,
            altLoc=altLoc,
            resName=resName,
            chainID=chainID,
            resSeq=resSeq,
            iCode=iCode,
            x=x,
            y=y,
            z=z,
            occupancy=occupancy,
            tempFactor=tempFactor,
            element=element,
            charge=charge
        )

    # Surprisingly hard to design this because of how irregular PDB files are
    # @classmethod
    # def DetectFiletype(cls, file: str|BytesIO, trust_extension: bool = True) -> list:
    #     if isinstance(file, str) and os.path.exists(file):
    #         if trust_extension and len(Path(file).suffixes) != 0:
    #             return Path(file).suffixes
    #     extensions = []
    #     lines = cls._prepare_file(file)
    #


    # @classmethod
    # def IsPDB(cls, file: str|BytesIO):
    #     pass
        # Extrapolate file type
        # Go line by line
        # Grab symmetry information
        # Parse atom information Organize residues


        # urllib.request.urlretrieve(fetch_url, name)
        # response = requests.get(fetch_url)
        # response.raise_for_status()
        # with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
        #     with TextIOWrapper(gz) as fp:
        #         for line in fp.readlines():
        #             print(line.strip())
        #             break

        # print("Fetching ", prot)
        # import urllib.request
        # url = r'https://files.rcsb.org/download/' + prot.strip() + '.pdb'
        # try:
        #     with urllib.request.urlopen(url) as f:
        #         self.biomolecule_old.SetFetch(f.read().decode('utf-8'))
        #         self._Parse(hold_pdb)
        #         return True
        # except urllib.error.URLError:
        #     sys.stderr.write("The requested pdb code could not be retrieved or does not exist\n")
        #     if crash:
        #         exit()
        #     return False

    # def Fetch(self, code: str, extension: str="pdb"):
    #
    #     fetch_url = r"https://files.rcsb.org/pub/pdb/data/structures/divided/pdb/b8/"
    #
    #     url = r"https://www.rcsb.org/fasta/entry/" + prot.strip().upper() + r"/display"
    #     try:
    #         with urllib.request.urlopen(url) as f:
    #             return f.read().decode('utf-8')
    #     except urllib.error.URLError:
    #         sys.stderr.write("The requested pdb code could not be retrieved or does not exist\n")
    #         return False


# class PDB:
#     def __init__(self):
#         self.biomolecule_old = biomolecule_old()
#         # print(apalib.j_data.GetJson())
#
#     def Current(self):
#         return self.biomolecule_old
#
#     def FetchFASTA(self, prot):
#         import urllib.request
#         url = r"https://www.rcsb.org/fasta/entry/" + prot.strip().upper() + r"/display"
#         try:
#             with urllib.request.urlopen(url) as f:
#                 return f.read().decode('utf-8')
#         except urllib.error.URLError:
#             sys.stderr.write("The requested pdb code could not be retrieved or does not exist\n")
#             return False
#
#     # def FetchAsFile(self, prot):
#     #     import urllib.request
#     #     url = r'https://files.rcsb.org/download/' + prot.strip() + '.pdb'
#     #     try:
#     #         with urllib.request.urlopen(url) as f:
#
#     #Enabling bad behavior
#     def fetch(self, prot, crash=True, hold_pdb=False):
#         return self.Fetch(prot, crash, hold_pdb)
#     def Fetch(self, prot, crash = True, hold_pdb=False):
#         # print("Fetching ", prot)
#         import urllib.request
#         url = r'https://files.rcsb.org/download/' + prot.strip() + '.pdb'
#         try:
#             with urllib.request.urlopen(url) as f:
#                 self.biomolecule_old.SetFetch(f.read().decode('utf-8'))
#                 self._Parse(hold_pdb)
#                 return True
#         except urllib.error.URLError:
#             sys.stderr.write("The requested pdb code could not be retrieved or does not exist\n")
#             if crash:
#                 exit()
#             return False
#
#     def Read(self, path, hold_pdb=False):
#         with open(path, 'r') as fp:
#             self.biomolecule_old.SetFetch(fp.read())
#             self._Parse(hold_pdb)
#
#     # Wrapper for the ParsePDB file to allow functionality with a fetched protein
#     def _Parse(self, hold_pdb=False):
#         try:
#             if self.biomolecule_old.GetFetch() is None:
#                 raise apaExcept.NoFetchError
#             return self._ParsePDB(self.biomolecule_old.GetFetch(), hold_pdb)
#             # return self._ParsePDB(self.container.GetFetch().splitlines())
#         except apaExcept.NoFetchError as e:
#             sys.stderr.write(e.message)
#
#
#     #PDB standard described here: https://www.wwpdb.org/documentation/file-format-content/format33/v3.3.html
#     def _ParsePDB(self, raw_pdb, hold_pdb=False):
#         self.biomolecule_old.ClearAll()
#         remark350 = ""
#         if hold_pdb:
#             self.biomolecule_old.SetFetch(raw_pdb)
#         for line in raw_pdb.splitlines():
#             # print(line)
#             if line[0:6] == 'ATOM  ' or line[0:6] == 'HETATM':
#                 self._ExtractAtomAndResidue(line)
#             if line.find("REMARK 350") != -1:
#                 remark350 += line + "\n"
#
#         symmetry_groups = self._ParseRemark350(remark350)
#         self.biomolecule_old._AddSymmetry(symmetry_groups)
#         self.biomolecule_old._PostParseEvaluations()
#     def _ParseRemark350(self, remark350):
#         lines = remark350.splitlines()
#         lines.append("END")
#         symFlag = False
#         biomolecules = []
#         for line in lines:
#             if 'REMARK 350 APPLY' in line and ":" in line and symFlag is False:
#                 symFlag = True
#                 symLines = []
#                 chains = line[line.find(":")+1:].replace(",", " ").split()
#             elif 'REMARK 350 APPLY' in line and ":" in line and symFlag is True:
#                 chains += line[line.find(":")+1:].replace(",", " ").split() #This feels dangerous
#             elif 'AND CHAINS:' in line and symFlag is True:
#                 chains += line[line.find(":") + 1:].replace(",", " ").split() #This also feels dangerous
#             elif 'BIOMT' in line and symFlag:
#                 BIOMT = line[13:19].strip()
#                 id = line[19:23].strip()
#                 x = line[23:33].strip()
#                 y = line[33:43].strip()
#                 z = line[43:53].strip()
#                 m = line[53:].strip()
#                 symLines.append([BIOMT, int(id), float(x), float(y), float(z) ,float(m)])
#             elif symFlag:
#                 symFlag = False
#                 biomolecule_old = {}
#                 biomolecule_old['chains'] = chains
#                 for sl in symLines:
#                     if sl[1] not in biomolecule_old.keys():
#                         biomolecule_old[sl[1]] = []
#                     biomolecule_old[sl[1]].append([sl[0]] + sl[2:])
#                 biomolecules.append(biomolecule_old)
#             #I hate PDB file format
#         for i in range(len(biomolecules)):
#             biomolecule_old = biomolecules[i]
#             for key in biomolecule_old.keys():
#                 biomolecule_old[key].sort(key=lambda x:x[0])
#                 for i in range(len(biomolecule_old[key])):
#                     if key == "chains":
#                         continue
#                     biomolecule_old[key][i].pop(0)
#         return biomolecules
#
#     def _ExtractAtomAndResidue(self, line):
#         serial = line[6:11].strip()
#         name = line[12:16].strip()
#         altLoc = line[16].strip()
#         resName = line[17:20].strip()
#         chainID = line[21].strip()
#         resSeq = line[22:26].strip()
#         iCode = line[26].strip()
#         x = line[30:38].strip()
#         y = line[38:46].strip()
#         z = line[46:54].strip()
#         occupancy = line[54:60].strip()
#         tempFactor = line[60:66].strip()
#         element = line[76:78].strip()
#         charge = line[78:80].strip()
#         atom = Atom.Atom(serial=serial, name=name, altLoc=altLoc, resName=resName, chainID=chainID, resSeq=resSeq,
#                          iCode=iCode, x=float(x), y=float(y), z=float(z), occupancy=occupancy, tempFactor=tempFactor, element=element,
#                          charge=charge)
#         if "HETATM" in line:
#             resType = "HETATM"
#         else:
#             resType = self.DetermineResType(resName)
#         residue = self.biomolecule_old.AddResidue(resType, resSeq, resName, chainID)
#         residue.InsertAtom(atom)
#
#     def DetermineResType(self, res_code):
#         if data.ValidateRNA(res_code):
#             return 'RNA'
#         elif data.ValidateDNA(res_code):
#             return 'DNA'
#         elif data.ValidateAA(res_code):
#             return "AA"
#         else:
#             return "HETATM"
#
#     #Remove all of the waters from the current fetch. Probably make this more general for any HETATM group. Make a wrapper?
#     def RemoveWater(self):
#         h_chains = self.biomolecule_old.GetHETATMChains()
#         for chain in h_chains.keys():
#             h_chains[chain] = {key: value for (key, value) in h_chains[chain].items() if value.GetResName().upper() != 'HOH'}
#
#     # def Validate(self, **kwargs):
#     #     for key in kwargs:
#     #         if key != 'pdb' or (key == 'pdb' and not isinstance(kwargs['pdb'], str)):
#     #             raise apalib.apalibExceptions.BadKwarg('pdb=<pdb_to_validate>')
#
#     #Write contents to a PDB file
#
#     def AddChain(self, collection, name=None):
#         if name is None:
#             chains = list(self.biomolecule_old.Chains.keys())
#             for i in range(26):
#                 if chr(ord('z') - i) not in chains:
#                     name = chr(ord('z') - i)
#                     break
#         else:
#             if len(name) > 1 or not name.isalnum():
#                 raise BadNameException("A chain must be a single-character alphanumeric input")
#         #Rechain all of the atoms and residues with new name
#         for residue in collection:
#             residue.SetChainID(name)
#             for atom in residue.GetAtoms():
#                 atom.SetChainID(name)
#         self.biomolecule_old.AddChain(name)
#         self.biomolecule_old.Chains[name] = collection
#
#     def WritePDB(self, fp):
#         s = sorted(self.biomolecule_old.DumpResidues(), key=lambda x: x.seqNum)
#         with open(fp, "w") as f:
#             for res in s:
#                 f.write(res.WriteForPDB())
#
#     #Write contents to FASTA
#     def ToFASTA(self):
#         ls = self.biomolecule_old.AsList(ordered=True)
#         retStr = ""
#         for r in ls:
#             if data.ValidateAA(r.resName):
#                 name = data.Map("Amino Acids", r.resName)
#                 retStr += data.GetJson()["Amino Acids"][name]["1code"]
#             elif r.resName.upper() != "HOH":
#                 retStr += "X"
#         return retStr