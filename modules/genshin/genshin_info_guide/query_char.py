import yaml
import base64
from io import BytesIO
from pathlib import Path
from loguru import logger
from PIL import Image as IMG

from graia.ariadne import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image

from utils import get_context, GraiaAdapter, TextEngine
from utils.TXSDK_util import TXSDK

CHAR_PATH = Path.cwd() / "data" / "genshin" / "characters"
CHARACTER_INFO_PATH = Path.cwd() / "data" / "genshin" / "character_info.yaml"
guide_path = CHAR_PATH / "guide"
info_path = CHAR_PATH / "info"
char_url = "https://bbs.mihoyo.com/ys/obc/channel/map/189/25?bbs_presentation_style=no_header"
info_url = "https://bbs-api.mihoyo.com/post/wapi/getPostFullInCollection?gids=2&order_type=2&collection_id=428421"
guide_ori_url = "https://bbs-api.mihoyo.com/post/wapi/getPostFullInCollection?gids=2&order_type=1&collection_id=642956"
guide_url = "https://bbs-api.mihoyo.com/post/wapi/getPostFullInCollection?&gids=2&order_type=2&collection_id=1180811"

char_data = {}
alias_dic = {}
ID2name_dic = {}


def load_char_yaml():
    global char_data
    with CHARACTER_INFO_PATH.open("r", encoding="utf-8") as infor:
        char_data = yaml.load(infor.read(), Loader=yaml.FullLoader)
    update_char_dic()


def save_char_yaml():
    with CHARACTER_INFO_PATH.open("w", encoding="utf-8") as infow:
        yaml.dump(char_data, infow, allow_unicode=True, Dumper=yaml.SafeDumper)


# 给其它模块提供查询角色信息的接口
def get_char_data():
    return char_data


if not CHARACTER_INFO_PATH.exists():
    save_char_yaml()


# 判断是否在alias字典中
def is_char(name: str) -> bool:
    if name in alias_dic:
        return True
    return False


# 更新alias、ID2name字典信息
def update_char_dic():
    global alias_dic, ID2name_dic
    alias_dic = {}
    ID2name_dic = {}
    for character in char_data:
        for alias in char_data[character]['alias']:
            alias_dic[alias] = char_data[character]['ID']
        ID2name_dic[char_data[character]['ID']] = character


# 更新角色列表信息
async def update_char_list():
    context = await get_context(headless=False)
    page = await context.new_page()

    await page.goto(char_url)
    all_char = await page.locator("text=坎蒂丝 赛诺").text_content()
    all_char = all_char.split(" ")[1:]
    await context.close()

    for char in all_char:
        if char not in char_data:
            char_data[char] = {}
            char_data[char]['alias'] = [char]
            char_data[char]['ID'] = len(char_data) - 1
    update_char_dic()
    save_char_yaml()


# 获得角色列表(MessageChain)
def get_char_list() -> MessageChain:
    content = "当前角色列表如下：\n"
    for key in char_data:
        content += f"    {key}\n"
    return MessageChain(Image(
        data_bytes=TextEngine([GraiaAdapter(MessageChain(content))]).draw()
    ))


# 查询角色攻略
async def query_char_guide(character_name: str) -> MessageChain:
    if character_name not in alias_dic:
        return MessageChain("查询不到该角色的攻略哦~\n可发送 '原神角色列表' 查询所有角色姓名")
    img_path = guide_path.joinpath(str(alias_dic[character_name]) + ".png")
    if img_path.exists():
        return MessageChain(Image(path=img_path))
    else:
        character_name = ID2name_dic[alias_dic[character_name]]
        if "旅行者·" in character_name:
            character_name = character_name[-1] + "主"

        session = Ariadne.service.client_session
        async with session.get(guide_url) as resp:
            resp = await resp.json()

        if not resp or resp["retcode"] != 0:
            logger.error(resp)
            raise ValueError(resp["message"])

        img_url = None
        for val in resp["data"]["posts"]:
            if character_name in val["post"]["subject"]:
                MAX = 0
                for i, v in enumerate(val["image_list"]):
                    if int(v["size"]) >= int(val["image_list"][MAX]["size"]):
                        MAX = i
                img_url = val["image_list"][MAX]["url"]
                break
        if img_url:
            async with session.get(img_url) as img_resp:
                bytes_img = await img_resp.read()
            with open(img_path, "wb") as f:
                f.write(bytes_img)
            return MessageChain(Image(data_bytes=bytes_img))
        else:
            return MessageChain("本地和网站API里斗没有该角色的攻略哦~\n要等攻略up更新，或者collection_id需要更新啦。")


# 查询角色信息
async def query_char_info(character_name: str) -> MessageChain:
    if character_name not in alias_dic:
        return MessageChain("查询不到该角色的信息哦~\n可发送 '原神角色列表' 查询所有角色姓名")
    img_path = info_path.joinpath(str(alias_dic[character_name]) + ".png")
    if img_path.exists():
        return MessageChain(Image(path=img_path))
    else:  # 不存在则从API获取更新并缓存
        character_name = ID2name_dic[alias_dic[character_name]]

        session = Ariadne.service.client_session
        async with session.get(info_url) as resp:
            resp = await resp.json()

        if not resp or resp["retcode"] != 0:
            logger.error(resp)
            raise ValueError(resp["message"])

        special = ['雷电将军', '珊瑚宫心海', '菲谢尔', '托马', '八重神子', '九条裟罗', '辛焱', '神里绫华']
        img_url = None
        for val in resp["data"]["posts"]:
            if character_name in val["post"]["subject"]:
                img_url = val["image_list"][1]["url"] if character_name not in special else val["image_list"][2]["url"]
                break
        if img_url:
            async with session.get(img_url) as img_resp:
                bytes_img = await img_resp.read()
            with open(img_path, "wb") as f:
                f.write(bytes_img)
            return MessageChain(Image(data_bytes=bytes_img))
        else:
            return MessageChain("API查询不到该角色的信息哦~\n 可能要等up主来更新信息啦。")


# 重新绘制角色攻略
async def update_guide():
    if not guide_path.exists():
        guide_path.mkdir()
    else:
        for f in guide_path.iterdir():
            if f.is_file():
                f.unlink()

    ori_path = guide_path.joinpath("original")
    if not ori_path.exists():
        ori_path.mkdir()
    else:
        for f in ori_path.iterdir():
            if f.is_file():
                f.unlink()

    await get_original_img(ori_path)
    await crop_correspondence(ori_path)
    update_char_dic()
    logger.success("原神角色攻略更新成功！")


# 爬取攻略original图片
async def get_original_img(ori_path):
    session = Ariadne.service.client_session
    async with session.get(guide_ori_url) as resp:
        resp = await resp.json()

    if not resp or resp["retcode"] != 0:
        logger.error(resp)
        raise ValueError(resp["message"])

    latest = 0
    for i, v in enumerate(resp["data"]["posts"]):
        if int(resp["data"]["posts"][latest]["post"]["post_id"]) <= int(v["post"]["post_id"]):
            latest = i
    urls = resp["data"]["posts"][latest]["image_list"][2:-2]
    for i, url in enumerate(urls):
        async with session.get(url["url"]) as res:
            res = await res.read()
        with open(ori_path.joinpath(f"{i}.png"), "wb") as f:
            f.write(res)


# 图片切割并归类
async def crop_correspondence(ori_path: Path):
    logger.info("开始图片切割归类")

    SIZE = (2560, 1440)
    rect = (39, 1050, 585, 1210)

    for f in ori_path.iterdir():
        img = IMG.open(f)
        img_size = img.size
        cnt = round(img_size[1] / SIZE[1])
        w = img_size[0]
        h = img_size[1] // cnt

        for i in range(cnt):
            img_char = img.crop((0, i * h, w, (i + 1) * h)).resize(SIZE, IMG.Resampling.LANCZOS)  # 角色攻略图片
            img_name = img_char.crop(rect)  # 角色姓名

            # 姓名识别
            buffer = BytesIO()
            img_name.save(buffer, format="PNG")
            b64_str = base64.b64encode(buffer.getvalue()).decode()
            resp = await TXSDK.text_recognize.async_get_resp({"ImageBase64": b64_str})
            print(resp)
            if "error" in resp:
                raise ValueError(resp['error'])

            name = resp["TextDetections"][0]['DetectedText']
            if name in alias_dic:
                img_char.save(guide_path.joinpath(f"{str(alias_dic[name])}.png"))
            else:
                raise ValueError(f"不存在角色\"{name}\"，请检查角色姓名 或 更新角色列表！")

    logger.success("图片切割归类成功！")
