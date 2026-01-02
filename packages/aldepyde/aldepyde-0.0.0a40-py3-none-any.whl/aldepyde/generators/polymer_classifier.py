from abc import ABC, abstractmethod
from typing import ClassVar, Set
import sys

# Define monomer classes and alphabets
class PolymerClassifier(ABC):
    def __init__(self, alphabet:str|list|set, classes:dict, flags:dict|None = None):
        self.alphabet: ClassVar[set[str]] = alphabet if isinstance(alphabet, set) else set(alphabet)
        self.classes = classes
        self.flags = flags

    def is_valid(self, residue:str) -> bool:
        return residue in self.alphabet

    def in_class(self, residue:str, class_name:str) -> bool:
        return residue in self.classes[class_name]

    def in_classes(self, residue:str) -> list:
        inside = list()
        for key in self.classes.keys():
            if residue in self.classes[key]:
                inside.append(key)
        return inside

    def get_classes(self) -> list:
        return list(self.classes.keys())

    def get_alphabet(self) -> set:
        return self.alphabet

    def load_alphabet(self, alphabet:str|list):
        self.alphabet = alphabet if isinstance(alphabet, list) else list(alphabet)

    def load_classes(self, classes:dict):
        self.classes = classes

    def get_class_members(self, class_name):
        return self.classes[class_name]

    def append_class(self, class_name:str, members:set|str):
        if isinstance(members, str):
            self.alphabet |= set(members)
            self.classes[class_name] |= set(members)
        else:
            self.alphabet |= members
            self.classes[class_name] |= members


    def add_class(self, class_name:str, members=None):
        if members is None:
            members = set("")
        if isinstance(members, str):
            members = set(members)
        if class_name not in self.classes.keys():
            self.classes[class_name] = set()
        self.append_class(class_name, members)

    def remove_class(self, class_name:str, clean_alphabet=False):
        members = self.classes[class_name]
        if self.classes.pop(class_name, None) is None:
            sys.stderr.write(f"Tried to remove class '{class_name},' which does not exist\n")
        else:
            if clean_alphabet:
                self.clean_alphabet(members)

    def clean_alphabet(self, members:set):
        orphans = set()
        for member in members:
            for cls in self.classes.keys():
                if member in self.classes[cls]:
                    break
            else:
                orphans.add(member)
        self.remove_from_alphabet(orphans)

    def remove_from_alphabet(self, members:set):
        self.alphabet -= members
        for key in self.classes.keys():
            self.classes[key] -= members

    @abstractmethod
    def default_alphabet(self):
        pass

    @abstractmethod
    def default_classes(self):
        pass

    @abstractmethod
    def default_flags(self):
        pass

    def reset_defaults(self):
        self.default_classes()
        self.default_alphabet()
