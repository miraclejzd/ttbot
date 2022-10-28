from typing import Union

from graia.ariadne.entry import *
from graia.saya import Channel
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.message.parser.twilight import FullMatch, RegexResult, ParamMatch, SpacePolicy

from utils.Permission import Permission
from utils.text_util import GraiaAdapter, TextEngine
from .query_resource import get_resource_type_list, query_resource, init, load_data, check_resource_exists

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                FullMatch("/位置"),
                FullMatch("-", optional=True),
                ParamMatch() @ "resource_name",
            ])
        ]
    )
)
async def genshin_resource_points(
        app: Ariadne,
        message: MessageChain,
        group: Group,
        resource_name: RegexResult
):
    if not Permission(group).get(channel.module):
        return
    resource_name = resource_name.result.display.strip()
    if check_resource_exists(resource_name):
        await get_resource_list()
        await app.send_group_message(group, MessageChain("正在生成位置...."))
        await app.send_group_message(group, await query_resource(resource_name), quote=message.get_first(Source))
    else:
        await app.send_group_message(
            group,
            MessageChain(f"未查找到 {resource_name} 资源，可通过 “原神资源列表” 获取全部资源名称.."),
            quote=message.get_first(Source)
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("原神资源列表")])],
    )
)
async def genshin_resource_point_list(app: Ariadne, group: Group):
    await app.send_message(group, await get_resource_list())


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def launch_init():
    load_data()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[Twilight(FullMatch("更新原神地图"))]
    )
)
async def update_resource(app: Ariadne, event: Union[GroupMessage, FriendMessage]):
    if not Permission(event).get(channel.module):
        return

    await app.send_message(event, MessageChain("正在更新中..."))
    try:
        await init()
        await app.send_message(event, MessageChain("原神地图更新成功"))
    except Exception as e:
        await app.send_message(event, MessageChain(f"原神地图更新失败\n{str(e)}"))


async def get_resource_list() -> MessageChain:
    content = get_resource_type_list()
    return MessageChain([Image(data_bytes=TextEngine([GraiaAdapter(MessageChain(content))], min_width=4096).draw())])
