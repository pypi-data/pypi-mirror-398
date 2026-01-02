from aldepyde.biomolecule_old._Atom import Atom as atom

__all__ = ['CreateAtom', 'CreateEnforced', 'CreateDummy']

def CreateAtom(  # General atom
        record_name: str| None = None,
        serial: str | int | None = None,
        name: str | None = None,
        altLoc: str | None = None,
        resName: str | None = None,
        chainID: str | None = None,
        resSeq: str | None = None,
        iCode: str | None = None,
        x: str | float | None = None,
        y: str | float |  None = None,
        z: str | float |  None = None,
        occupancy: str | float |  None = None,
        tempFactor: str | float |  None = None,
        element: str | None = None,
        charge: str | None = None
) -> atom:
    return atom(record_name=record_name, serial=serial, name=name, altLoc=altLoc, resName=resName,
                chainID=chainID, resSeq=resSeq, iCode=iCode, x=x, y=y, z=z,
                occupancy=occupancy, tempFactor=tempFactor, element=element,
                charge=charge)

def CreateEnforced( # The type of atom from the parsers. Enforce what's required by PDB standard
        serial: str,
        name: str,
        altLoc: str,
        resName: str,
        chainID: str,
        resSeq: str,
        iCode: str,
        x: str,
        y: str,
        z: str,
        occupancy: str,
        tempFactor: str,
        record_name: str = None,
        element: str | None = None,
        charge: str | None = None
) -> atom:
    return atom(serial=serial, name=name, altLoc=altLoc, resName=resName,
                chainID=chainID, resSeq=resSeq, iCode=iCode, x=x, y=y, z=z,
                occupancy=occupancy, tempFactor=tempFactor, element=element,
                charge=charge, record_name=record_name)


def CreateDummy( # As the name implies
        record_name: str| None = "HETATM",
        serial: str | int = "-1",
        name: str = "PS",
        altLoc: str = "",
        resName: str = "PSD",
        chainID: str = "$P",
        resSeq: str = "PSD",
        iCode: str = "",
        x: str | float = "0.0",
        y: str | float = "0.0",
        z: str | float = "0.0",
        occupancy: str | float = "0.0",
        tempFactor: str | float = "0.0",
        element: str | None = "PS",
        charge: str | None = None
) -> atom:
    return atom(record_name=record_name, serial=serial, name=name, altLoc=altLoc, resName=resName,
                chainID=chainID, resSeq=resSeq, iCode=iCode, x=x, y=y, z=z,
                occupancy=occupancy, tempFactor=tempFactor, element=element,
                charge=charge)

