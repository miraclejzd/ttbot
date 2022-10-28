from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group

from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from utils.Permission import Permission
from utils.MessageChain_util import safe_send_message

channel = Channel.current()

channel.name("check_sese")
channel.author("miraclejzd")
channel.description("色色检查插件")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def check_sese(app: Ariadne, group: Group, message: MessageChain):
    if not Permission(group).get(channel.module):
        return
    if contain_sese(str(message)):
        await safe_send_message(
            app,
            group,
            MessageChain(f"不可以色色！！！"),
        )


def contain_sese(txt):
    if txt.find("色色") != -1:
        return 1
    elif txt.find("涩涩") != -1:
        return 1
    elif txt.find("瑟瑟") != -1:
        return 1
    elif txt.find("sese") != -1:
        return 1
    return 0
