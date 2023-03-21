import random
from loguru import logger
from typing import Union, Dict

from graia.ariadne.entry import *
from graia.saya import Channel
from graia.ariadne.message.parser.twilight import ParamMatch

from utils import Permission, safe_send_message
from utils.BDCloud_util import BDC
from .filter import filtList, idList

channel = Channel.current()

channel.name("beautiful_pictures")
channel.author("miraclejzd")
channel.description("一个可以发送好看图片的插件，发送 '来张xx图片' 即可。")

URL = "https://api.obfs.dev"
pid_url = "https://pixiv.re/{}.jpg"


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage, TempMessage],
    inline_dispatchers=[
        Twilight([
            UnionMatch("来点", "来张"),
            RegexMatch(r"[^\s]+", optional=True) @ "keyword",
            UnionMatch("图片", "色图", "涩图", "瑟图"),
        ])
    ],
    decorators=[Permission.require(channel.module)]
))
async def keyword_pictures(
        app: Ariadne, keyword: RegexResult, source: Source,
        event: Union[GroupMessage, FriendMessage, TempMessage]
):
    if not keyword.matched:
        return await safe_send_message(app, event, await get_random_img(), quote=source)

    keyword = keyword.result.display
    res = await get_image_keyword(keyword)

    spare = None
    if res.has(Image):
        spare = res.get(Plain)[-1]
    await safe_send_message(app, event, res, quote=source, spare=spare)


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage, TempMessage],
    inline_dispatchers=[
        Twilight([
            FullMatch("/pid"),
            FullMatch("-", optional=True),
            ParamMatch() @ "pid"
        ])
    ],
    decorators=[Permission.require(channel.module)]
))
async def pid_pictures(
        app: Ariadne, pid: RegexResult, source: Source,
        event: Union[GroupMessage, FriendMessage, TempMessage]
):
    pid = pid.result.display.strip()
    res = await get_image_pid(pid)

    spare = None
    if res.has(Image):
        spare = res.get(Plain)[-1]
    await safe_send_message(app, event, res, quote=source, spare=spare)


async def get_image_keyword(keyword: str) -> MessageChain:
    return await get_image(URL + f"/api/pixiv/search?word={keyword}")


async def get_image_pid(pid: Union[int, str]) -> MessageChain:
    # return await get_image((URL + f"/api/pixiv/illust?id={pid}"))
    session = Ariadne.service.client_session
    img_url = pid_url.format(pid)
    try:
        async with session.get(img_url) as resp:
            if resp.status == 200:
                img_content = await resp.read()
                return MessageChain([
                    Plain(text=f"你要的图片来辣！\n"),
                    Image(data_bytes=img_content),
                    Plain(text=f"\nurl:{img_url}"),
                ])
            elif resp.status == 503:
                return MessageChain([
                    Plain("API限速，访问频率过高，请等一等再试哦。"),
                    Plain(text=f"\nurl:{img_url}")
                ])
            else:
                return MessageChain([
                    Plain("连接失败，请检查是不是pid有误。")
                ])
    except Exception as e:
        return MessageChain(f"出现了一点错误：{str(e)}")


def change_pixiv_url(url: str):
    # available = "i.pixiv.re"
    available = "pixiv.re"
    url = "https://" + available + "/" + (
        url.split('/')[-1]
        .replace("_p0", "")
        .replace("_p", "-")
        .replace(".png", ".jpg")
    )
    # url = (
    #     url.replace("i.pximg.net", available)
    #         .replace("i.pixiv.cat", available)
    #         .replace("_webp", "")
    # )
    return url


async def get_image(url: str) -> MessageChain:
    session = Ariadne.service.client_session
    try:
        async with session.get(url) as resp:
            result: Dict = await resp.json()
    except Exception as e:
        logger.error(e)
        return MessageChain(f"出现了一点错误:\n{str(e)}")

    if result.get("error"):
        return MessageChain("出现了一点错误:\n" + result["error"]["message"])

    if result.get("illusts"):
        if len(result["illusts"]) != 0:
            data = random.choice(result["illusts"])
        else:
            return MessageChain(f"没有搜到相关图片呢，果咩纳塞~")
    elif result.get("illust"):
        data = result["illust"]
    else:
        return MessageChain(f"没有搜到相关图片呢，果咩纳塞~")

    try:
        img_url = data["meta_single_page"]["original_image_url"]
    except KeyError:
        img_url = data["meta_pages"][-1]["image_urls"]["original"]
    img_url = change_pixiv_url(img_url)
    info = f"title: {data['title']}\nauthor: {data['user']['name']}\nurl:{img_url}"
    async with session.get(url=img_url) as resp:
        if resp.status == 200:
            img_content = await resp.read()
            return MessageChain([
                Plain(text=f"你要的图片来辣！\n"),
                Image(data_bytes=img_content),
                Plain(text=f"\n{info}"),
            ])
        elif resp.status == 503:
            return MessageChain([
                Plain("API限速，访问频率过高，请等一等再试哦。"),
                Plain(text=f"\n{info}")
            ])
        else:
            return MessageChain([
                Plain("连接失败，请检查是不是pid有误。")
            ])


async def get_random_img() -> MessageChain:
    id = random.choice(idList)
    url = f'https://img.moehu.org/pic.php?id={id}'

    session = Ariadne.service.client_session
    async with session.get(url) as r:
        return MessageChain(Image(data_bytes=await r.read()))
