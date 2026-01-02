from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field
from ..biomolecule.structure import Atom, Residue, Chain, Model, Structure


def catagorize_lines(text, *args:str) -> dict:
    catagories = {k:list() for k in args}
    for line in text.split('\n'):
        if line.startswith(args):
            match = next(p for p in args if line.startswith(p))
            catagories[match].append(line)
    return catagories

# PDB documentation guarantees only 1 HEADER per file
def get_title_from_header(header):
    return header[0][62:66] if len(header) != 0 else None

def _slice(s, start, end):
    if start >= len(s):
        return ""
    return s[start:end].strip()

def _parse_atom(s:str) -> Optional[Atom]:
    serial = _slice(s, 6, 11)
    atom_name = _slice(s, 12, 16)
    altLoc = _slice(s, 16, 17)
    x = _slice(s, 30, 38)
    y = _slice(s, 38, 46)
    z = _slice(s, 46, 54)
    try:
        x = float(x)
        y = float(y)
        z = float(z)
    except ValueError:
        return None
    occupancy = _slice(s, 54, 60)
    try:
        occupancy = float(occupancy)
    except ValueError:
        return None
    tempFactor = _slice(s, 60, 66)
    try:
        tempFactor = float(tempFactor)
    except ValueError:
        return None
    element = _slice(s, 76, 78)
    charge = _slice(s, 78, 80)
    return Atom(serial=serial,
                name=atom_name,
                altloc=altLoc,
                coord=(x, y, z),
                occupancy=occupancy,
                b_factor=tempFactor,
                element=element,
                charge=charge,
                is_het=s.startswith('HETATM'))

def _parse_pdb(text:str) -> Optional[Structure]:
    special_lines = catagorize_lines(text, 'HEADER', "TITLE", "REMARK 350")
    structure_name = get_title_from_header(special_lines['HEADER'])
    title = "".join(special_lines['TITLE']) # TODO clean this up
    structure = Structure(id=structure_name)
    # structure = Structure(id=structure_name, title=title)
    lines = text.split('\n')
    current_model = None
    chains:Dict[str, Chain] = {}
    residues:Dict[str, Residue] = {}
    # structure.add_model(current_model)
    for line in lines:
        if line.startswith('MODEL'):
            model_index = _slice(line, 10, 14)
            current_model = Model(model_index)
            structure.add_model(current_model)
            chains = {}
            residues = {}
        if line.startswith('ENDMDL'):
            chains = {}
            residues = {}
        if line.startswith(('ATOM', 'HETATM')):
            if current_model is None:
                current_model = Model('1')
                chains: Dict[str, Chain] = {}
                residues: Dict[str, Residue] = {}
                structure.add_model(current_model)
            atom = _parse_atom(line)
            if atom is None:
                continue
            chain_id = _slice(line, 21, 22)
            if chain_id not in chains:
                chains[chain_id] = Chain(id=chain_id)
                current_model.add_chain(chains[chain_id])

            resName = _slice(line, 17, 20)
            resSeq = _slice(line, 22, 26)
            # resSeq = int(resSeq)

            i_code = _slice(line, 26, 27)
            if resSeq not in residues:
                residues[resSeq] = Residue(resName, resSeq, i_code)
                chains[chain_id].add_residue(residues[resSeq])
            residues[resSeq].add_atom(atom)
    return structure