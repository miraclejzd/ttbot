import asyncio
from typing import Union
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from graia.ariadne.entry import *
from graia.saya import Channel
from graia.ariadne.message.parser.twilight import ParamMatch
from enkanetwork import EnkaNetworkAPI, EnkaPlayerNotFound
from playwright.async_api import async_playwright

from utils import Permission, safe_send_message
from ..genshin_info_guide.query_char import get_char_name
from .models import Character

channel = Channel.current()

cwd_path = Path(__file__).parent


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage, TempMessage],
    inline_dispatchers=[Twilight(
        FullMatch("/练度"),
        RegexMatch(r"[1-9](\d{8})") @ "uid",
        "tar_char" @ ParamMatch()
    )],
    decorators=[Permission.require(channel.module)]
))
async def genshin_make_profile(
        app: Ariadne, evt: Union[GroupMessage, FriendMessage, TempMessage],
        uid: RegexResult, tar_char: RegexResult,
        source: Source
):
    uid = int(uid.result.display.strip())
    tar_char = tar_char.result.display.strip()

    print(f"uid: {uid},  tar_char: {tar_char}")

    result = await get_profile(uid, tar_char)
    await safe_send_message(app, evt, result, quote=source)


async def get_profile(uid: int, tar_char: str) -> MessageChain:
    char_name = get_char_name(tar_char)
    if char_name is None:
        return MessageChain(f"没有 {tar_char} 这个角色哦~")

    client = EnkaNetworkAPI(lang="chs")
    async with client:
        try:
            data = await client.fetch_user(uid)
        except EnkaPlayerNotFound:
            return MessageChain("没找到这个玩家，请检查UID是否有误！")
        except asyncio.TimeoutError:
            return MessageChain(f"连接超时，可能Enka网络正在维护服务器（大概需要5~8h）")
        except Exception as e:
            return MessageChain(f"出现错误：{str(e)}")

        if data.characters is None:
            return MessageChain("角色展示关闭了！请将角色展示打开并稍等1-2min再进行查询哦。")

        filter_list = list(filter(lambda char: char.name == char_name, data.characters))
        if len(filter_list) == 0:
            exist_char: str = "、".join(c.name for c in data.characters)
            return MessageChain(f"角色展柜里没有 {tar_char} 这个角色哦!\n当前展柜里的角色为：{exist_char}")

        char = Character(filter_list[0])
        env = Environment(loader=FileSystemLoader(cwd_path))
        temp = env.get_template("profile.html")
        params = {
            "uid": uid,
            "char": char,
            "talentMap": ["a", "e", "q"],
            "weapon": char.weap,
            "artisDetail": char.artis,
            "updateTime": datetime.now().strftime("%m.%d  %H:%M")
        }
        res = temp.render(**params)
        res_path = cwd_path.joinpath(f"res_{uid}_{char_name}.html")
        with open(res_path, "w", encoding='utf-8') as f:
            f.write(res)

        async with async_playwright() as ap:
            browser = await ap.chromium.launch()
            page = await browser.new_page()

            await page.goto(str(res_path))
            img_bytes = await page.locator("#container").screenshot(omit_background=True)
            await browser.close()

            res_path.unlink()

            return MessageChain(Image(data_bytes=img_bytes))
