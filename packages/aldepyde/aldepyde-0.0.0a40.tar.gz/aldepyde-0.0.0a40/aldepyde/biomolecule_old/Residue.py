from abc import ABC, abstractmethod

class Residue(ABC):

    def __init__(self):
        self.atoms = None
        self.resID = None
        self.resName = None

