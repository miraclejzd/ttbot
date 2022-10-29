import random
from datetime import datetime

from graia.ariadne.entry import *
from graia.saya import Channel

from utils import Permission

channel = Channel.current()

channel.name("forward_message")
channel.author("miraclejzd")
channel.description("转发消息测试插件(无卵用)")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(FullMatch("看看奶"))],
        decorators=[Permission.require(channel.module)]
    )
)
async def create_forward(app: Ariadne, group: Group, member: Member):
    fwd_nodelist = [
        ForwardNode(
            target=member,
            time=datetime.now(),
            message=MessageChain(Image(path=r"./data/image/big_milk.png")),
        )
    ]
    member_list = await app.get_member_list(group)
    for _ in range(3):
        random_member: Member = random.choice(member_list)
        fwd_nodelist.append(
            ForwardNode(
                target=random_member,
                time=datetime.now(),
                message=MessageChain("好大的奶")
            )
        )

    message = MessageChain(Forward(fwd_nodelist))
    await app.send_message(group, message)
