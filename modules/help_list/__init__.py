from typing import Union

from graia.ariadne.entry import *
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from .helpList import helpList
from utils import Permission, Forward_generator, safe_send_message

channel = Channel.current()

channel.name("help_list")
channel.author("miraclejzd")
channel.description("bot功能列表")


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage, TempMessage],
    inline_dispatchers=[Twilight(
        ElementMatch(At, optional=True),
        FullMatch("/"),
        UnionMatch("help", "帮助")
    )],
    decorators=[Permission.require(channel.module)]
))
async def help_list(app: Ariadne, evt: Union[GroupMessage, FriendMessage, TempMessage]):
    fwd = Forward_generator(app.account, "ttbot", helpList)
    await safe_send_message(app, evt, MessageChain(fwd))
