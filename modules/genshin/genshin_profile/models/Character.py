import math
from typing import Dict, Union
from enkanetwork import CharacterInfo, StatsPercentage

from .Weapon import Weapon
from .Artifact import ArtifactSets
from .meta import AttrWeights

elementMap = {
    "Wind": "anemo",
    "Ice": "cryo",
    "Grass": "dendro",
    "Electric": "electro",
    "Rock": "geo",
    "Water": "hydro",
    "Fire": "pyro"
}


class Character:
    name: str
    element: str
    level: int
    cons: int
    talent: Dict[str, Dict[str, Union[int, bool]]]

    BaseHp: float
    ExtraHp: float
    BaseAtk: float
    ExtraAtk: float
    BaseDef: float
    ExtraDef: float
    Mastery: float
    Cpct: str
    Cdmg: str
    Recharge: str
    Dmg: str

    weap: Weapon
    artis: ArtifactSets

    attrWeight: Dict[str, float]

    def __init__(self, charInfo: CharacterInfo):
        self.name = charInfo.name
        self.element = elementMap[charInfo.element] if charInfo.element in elementMap else ""
        self.level = charInfo.level
        self.cons = charInfo.constellations_unlocked

        self.talent = {}
        talentMap = ['a', 'e', 'q']
        for idx, skill in enumerate(charInfo.skills):
            crown: bool = False
            if self.name == "达达利亚" and idx == 0 and skill.level >= 11:
                crown = True
            else:
                crown = skill.level >= 13 if skill.is_boosted else skill.level >= 10

            self.talent[talentMap[idx]] = {
                'level': skill.level,
                'plus': skill.is_boosted,
                "crown": crown
            }

        stats = charInfo.stats
        self.BaseHp = stats.BASE_HP.to_rounded()
        self.ExtraHp = math.ceil(stats.BASE_HP.value * stats.FIGHT_PROP_HP_PERCENT.value + stats.FIGHT_PROP_HP.value)
        self.BaseAtk = stats.FIGHT_PROP_BASE_ATTACK.to_rounded()
        self.ExtraAtk = math.ceil(
            stats.FIGHT_PROP_BASE_ATTACK.value * stats.FIGHT_PROP_ATTACK_PERCENT.value + stats.FIGHT_PROP_ATTACK.value)
        self.BaseDef = stats.FIGHT_PROP_BASE_DEFENSE.to_rounded()
        self.ExtraDef = math.ceil(
            stats.FIGHT_PROP_BASE_DEFENSE.value * stats.FIGHT_PROP_DEFENSE_PERCENT.value + stats.FIGHT_PROP_DEFENSE.value)
        self.Mastery = stats.FIGHT_PROP_ELEMENT_MASTERY.to_rounded()
        self.Cpct = stats.FIGHT_PROP_CRITICAL.to_percentage_symbol()
        self.Cdmg = stats.FIGHT_PROP_CRITICAL_HURT.to_percentage_symbol()
        self.Recharge = stats.FIGHT_PROP_CHARGE_EFFICIENCY.to_percentage_symbol()
        try:
            attr: StatsPercentage = getattr(stats, f"FIGHT_PROP_{charInfo.element.upper()}_ADD_HURT")
            self.Dmg = attr.to_percentage_symbol()
        except AttributeError:
            self.Dmg = "0.0%"

        self.weap = Weapon(charInfo.equipments[-1])
        self.artis = ArtifactSets(charInfo.equipments[:-1])

        if self.name in AttrWeights:
            self.attrWeight = AttrWeights[self.name]
        else:
            self.attrWeight = {"大攻击": 75, "小攻击": 75, "暴击率": 100, "暴击伤害": 100, "充能效率": 55}

        for artifact in self.artis.artis:
            artifact.calc_mark(self.attrWeight)
        self.artis.calc_mark()
