import os
import json
import random
from pathlib import Path
from math import sqrt, pow
from typing import Tuple, List

from utils.image_util import BuildImage

IMAGE_PATH = TEXT_PATH = Path.cwd() / "data"
icon_path = IMAGE_PATH / "genshin" / "genshin_icon"
map_path = IMAGE_PATH / "genshin" / "map" / "map.png"
resource_label_file = Path(TEXT_PATH) / "genshin" / "resource_label_file.json"
resource_point_file = Path(TEXT_PATH) / "genshin" / "resource_point_file.json"


class Map:
    """
    原神资源生成类
    """

    def __init__(
            self,
            resource_name: str,
            center_point: Tuple[int, int],
            deviation: Tuple[int, int] = (25, 51),
            padding: int = 100,
            planning_route: bool = False,
            ratio: float = 1,
    ):
        """
        参数：
            :param resource_name: 资源名称
            :param center_point: 中心点
            :param deviation: 坐标误差
            :param padding: 截图外边距
            :param planning_route: 是否规划最佳线路
            :param ratio: 压缩比率
        """
        self.map = BuildImage(0, 0, background=map_path)
        self.resource_name = resource_name
        self.center_x = center_point[0]
        self.center_y = center_point[1]
        self.deviation = deviation
        self.padding = int(padding * ratio)
        self.planning_route = planning_route
        self.ratio = ratio

        self.deviation = (
            int(self.deviation[0] * ratio),
            int(self.deviation[1] * ratio),
        )

        # 资源、传送锚点、秘境、神像 id
        data = json.load(open(resource_label_file, "r", encoding="utf8"))
        print(resource_name)
        for x in data:
            if x != "CENTER_POINT":
                if data[x]["name"] == resource_name:
                    self.resource_id = data[x]["id"]
                elif data[x]["name"] == "传送锚点":
                    self.teleport_anchor_id = data[x]["id"]
                elif data[x]["name"] == "秘境":
                    self.mystery_realm_id = data[x]["id"]
                elif data[x]["name"] == "七天神像":
                    self.teleport_god_id = data[x]["id"]

        print("resource_id", self.resource_id)
        print("teleport_anchor_id", self.teleport_anchor_id)
        print("mystery_realm_id", self.mystery_realm_id)
        print("teleport_god_id", self.teleport_god_id)

        # 资源、传送锚点、秘境、神像 坐标
        data = json.load(open(resource_point_file, "r", encoding="utf8"))
        self.resource_point = []
        self.teleport_anchor_point = []
        self.mystery_realm_point = []
        self.teleport_god_point = []
        cnt = 0
        for x in data:
            if x != "CENTER_POINT" and data[x]["label_id"] in [self.resource_id, self.teleport_anchor_id,
                                                               self.mystery_realm_id, self.teleport_god_id]:
                Resource = Resources(
                    int((self.center_x + data[x]["x_pos"]) * ratio),
                    int((self.center_y + data[x]["y_pos"]) * ratio),
                )
                if data[x]["label_id"] == self.resource_id:
                    cnt += 1
                    self.resource_point.append(Resource)
                elif data[x]["label_id"] == self.teleport_anchor_id:
                    self.teleport_anchor_point.append(Resource)
                elif data[x]["label_id"] == self.mystery_realm_id:
                    self.mystery_realm_point.append(Resource)
                else:
                    self.teleport_god_point.append(Resource)
        print("cnt = ", cnt)
        print("len(resource_point) = ", self.get_resource_count())

    # 将地图上生成资源图标
    def generate_resource_icon_in_map(self) -> int:
        x_list = [x.x for x in self.resource_point]
        y_list = [x.y for x in self.resource_point]
        min_width = min(x_list) - self.padding
        max_width = max(x_list) + self.padding
        min_height = min(y_list) - self.padding
        max_height = max(y_list) + self.padding
        self._generate_transfer_icon((min_width, min_height, max_width, max_height))
        for res in self.resource_point:
            icon = self._get_icon_image(self.resource_id)
            self.map.paste(
                icon, (res.x - self.deviation[0], res.y - self.deviation[1]), True
            )
        if self.planning_route:
            self._generate_best_route()
        self.map.crop((min_width, min_height, max_width, max_height))
        rand = random.randint(1, 10000)
        if not (IMAGE_PATH / "genshin" / "temp").exists():
            os.mkdir(str(IMAGE_PATH / "genshin" / "temp"))
        self.map.save(IMAGE_PATH / "genshin" / "temp" / f"genshin_map_{rand}.png")
        return rand

    # 资源数量
    def get_resource_count(self) -> int:
        return len(self.resource_point)

    # 生成传送锚点、秘境和神像
    def _generate_transfer_icon(self, box: Tuple[int, int, int, int]):
        min_width, min_height, max_width, max_height = box
        for resources in [self.teleport_anchor_point, self.mystery_realm_point, self.teleport_god_point]:
            if resources == self.teleport_anchor_point:
                id_ = self.teleport_anchor_id
            elif resources == self.mystery_realm_point:
                id_ = self.mystery_realm_id
            else:
                id_ = self.teleport_god_id
            for res in resources:
                if min_width < res.x < max_width and min_height < res.y < max_height:
                    icon = self._get_icon_image(id_)
                    self.map.paste(
                        icon,
                        (res.x - self.deviation[0], res.y - self.deviation[1]),
                        True,
                    )

    # 生成最优路线（说是最优其实就是直线最短）
    def _generate_best_route(self):
        teleport_list = self.teleport_anchor_point + self.mystery_realm_point + self.teleport_god_point
        for teleport in teleport_list:
            current_res, res_min_distance = teleport.get_resource_distance(self.resource_point)
            current_teleport, teleport_min_distance = current_res.get_resource_distance(teleport_list)
            if current_teleport == teleport:
                self.map.line(
                    (current_teleport.x, current_teleport.y, current_res.x, current_res.y), (255, 0, 0), width=1
                )
        is_used_res_points = []
        for res in self.resource_point:
            if res in is_used_res_points:
                continue
            current_teleport, teleport_min_distance = res.get_resource_distance(teleport_list)
            current_res, res_min_distance = res.get_resource_distance(self.resource_point)
            if teleport_min_distance < res_min_distance:
                self.map.line(
                    (current_teleport.x, current_teleport.y, res.x, res.y), (255, 0, 0), width=1
                )
            else:
                is_used_res_points.append(current_res)
                self.map.line(
                    (current_res.x, current_res.y, res.x, res.y), (255, 0, 0), width=1
                )
                res_cp = self.resource_point[:]
                res_cp.remove(current_res)
                # for _ in res_cp:
                current_teleport_, teleport_min_distance = res.get_resource_distance(teleport_list)
                current_res, res_min_distance = res.get_resource_distance(res_cp)
                if teleport_min_distance < res_min_distance:
                    self.map.line(
                        (current_teleport.x, current_teleport.y, res.x, res.y), (255, 0, 0), width=1
                    )
                else:
                    self.map.line(
                        (current_res.x, current_res.y, res.x, res.y), (255, 0, 0), width=1
                    )
                    is_used_res_points.append(current_res)
            is_used_res_points.append(res)

    # 获取资源图标
    def _get_icon_image(self, id_: int) -> "BuildImage":
        icon = icon_path / f"{id_}.png"
        if icon.exists():
            return BuildImage(
                int(50 * self.ratio), int(50 * self.ratio), background=icon
            )
        return BuildImage(
            int(50 * self.ratio),
            int(50 * self.ratio),
            background=f"{icon_path}/box.png",
        )

    # def _get_shortest_path(self, res: 'Resources', res_2: 'Resources'):


# 资源类
class Resources:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def get_distance(self, x: int, y: int):
        return int(sqrt(pow(abs(self.x - x), 2) + pow(abs(self.y - y), 2)))

    # 拿到资源在该列表中的最短路径
    def get_resource_distance(self, resources: List["Resources"]) -> "Resources, int":
        current_res = None
        min_distance = 999999
        for res in resources:
            distance = self.get_distance(res.x, res.y)
            if distance < min_distance and res != self:
                current_res = res
                min_distance = distance
        return current_res, min_distance
