import yaml
import aiohttp
from pathlib import Path

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image

from utils import get_context, TextEngine, GraiaAdapter

WEAP_PATH = Path.cwd() / "data" / "genshin" / "weapons"
WEAPON_INFO_PATH = Path.cwd() / "data" / "genshin" / "weapon_info.yaml"
mys_weap_url = "https://bbs.mihoyo.com/ys/obc/channel/map/189/5?bbs_presentation_style=no_header"
paimon_weap_url = "https://static.cherishmoon.fun/LittlePaimon/WeaponMaps/{}.jpg"

weap_data = {}
alias_dic = {}
ID2name_dic = {}


def load_weap_yaml():
    global weap_data
    if WEAPON_INFO_PATH.exists():
        with WEAPON_INFO_PATH.open("r", encoding="utf-8") as infor:
            weap_data = yaml.load(infor.read(), Loader=yaml.FullLoader)
    update_weap_dic()


def save_weap_yaml():
    with WEAPON_INFO_PATH.open("w", encoding="utf-8") as infow:
        yaml.dump(weap_data, infow, allow_unicode=True, Dumper=yaml.SafeDumper)


# 判断是否在alias字典中，或是否为武器正名的一部分
def is_weap(name: str) -> bool:
    if name in alias_dic:
        return True
    for weap in weap_data:
        if name in weap:
            alias_dic[name] = weap_data[weap]["ID"]  # 缓存至alias字典中
            return True
    return False


# 更新alias、ID2name字典信息
def update_weap_dic():
    global alias_dic, ID2name_dic
    alias_dic = {}
    ID2name_dic = {}
    for weap in weap_data:
        for alias in weap_data[weap]['alias']:
            alias_dic[alias] = weap_data[weap]['ID']
        ID2name_dic[weap_data[weap]['ID']] = weap


# 更新武器列表信息
async def update_weap_list():
    WEAP_PATH.mkdir(parents=True, exist_ok=True)

    context = await get_context(headless=False)
    page = await context.new_page()

    await page.goto(mys_weap_url)
    all_weap = await page.locator("text=猎弓 无锋剑").text_content()
    all_weap = all_weap.split(" ")[1:]
    await context.close()

    for weap in all_weap:
        if weap not in weap_data:
            weap_data[weap] = {}
            weap_data[weap]['alias'] = [weap]
            weap_data[weap]['ID'] = len(weap_data) - 1
    update_weap_dic()
    save_weap_yaml()


# 获得武器列表(MessageChain)
def get_weap_list() -> MessageChain:
    content = "当前武器列表如下："

    weap_list = sorted(list(weap_data.keys()))
    for idx, key in enumerate(weap_list):
        if idx % 5 == 0:
            content += f"\n    {str(key)}"
        else:
            content += f"、{str(key)}"
    return MessageChain(Image(
        data_bytes=TextEngine([GraiaAdapter(MessageChain(content))]).draw()
    ))


# 查询角色信息
async def query_weap_info(weapon_name: str) -> MessageChain:
    if weapon_name not in alias_dic:
        return MessageChain("查询不到该角色的攻略哦~\n可发送 '原神角色列表' 查询所有角色姓名")
    img_path = WEAP_PATH.joinpath(str(alias_dic[weapon_name]) + ".png")
    if img_path.exists():
        return MessageChain(Image(path=img_path))
    else:  # 不存在则网上更新并缓存
        weapon_name = ID2name_dic[alias_dic[weapon_name]]

        async with aiohttp.ClientSession() as session:
            async with session.get(paimon_weap_url.format(weapon_name)) as resp:
                data_bytes = await resp.read()

        # context = await get_context(headless=False)
        #
        # page = await context.new_page()
        # await page.goto(mys_weap_url)
        # async with page.expect_popup() as popup_info:
        #     await page.locator(f"a:has-text(\"{weapon_name}\")").click()
        #     page1 = await popup_info.value
        #     bytes_whole = await page1.locator(".obc-tmpl > div:nth-child(3)").screenshot()
        #     await context.close()

        with open(img_path, "wb") as f:
            f.write(data_bytes)

        return MessageChain(Image(path=img_path))
