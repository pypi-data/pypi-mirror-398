from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field
from ..biomolecule.structure import Atom, Residue, Chain, Model, Structure


@dataclass
class Loop():
    title: str
    canon_loop: bool
    tokens: List[str] = field(default_factory=list)
    data: str = ""
    data_fields: List[list] = field(default_factory=list)

    def set_title(self, title):
        self.title = title

    def add_token(self, token):
        self.tokens.append(token)

    def add_data(self, data):
        self.data += data

    def add_row(self, row):
        self.data_fields.append(row)

    def is_canon(self):
        return self.canon_loop

def catagorize_mmcif_sections(text):
    loops: Dict[str, Loop] = {}
    canon_loop = False
    in_text_field = False
    current_loop = Loop(str(None), False)
    for line in text.split('\n'):
        # End of group
        if len(line.strip()) < 1:
            continue
        if line.lower().startswith('data_'):
            continue
        if line.strip() == '#':
            current_loop = Loop(str(None), False)
            continue
        if line.strip() == ';':
            in_text_field = False
        # Start of a canon loop
        if line.lower().startswith('loop_'):
            canon_loop = True
            continue
        line += '\n' # <-- I hate semicolons
        if canon_loop:
            title = line.strip()[:line.find('.')]
            current_loop = Loop(title, canon_loop)
            loops[title] = current_loop
            canon_loop = False
        if current_loop.is_canon() and line.startswith('_'):
            current_loop.add_token(line.strip())
            continue
        elif current_loop.is_canon() and not line.startswith('_'):
            current_loop.add_data(line)

        if not current_loop.is_canon():
            title = line.strip()[:line.find('.')]
            if title not in loops.keys():
                loops[title] = current_loop
                current_loop.set_title(title)
            current_loop.add_token(line.split()[0])
            current_loop.add_data(line[len(line.split()[0]):])
    return loops

def split_list(ls:list, n:int):
    q, r = divmod(len(ls), n)
    if r != 0:
        yield None
    try:
        for i in range(0, len(ls), n):
            yield ls[i:i + n]
    except ValueError:
        yield None

SPECIAL_CHARACTERS = {'\'', '\"', '\n;'}
def evaluate_fields(loops:Dict[str, Loop]):
    for key in loops.keys():
        loop = loops[key]
        current_value = ""
        special_flag = ""
        values = list()
        for i in range(len(loop.data)):
            char = loop.data[i]
            if char in SPECIAL_CHARACTERS or loop.data[i - 1]+char in SPECIAL_CHARACTERS:
                if special_flag == "":
                    special_flag = char
                elif special_flag == char:
                    special_flag = ""
            # Hit whitespace. Attempt to complete a value
            if char.isspace() and special_flag == "":
                if len(current_value) > 0:
                    values.append(current_value)
                    current_value = ""
                else:
                    continue
            else:
                current_value += char
        for l in split_list(values, len(loop.tokens)):
            loop.add_row(l)
    return loops
'''
    return Atom(serial=serial,
                name=atom_name,
                altloc=altLoc,
                coord=(x, y, z),
                occupancy=occupancy,
                b_factor=tempFactor,
                element=element,
                charge=charge,
                is_het=s.startswith('HETATM'))
'''
def _build_mmcif_structure(name:str, _atom_site: Loop) -> Structure|None:
    fl = _atom_site.tokens
    try:
        id_idx = fl.index('_atom_site.id') # Turns out this is the only required field. I require PDB minimum
        group_idx = fl.index('_atom_site.group_PDB')
        atom_name_idx = fl.index('_atom_site.auth_atom_id')
        x_idx = fl.index('_atom_site.Cartn_x')
        y_idx = fl.index('_atom_site.Cartn_y')
        z_idx = fl.index('_atom_site.Cartn_z')
        occ_idx = fl.index('_atom_site.occupancy')
        b_f_idx = fl.index('_atom_site.B_iso_or_equiv')
        res_name_idx = fl.index('_atom_site.auth_comp_id')
        res_num_idx = fl.index('_atom_site.auth_seq_id')
    except ValueError:
        return None
    try:
        i_code_idx = fl.index('_atom_site.pdbx_PDB_ins_code')
    except ValueError:
        i_code_idx = None
    try:
        model_idx = fl.index('_atom_site.pdbx_PDB_model_num')
    except ValueError:
        model_idx = None
    try:
        chain_id_idx = fl.index('_atom_site.auth_asym_id')
    except ValueError:
        chain_id_idx = None
    try:
        alt_loc_idx = fl.index('_atom_site.label_alt_id')
    except ValueError:
        alt_loc_idx = None
    try:
        element_idx = fl.index('_atom_site.type_symbol')
    except ValueError:
        element_idx = None
    try:
        charge_idx = fl.index('_atom_site.pdbx_formal_charge')
    except ValueError:
        charge_idx = None

    structure = Structure(name)
    models: Dict[int, Model] = {}
    chains: Dict[str, Chain] = {}
    residues: Dict[str, Residue] = {}
    current_model = Model(1)
    current_chain = Chain('A')

    if model_idx is None:
        structure.add_model(current_model)
    if charge_idx is None:
        current_model.add_chain(current_chain)

    for field in _atom_site.data_fields:
        atom = Atom(serial=field[id_idx],
             name=field[atom_name_idx],
             coord=(float(field[x_idx]), float(field[y_idx]), float(field[z_idx])),
             occupancy=float(field[occ_idx]),
             b_factor=float(field[b_f_idx]),
             altloc=field[alt_loc_idx] if alt_loc_idx is not None else None,
             element=field[element_idx] if element_idx is not None else None,
             charge=field[charge_idx] if charge_idx is not None else None,
             is_het=field[group_idx].startswith('HETATM'))
        res_id = field[res_num_idx]
        res_name = field[res_name_idx]
        i_code = field[i_code_idx] if i_code_idx is not None else None
        chain_id = field[chain_id_idx] if chain_id_idx is not None else 'A'
        model_id = field[model_idx] if chain_id_idx is not None else 1
        if model_id not in models:
            models[model_id] = Model(model_id)
            structure.add_model(models[model_id])
        current_model = models[model_id]
        if chain_id not in current_model.chains:
            chains[chain_id] = Chain(id=chain_id)
            current_model.add_chain(chains[chain_id])
        current_chain = models[model_id].get_chain(chain_id)
        if res_id not in current_chain.residues:
            residues[res_id] = Residue(res_name, res_id, i_code)
            chains[chain_id].add_residue(residues[res_id])
        residues[res_id].add_atom(atom) # Atoms should be guaranteed to have different _atom_site.id values
    return structure



def _parse_mmcif(text:str):
    loops = catagorize_mmcif_sections(text)
    loops = evaluate_fields(loops)
    try:
        structure_name = text[len('_data'):text.find('\n')].strip()
        structure = _build_mmcif_structure(structure_name, loops['_atom_site'])
        return structure
    except ZeroDivisionError:
        return None