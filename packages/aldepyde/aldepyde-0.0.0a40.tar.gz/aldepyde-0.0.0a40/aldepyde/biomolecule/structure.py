from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field


@dataclass
class Atom():
    serial: str
    name: str
    coord: Tuple[float, float, float]
    occupancy: float
    b_factor: float
    is_het: bool
    element: Optional[str]
    charge: Optional[str]
    altloc: Optional[str]


@dataclass
class Residue():
    name: str
    id: str
    ins_code: Optional[str]
    atoms: List[Atom] = field(default_factory=list)

    def add_atom(self, atom: Atom) -> None:
        self.atoms.append(atom)

@dataclass
class Chain():
    id: str
    residues: Dict[str, Residue] = field(default_factory=dict)

    def add_residue(self, residue: Residue):
        self.residues[residue.id] = residue
        # self.residues.append(residue)

    def get_residue(self, id):
        return self.residues[id]

@dataclass
class Model:
    id: str
    chains: Dict[str, Chain] = field(default_factory=dict)

    def add_chain(self, chain: Chain) -> None:
        self.chains[chain.id] = chain
        # self.chains.append(chain)

    def get_chain(self, id) -> Chain:
        return self.chains[id]

@dataclass
class Structure:
    id: str
    # title: str = ""
    models: Dict[str, Model] = field(default_factory=dict)

    def add_model(self, model: Model) -> None:
        self.models[model.id] = model
        # self.models.append(model)