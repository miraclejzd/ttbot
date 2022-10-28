from loguru import logger
from typing import Union

from graia.ariadne.entry import *
from graia.saya.channel import Channel
from graia.ariadne.message.parser.twilight import ParamMatch

from utils import Permission, safe_send_message
from .util import get_game_id
from .word_guess import word_guess
from ._24_points import twenty_four_points
from .voice_guess import voice_guess, get_voice_dict

channel = Channel.current()

channel.name("games")
channel.author("miraclejzd")
channel.description("群聊小游戏插件，一些有趣的小游戏。")

game_running = {}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage, TempMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("/word"),
                RegexMatch(r"(l|length)=[0-9]+", optional=True) @ "length",
                RegexMatch(r"(d|dic)=\w+", optional=True) @ "dic",
                ArgumentMatch("-help", "-h", action="store_true", optional=True) @ "get_help",
            ])
        ]
    )
)
async def game_word_guess(
        app: Ariadne,
        ev: Union[GroupMessage, TempMessage, FriendMessage],
        source: Source,
        dic: RegexResult,
        length: ArgResult,
        get_help: ArgResult,
):
    if not Permission(ev).get(channel.module):
        return

    game_id = get_game_id(ev)
    if game_id in game_running and game_running[game_id]:
        return await safe_send_message(app, ev, MessageChain("已有正在运行中的游戏实例，请等待游戏结束！"), source)

    game_running[game_id] = True
    await word_guess(app, ev, source, dic, length, get_help, game_id)
    game_running[game_id] = False


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage, TempMessage],
    inline_dispatchers=[Twilight(
        FullMatch("/"),
        UnionMatch("24", "24p", "24d", "24点", "二十四点"),
        RegexMatch(r"", optional=True) @ "length",
    )]
))
async def game_24_points(
        app: Ariadne,
        evt: Union[GroupMessage, FriendMessage, TempMessage],
        source: Source
):
    if not Permission(evt).get(channel.module):
        return

    game_id = get_game_id(evt)
    if game_id in game_running and game_running[game_id]:
        return await safe_send_message(app, evt, MessageChain("已有正在运行中的游戏实例，请等待游戏结束！"), source)

    game_running[game_id] = True
    await twenty_four_points(app, evt, source, game_id)
    game_running[game_id] = False


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage, TempMessage],
    inline_dispatchers=[Twilight(
        FullMatch("/猜语音"),
        ParamMatch(optional=True) @ "lang"
    )]
))
async def game_voice_guess(
        app: Ariadne,
        evt: Union[GroupMessage, FriendMessage, TempMessage],
        lang: RegexResult,
        source: Source
):
    if not Permission(evt).get(channel.module):
        return

    game_id = get_game_id(evt)
    if game_id in game_running and game_running[game_id]:
        return await safe_send_message(app, evt, MessageChain("已有正在运行中的游戏实例，请等待游戏结束！"), source)

    game_running[game_id] = True
    await voice_guess(app, evt, lang, source, game_id)
    game_running[game_id] = False


@channel.use(ListenerSchema(listening_events=[ApplicationLaunch]))
async def init():
    try:
        await get_voice_dict()
        logger.success("原神角色语音加载成功！")
    except Exception as e:
        logger.error(e)
