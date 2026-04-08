from dataclasses import dataclass

@dataclass
class BiletLotniczy:
    pasażer: str
    kieruek: str
    cena: float
    czy_odprawiony: bool = False


nyc = BiletLotniczy("Damian", "New York", 1.200, False)

print(nyc)