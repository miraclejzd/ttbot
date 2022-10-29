from typing import Union

from graia.ariadne.entry import *
from graia.saya import Channel

from utils import Permission, safe_send_message
from .pero_dog_contents import pero_dog_contents

import random

channel = Channel.current()

channel.name("pero_dog_dairy")
channel.author("miraclejzd")
channel.description("发送一篇舔狗日记")


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage, TempMessage],
    inline_dispatchers=[Twilight(
        FullMatch("/舔狗日记")
    )],
    decorators=[Permission.require(channel.module)]
))
async def add_record(
        app: Ariadne,
        source: Source,
        evt: Union[GroupMessage, FriendMessage, TempMessage]
):
    List = [random.choice(pero_dog_contents).replace('*', '')]
    await safe_send_message(app, evt, MessageChain(List), source)
