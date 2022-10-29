from graia.ariadne.entry import *
from graia.saya import Channel
from graia.ariadne.message.parser.twilight import ParamMatch

from utils import Permission, safe_send_message

channel = Channel.current()

channel.name("aa_module")
channel.author("miraclejzd")
channel.description("测试插件(无卵用)")

f = True


# @channel.use(SchedulerSchema(crontabify("0 4 * * *")))
# @channel.use(SchedulerSchema(every_custom_seconds(10)))
# @channel.use(
#     ListenerSchema(
#         listening_events=[GroupMessage],
#         inline_dispatchers=[Twilight(
#             FullMatch("1")
#         )],
#         decorators=[Permission.require(channel.module)]
#     )
# )
async def aa_module(
        app: Ariadne, evt: GroupMessage,
):
    global f
    if f:
        await safe_send_message(app, evt, MessageChain("成功!"))
        for i in range(10000000):
            pass
        f = False
    else:
        f = True
        await safe_send_message(app, evt, MessageChain("失败!"))
