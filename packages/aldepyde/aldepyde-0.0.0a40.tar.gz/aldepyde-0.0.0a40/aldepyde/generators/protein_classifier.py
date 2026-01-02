from .polymer_classifier import PolymerClassifier

class ProteinClassifier(PolymerClassifier):
    DEFAULT_ALPHABET = set("ACDEFGHIKLMNPQRSTVWY")
    DEFAULT_CLASSES = classes = {
                "positive" : set("RHK"),
                "negative" : set("ED"),
                "polar" : set("NSCTQ"),
                "nonpolar" : set("MALIVGP"),
                "aromatic" : set("FYW"),
                "_other" : set("")
            }
    DEFAULT_FLAGS = {
                "handle_non_canonical" : True
            }

    #TODO Current conflict exists between custom classes and flags
    #What do you do if you create a custom class and want to generate with it?
    #What if a flag combines classes, or enables behavior such as handle_non_canonical?

    def __init__(self, alphabet: str | list | set = None, classes:dict = None, flags:dict|None = None):
        if alphabet is None:
            alphabet = self.DEFAULT_ALPHABET
        if classes is None:
            classes = self.DEFAULT_CLASSES
        if flags is None:
            flags = self.DEFAULT_FLAGS
        super().__init__(alphabet, classes, flags)

    def default_alphabet(self):
        self.alphabet = self.DEFAULT_ALPHABET

    def default_classes(self):
        self.classes = self.DEFAULT_CLASSES

    def default_flags(self):
        self.flags = self.DEFAULT_FLAGS


