__all__ = ['Atom']

class Atom():
    def __init__(self,
                 record_name: str = None,
                 serial: str = None,
                 name: str = None,
                 altLoc: str = None,
                 resName: str = None,
                 chainID: str = None,
                 resSeq: str = None,
                 iCode: str = None,
                 x: str = None,
                 y: str = None,
                 z: str = None,
                 occupancy: str = None,
                 tempFactor: str = None,
                 element: str = None,
                 charge: str = None
        ):
        self.SetRecordName(record_name)
        self.SetSerial(serial)
        self.SetAltLoc(altLoc)
        self.SetResName(resName)
        self.SetChainID(chainID)
        self.SetResSeq(resSeq)
        self.SetiCode(iCode)
        self.SetXYZ(x, y, z)
        self.SetOccupancy(occupancy)
        self.SetTempFactor(tempFactor)
        self.SetElement(element)
        self.SetCharge(charge)
        self.SetName(name) # Do this last to extract the element

    def SetRecordName(self, record_name: str) -> None:
        self.record_name = record_name

    def SetSerial(self, serial: str | int | None) -> None:
        self.serial = int(serial)

    def SetName(self, name) -> None:
        # TODO Extrapolate the element from the name
        self.name = name

    def SetAltLoc(self, altLoc: str | None) -> None:
        self.altLoc = altLoc

    def SetResName(self, resName: str | None) -> None:
        self.resName = resName

    def SetChainID(self, chainID: str | None) -> None:
        self.chainID = chainID

    def SetResSeq(self, resSeq: str | None) -> None:
        self.resSeq = resSeq

    def SetiCode(self, iCode: str | None) -> None:
        self.iCode = iCode

    def SetXYZ(self, x: str | float | None, y: str | float | None, z: str | float | None) -> None:
        self.x = float(x) if x is not None else None
        self.y = float(y) if y is not None else None
        self.z = float(z) if z is not None else None

    def SetX(self, x: str | float | None):
        self.x = float(x) if x is not None else None

    def SetY(self, x: str | float | None):
        self.x = float(x) if x is not None else None

    def SetZ(self, x: str | float | None):
        self.x = float(x) if x is not None else None

    def SetOccupancy(self, occupancy: str | float | None) -> None:
        self.occupancy = float(occupancy) if occupancy is not None else None

    def SetTempFactor(self, tempFactor: str | float | None) -> None:
        self.tempFactor = float(tempFactor) if tempFactor is not None else None

    def SetElement(self, element: str | None) -> None:
        self.element = element

    def SetCharge(self, charge: str | None) -> None:
        self.charge = charge

    def Distance(self, other: 'Atom') -> float:
        return ((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)**(.5)

    # In case you want to treat aldepyde like that other importable module that shall not be named
    def __sub__(self, other):
        return self.Distance(other)

    def __str__(self):
        return f"{self.record_name} {self.serial} {self.resName}"

