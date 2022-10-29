from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.mirai import NudgeEvent

from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from utils.Permission import Permission
from utils.MessageChain_util import safe_send_group_message

channel = Channel.current()

channel.name("chuochuo")
channel.author("miraclejzd")
channel.description("戳戳bot回复插件")


@channel.use(ListenerSchema(
    listening_events=[NudgeEvent],
    decorators=[Permission.require(channel.module)]
))
async def chuochuo(app: Ariadne, event: NudgeEvent):
    if event.context_type == "group":
        if event.target == app.account:
            await safe_send_group_message(
                app,
                event.group_id,
                MessageChain("不要拍拍啦，好痛的！")
            )
    elif event.context_type == "friend":
        await app.send_friend_message(
            event.friend_id,
            MessageChain("单独拍我干什么！")
        )
    else:
        return
