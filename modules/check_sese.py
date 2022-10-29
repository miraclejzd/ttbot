from graia.ariadne.entry import *
from graia.saya import Channel

from utils import Permission, safe_send_message

channel = Channel.current()

channel.name("check_sese")
channel.author("miraclejzd")
channel.description("色色检查插件")


@channel.use(ListenerSchema(
    listening_events=[GroupMessage],
    decorators=[Permission.require(channel.module)]
))
async def check_sese(app: Ariadne, group: Group, message: MessageChain):
    if contain_sese(message.display):
        await safe_send_message(
            app,
            group,
            MessageChain(f"不可以色色！！！"),
        )


sese_words = [
    "色色", "涩涩", "sese"
]


def contain_sese(txt):
    for word in sese_words:
        if word in txt:
            return True
    return False
