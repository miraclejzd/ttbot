from enum import Enum
from typing import Union

from graia.ariadne.entry import *
from graia.saya import Channel

from .util import handlers
from utils.Permission import Permission

channel = Channel.current()
channel.name("music_search")
channel.author("miraclejzd")
channel.description("点歌插件  发送 '点歌 xxx' 即可点歌")

DEFAULT_MUSIC_PLATFORM = "wyy"
DEFAULT_SEND_TYPE = "card"


class MusicPlatform(Enum):
    wyy = "网易云音乐"
    qq = "QQ音乐"


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage],
    inline_dispatchers=[
        Twilight([
            FullMatch("/点歌"),
            ArgumentMatch("-p", "-platform", type=str, choices=["qq", "wyy"], optional=True) @ "platform",
            ArgumentMatch("-t", "-type", type=str, choices=["card", "voice", "file"], optional=True) @ "send_type",
            WildcardMatch() @ "keyword"
        ])
    ]
))
async def music_search(app: Ariadne, event: Union[GroupMessage, FriendMessage], keyword: RegexResult,
                       platform: ArgResult, send_type: ArgResult):
    if not Permission(event).get(channel.module):
        return

    platform = platform.result.display.strip() if platform.matched else DEFAULT_MUSIC_PLATFORM
    send_type = send_type.result if send_type.matched else DEFAULT_SEND_TYPE
    keyword = keyword.result
    element = await handlers[platform](keyword, send_type)
    if element:
        if isinstance(element, tuple):
            if isinstance(event, GroupMessage):
                meth = UploadMethod.Group
                tar = event.sender.group
            else:
                meth = UploadMethod.Friend
                tar = event.sender

            await app.upload_file(
                data=element[1],
                method=meth,
                target=tar,
                name=f"{element[0]}.mp3"
            )
        else:
            await app.send_message(event, MessageChain(element))
