import ast
import time
from math import ceil
from io import BytesIO
from pathlib import Path
from typing import Union
from loguru import logger
from PIL import Image as IMG
from datetime import datetime, timedelta

from graia.ariadne.entry import *
from graia.saya import Channel

from utils import Permission, BuildImage, safe_send_message

channel = Channel.current()

IMAGE_PATH = Path.cwd() / "data" / "genshin" / "material"


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage, TempMessage],
        inline_dispatchers=[Twilight(
            FullMatch("/"),
            FullMatch("原神", optional=True),
            UnionMatch("今日", "每日"),
            FullMatch("素材")
        )]
    )
)
async def genshin_material_remind(
        app: Ariadne,
        evt: Union[GroupMessage, FriendMessage, TempMessage],
        source: Source
):
    if not Permission(evt).get(channel.module):
        return

    file_name = str((datetime.now() - timedelta(hours=4)).date())
    try:
        if not (Path(IMAGE_PATH) / f"{file_name}.png").exists():
            await safe_send_message(app, evt, MessageChain("正在自动更新中..."))
            _ = await update_image()
        await safe_send_message(
            app, evt,
            MessageChain(Image(path=IMAGE_PATH.joinpath(f"{file_name}.png"))),
            quote=source
        )
    except Exception as e:
        logger.error(e)
        await safe_send_message(app, evt, MessageChain(f"出现错误:\n{str(e)}"), quote=source)


@channel.use(SchedulerSchema(crontabify("0 4 * * *")))
async def update_daily_material(app: Ariadne):
    group_id = 463759403
    try:
        _ = await update_image()
        await app.send_group_message(group_id, MessageChain("原神今日素材已更新！"))
    except Exception as e:
        logger.error(e)
        await app.send_group_message(group_id, MessageChain(str(e)))


url = "https://api-static.mihoyo.com/common/blackboard/ys_obc/v1/get_activity_calendar?app_sn=ys_obc"
color = (253, 245, 230)  # 淡黄色
_size = (100, 140)  # 图像大小
w0 = 55  # 边框距离
w_gap = 25  # 图像间距
w_n = 7  # 一行多少图标


async def update_image():
    logger.info("开始更新每日素材...")
    for f in IMAGE_PATH.iterdir():
        if f.is_file():
            f.unlink()

    char_list = []
    weap_list = []

    session = Ariadne.service.client_session
    async with session.get(url) as resp:
        resp = await resp.json()
    sort_day = time.strftime("%w")
    day = str(int(sort_day) + 7) if sort_day == "0" else sort_day
    for v in resp["data"]["list"]:
        if day in v["drop_day"]:
            v["sort"] = ast.literal_eval(v["sort"])
            char_list.append(v) if v["break_type"] == "2" else weap_list.append(v)
    char_list.sort(key=lambda x: x["sort"][sort_day])
    weap_list.sort(key=lambda x: x["sort"][sort_day])

    W = _size[0] * w_n + w_gap * (w_n - 1) + w0 * 2  # 整张图的宽
    H = int(ceil(len(char_list) / w_n) + ceil(len(weap_list) / w_n)) * _size[1] + 3 * _size[1]  # 整张图的高

    bg = BuildImage(W, H, color=color)
    title1 = BuildImage(W, int(_size[1] * 1.5), font_size=75, is_alpha=True)
    title1.text((0, 0), text="今日角色天赋", center_type="center")
    bg.paste(title1, (0, 0), alpha=True)

    cw = w0
    ch = title1.size[1]
    for char in char_list:
        img = await make_icon(char["img_url"], char["title"])
        await bg.apaste(img, (cw, ch), alpha=True)
        cw = cw + _size[0] + w_gap
        if W - cw <= _size[0]:
            cw = w0
            ch += _size[1]

    title2 = BuildImage(W, int(_size[1] * 1.5), font_size=75, is_alpha=True)
    title2.text((0, 0), text="今日武器突破", center_type="center")
    bg.paste(title2, (0, ch := ch + _size[1]), alpha=True)

    cw = w0
    ch = ch + title2.size[1]
    for char in weap_list:
        img = await make_icon(char["img_url"], char["title"])
        await bg.apaste(img, (cw, ch), alpha=True)
        cw = cw + _size[0] + w_gap
        if W - cw <= _size[0]:
            cw = w0
            ch += _size[1]

    file_name = str((datetime.now() - timedelta(hours=4)).date())
    await bg.asave(IMAGE_PATH.joinpath(f"{file_name}.png"))
    logger.success("更新每日素材成功！")


# 制作 图像+名字 的图标
async def make_icon(img_url: str, name: str) -> BuildImage:
    session = Ariadne.service.client_session
    async with session.get(img_url) as resp:
        resp = await resp.read()
    img_obj = IMG.open(BytesIO(resp))
    img_obj = img_obj.resize((_size[0], _size[0]))
    font_size = _size[0] // 4 if len(name) <= 4 else _size[0] // len(name)
    img_name = BuildImage(_size[0], _size[1] - _size[0], font_size=font_size, is_alpha=True)
    await img_name.atext((0, 0), text=name, center_type="center")
    img = BuildImage(_size[0], _size[1], is_alpha=True)
    await img.apaste(img_obj, (0, 0), alpha=True), await img.apaste(img_name, (0, _size[0]), alpha=True)
    return img
