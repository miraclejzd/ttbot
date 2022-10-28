from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.twilight import Twilight, FullMatch
from graia.ariadne.model import Group

from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from utils.Permission import Permission
from utils.MessageChain_util import safe_send_message
from .pero_dog_contents import pero_dog_contents

import random

channel = Channel.current()

channel.name("pero_dog_dairy")
channel.author("miraclejzd")
channel.description("发送一篇舔狗日记")


@channel.use(ListenerSchema(
    listening_events=[GroupMessage],
    inline_dispatchers=[Twilight(
        FullMatch("/舔狗日记")
    )]
))
async def add_record(app: Ariadne, group: Group):
    if not Permission(group).get(channel.module):
        return

    List = [random.choice(pero_dog_contents).replace('*', '')]
    await safe_send_message(app, group, MessageChain(List))
