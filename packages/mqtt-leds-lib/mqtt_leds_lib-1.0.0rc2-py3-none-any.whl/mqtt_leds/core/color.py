from dataclasses import dataclass

@dataclass
class Color:
    r: int
    g: int
    b: int

    def as_tuple(self):
        return (self.r, self.g, self.b)
