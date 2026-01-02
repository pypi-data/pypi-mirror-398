# Configurable parent class
from abc import ABC, abstractmethod

class Configurable(ABC):
    @abstractmethod
    def UpdateSettings(self):
        """Update all settings upon loading or updating a _config"""