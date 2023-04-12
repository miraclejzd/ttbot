from enkanetwork import Equipments


class Weapon:
    name: str
    star: int
    level: int
    affix: int

    def __init__(self, weapInfo: Equipments):
        self.name = weapInfo.detail.name
        self.star = weapInfo.detail.rarity
        self.level = weapInfo.level
        self.affix = weapInfo.refinement
