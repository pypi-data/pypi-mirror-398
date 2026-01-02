from abc import ABC, abstractmethod
from .polymer_classifier import PolymerClassifier
import random

class ResidueGenerator(ABC):
    def __init__(self, classifier:PolymerClassifier):
        self.classifier = classifier

    def _generate(self):
        pass

    # Just pure, random generation. Nothing fancy
    def random(self, length, n=1) -> list:
        alphabet = list(self.classifier.alphabet)
        sequences = []
        for i in range(n):
            sequences.append("".join(random.choices(alphabet, k=length)))
        return sequences