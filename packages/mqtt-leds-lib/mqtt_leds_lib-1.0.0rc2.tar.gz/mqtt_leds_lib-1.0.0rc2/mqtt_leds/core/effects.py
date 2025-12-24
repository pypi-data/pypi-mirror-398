from abc import ABC, abstractmethod

class Effect(ABC):
    def __init__(self, strip):
        self.strip = strip

    @abstractmethod
    def step(self):
        pass