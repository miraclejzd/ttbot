from typing import Union

from graia.ariadne.entry import *
from graia.saya import Channel
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.message.parser.twilight import FullMatch, RegexResult, ParamMatch

from utils import Permission, GraiaAdapter, TextEngine, safe_send_message
from .query_resource import get_resource_type_list, query_resource, init, load_data, check_resource_exists

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def launch_init():
    load_data()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage, TempMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("/位置"),
                FullMatch("-", optional=True),
                ParamMatch() @ "resource_name",
            ])
        ],
        decorators=[Permission.require(channel.module)]
    )
)
async def genshin_resource_points(
        app: Ariadne,
        source: Source,
        evt: Union[GroupMessage, FriendMessage, TempMessage],
        resource_name: RegexResult
):
    resource_name = resource_name.result.display.strip()
    if check_resource_exists(resource_name):
        await safe_send_message(app, evt, MessageChain("正在生成位置...."))
        await safe_send_message(app, evt, await query_resource(resource_name), source)
    else:
        await safe_send_message(
            app, evt,
            MessageChain(f"未查找到 {resource_name} 资源，可通过 “原神资源列表” 获取全部资源名称.."),
            source
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage, TempMessage],
        inline_dispatchers=[Twilight([FullMatch("原神资源列表")])],
        decorators=[Permission.require(channel.module)]
    )
)
async def genshin_resource_point_list(
        app: Ariadne, source: Source,
        evt: Union[GroupMessage, FriendMessage, TempMessage]
):
    await safe_send_message(app, evt, await get_resource_list(), source)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[Twilight(FullMatch("更新原神地图"))],
        decorators=[Permission.require_admin()]
    )
)
async def update_resource(app: Ariadne, event: Union[GroupMessage, FriendMessage], source: Source):
    await safe_send_message(app, event, MessageChain("正在更新中..."))
    try:
        await init()
        await safe_send_message(app, event, MessageChain("原神地图更新成功"), source)
    except Exception as e:
        await safe_send_message(app, event, MessageChain(f"原神地图更新失败\n{str(e)}"), source)


async def get_resource_list() -> MessageChain:
    content = get_resource_type_list()
    return MessageChain([Image(data_bytes=TextEngine([GraiaAdapter(MessageChain(content))], min_width=4096).draw())])
