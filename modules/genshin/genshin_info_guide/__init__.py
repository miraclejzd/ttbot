import traceback
from typing import Union
from loguru import logger

from graia.ariadne.entry import *
from graia.saya import Channel
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.message.parser.twilight import ParamMatch

from utils import Permission, safe_send_message
from .query_weap import load_weap_yaml, is_weap, query_weap_info, get_weap_list, update_weap_list
from .query_char import load_char_yaml, query_char_guide, query_char_info, get_char_list, update_char_list, \
    update_guide

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage, TempMessage],
        inline_dispatchers=[Twilight(
            FullMatch("/攻略"),
            FullMatch("-", optional=True),
            "name" @ ParamMatch()
        )]
    )
)
async def genshin_query_guide(
        evt: Union[GroupMessage, FriendMessage, TempMessage],
        app: Ariadne, name: RegexResult, source: Source
):
    if not Permission(evt).get(channel.module):
        return

    name = name.result.display.strip()
    try:
        await safe_send_message(app, evt, await query_char_guide(name), quote=source)
    except Exception as e:
        logger.error(traceback.format_exc())
        await safe_send_message(app, evt, MessageChain(f"出现错误:\n{e}"), quote=source)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage, TempMessage],
        inline_dispatchers=[Twilight(
            FullMatch("/查询"),
            FullMatch("-", optional=True),
            "name" @ ParamMatch()
        )]
    )
)
async def genshin_query_info(
        evt: Union[GroupMessage, FriendMessage, TempMessage],
        app: Ariadne, name: RegexResult, source: Source
):
    if not Permission(evt).get(channel.module):
        return

    name = name.result.display.strip()
    try:
        await safe_send_message(app, evt, await query_info(name), quote=source)
    except Exception as e:
        logger.error(traceback.format_exc())
        await safe_send_message(app, evt, MessageChain(f"出现错误:\n{e}"), quote=source)


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage, TempMessage],
    inline_dispatchers=[Twilight(
        FullMatch("原神角色列表")
    )]
))
async def get_character_list(
        evt: Union[GroupMessage, FriendMessage, TempMessage],
        app: Ariadne, source: Source
):
    if not Permission(evt).get(channel.module):
        return

    await safe_send_message(
        app, evt,
        get_char_list(),
        quote=source
    )


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage, TempMessage],
    inline_dispatchers=[Twilight(
        FullMatch("原神武器列表")
    )]
))
async def get_weapon_list(
        evt: Union[GroupMessage, FriendMessage, TempMessage],
        app: Ariadne, source: Source
):
    if not Permission(evt).get(channel.module):
        return
    await safe_send_message(
        app, evt,
        get_weap_list(),
        quote=source
    )


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage],
    inline_dispatchers=[Twilight(
        FullMatch("更新角色攻略")
    )]
))
async def update_character_guide(
        evt: Union[GroupMessage, FriendMessage],
        app: Ariadne, source: Source
):
    if not Permission(evt.sender).get():
        return

    try:
        await safe_send_message(app, evt, MessageChain("正在更新原神角色攻略..."))
        await update_char_list()  # 先更新角色列表
        await update_guide()  # 后更新角色攻略
        await safe_send_message(app, evt, MessageChain("更新原神角色攻略成功！"), quote=source)
    except Exception as e:
        logger.error(traceback.format_exc())
        await safe_send_message(app, evt, MessageChain(f"出现错误:\n{e}"), quote=source)


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage],
    inline_dispatchers=[Twilight(
        FullMatch("更新角色列表")
    )]
))
async def update_character(
        evt: Union[GroupMessage, FriendMessage],
        app: Ariadne, source: Source
):
    if not Permission(evt.sender).get():
        return
    try:
        await safe_send_message(app, evt, MessageChain("正在更新角色列表..."))
        await update_char_list()
        await safe_send_message(app, evt, MessageChain("更新角色列表成功！"), quote=source)
    except Exception as e:
        logger.error(e)
        await safe_send_message(app, evt, MessageChain(str(e)), quote=source)


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage],
    inline_dispatchers=[Twilight(
        FullMatch("更新武器列表")
    )]
))
async def update_weapon(
        evt: Union[GroupMessage, FriendMessage],
        app: Ariadne, source: Source
):
    if not Permission(evt.sender).get():
        return
    try:
        await safe_send_message(app, evt, MessageChain("正在更新武器列表..."))
        await update_weap_list()
        await safe_send_message(app, evt, MessageChain("更新武器列表成功！"), quote=source)
    except Exception as e:
        logger.error(e)
        await safe_send_message(app, evt, MessageChain(str(e)), quote=source)


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def launch_init():
    load_char_yaml()
    load_weap_yaml()
    logger.success("原神角色、武器信息加载成功！")


async def query_info(name: str) -> MessageChain:
    if is_weap(name):
        return await query_weap_info(name)
    return await query_char_info(name)
