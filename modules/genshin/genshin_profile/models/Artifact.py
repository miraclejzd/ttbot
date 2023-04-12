import math
from typing import List, Union, Dict, NoReturn
from enkanetwork import Equipments, DigitType

from .meta import IdMap, AttrMap, CalcWeight


class Artifact:
    name: str
    set: str
    id: int
    level: int
    key: str
    value: str
    mark: float
    markClass: str
    attrs: List[Dict[str, Union[str, float]]]

    def __init__(self, arti: Equipments):
        self.name = arti.detail.name
        self.set = arti.detail.artifact_name_set
        self.id = IdMap[arti.detail.artifact_type]
        self.level = arti.level
        self.key = Artifact.get_attr_name(arti.detail.mainstats.name, arti.detail.mainstats.type)
        self.value = f"{arti.detail.mainstats.value}{'%' if arti.detail.mainstats.type == DigitType.PERCENT else ''}"

        self.attrs = []
        for substat in arti.detail.substats:
            subKey = Artifact.get_attr_name(substat.name, substat.type)
            subValue = substat.value
            subValueText = f"{substat.value}{'%' if substat.type == DigitType.PERCENT else ''}"
            upNum = Artifact.calc_inc_num(subKey, substat.value)
            self.attrs.append({
                'key': subKey,
                'value': subValue,
                'valueText': subValueText,
                'upNum': upNum
            })
        self.mark = 0
        self.markClass = "D"

    @staticmethod
    def get_attr_name(oriName: str, dType: DigitType) -> str:
        if oriName in ["生命值", "攻击力", "防御力"]:
            return ("大" if dType == DigitType.PERCENT else "小") + oriName[:2]
        elif oriName.find("伤害加成") != -1:
            return oriName[0] + "伤加成"
        elif oriName == "元素充能效率":
            return "充能效率"
        return oriName

    @staticmethod
    def calc_inc_num(subKey: str, subValue: float) -> float:
        if subKey not in AttrMap or subValue == 0:
            return 0

        cfg = AttrMap[subKey]
        if "maxValue" not in cfg or "minValue" not in cfg:
            return 0

        maxNum = min(5, math.floor(round(subValue / cfg["minValue"], 1) * 1))
        minNum = max(1, math.ceil(round(subValue / cfg["maxValue"], 1) * 1))

        if maxNum == minNum:
            return maxNum
        return round(subValue / (cfg["minValue"] + cfg["maxValue"]) * 2)

    def calc_mark(self, attrWeight: Dict[str, float]) -> NoReturn:
        self.mark = 0 if self.key not in ["暴击率", "暴击伤害"] else 20
        for attr in self.attrs:
            key = attr['key']
            if key in attrWeight:
                self.mark += attr['value'] * CalcWeight[key] * attrWeight[key] / 100
        self.mark = round(self.mark, 1)

        scoreMap = [["D", 10], ["C", 16.5], ["B", 23.1], ["A", 29.7], ["S", 36.3], ["SS", 42.9], ["SSS", 49.5],
                    ["ACE", 56.1], ["ACE²", 70]]
        for tar_mark in scoreMap:
            if self.mark < tar_mark[1]:
                self.markClass = tar_mark[0]
                break


class ArtifactSets:
    mark: float
    markClass: str
    artis: List[Artifact]
    set: Dict[str, int]  # 圣遗物套装

    def __init__(self, artisInfo: List[Equipments]):
        self.artis = []
        for artifact in artisInfo:
            self.artis.append(Artifact(artifact))

        self.set = {}
        for artifact in self.artis:
            if artifact.set not in self.set:
                self.set[artifact.set] = 1
            else:
                self.set[artifact.set] += 1

        self.mark = 0
        self.markClass = "D"

    def calc_mark(self):
        self.mark = 0
        for artifact in self.artis:
            self.mark += artifact.mark
        self.mark = round(self.mark, 1)

        scoreMap = [["D", 40], ["C", 66], ["B", 92.4], ["A", 118.8], ["S", 145.2], ["SS", 171.6], ["SSS", 200],
                    ["ACE", 224.4], ["ACE²", 300]]
        for tar_mark in scoreMap:
            if self.mark < tar_mark[1]:
                self.markClass = tar_mark[0]
                break
