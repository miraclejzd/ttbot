from typing import Union

from graia.ariadne.entry import *
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from .helpList import helpList
from utils.Permission import Permission
from utils.MessageChain_util import Forward_generator, safe_send_message

channel = Channel.current()

channel.name("help_list")
channel.author("miraclejzd")
channel.description("bot功能列表")


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage, TempMessage],
    inline_dispatchers=[Twilight(
        FullMatch("/"),
        UnionMatch("help", "帮助")
    )]
))
async def help_list(app: Ariadne, evt: Union[GroupMessage, FriendMessage, TempMessage]):
    if not Permission(evt).get(channel.module):
        return

    fwd = Forward_generator(app.account, "ttbot", helpList)
    await safe_send_message(app, evt, MessageChain(fwd))


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def mention_me(app: Ariadne, group: Group, message: MessageChain = MentionMe()):
    if not Permission(group).get(channel.module):
        return

    msg = message.display.strip()

    if msg[0:2].find("帮助") != -1 or msg[0:4].casefold() == "help":
        fwd = Forward_generator(app.account, "ttbot", helpList)
        await safe_send_message(app, group, MessageChain(fwd))
