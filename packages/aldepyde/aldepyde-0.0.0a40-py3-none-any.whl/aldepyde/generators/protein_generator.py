from .residue_generator import ResidueGenerator
from .protein_classifier import ProteinClassifier

class ProteinGenerator(ResidueGenerator):
    def __init__(self, classifier:ProteinClassifier|None = None):
        if classifier is None:
            super().__init__(ProteinClassifier())
        else:
            super().__init__(classifier)

    def get_classifier(self):
        return self.classifier

    def generate(self,
                 length:int, mode:str='build', batch_size:int=1):
        pass

