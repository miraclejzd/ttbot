from typing import Optional

from graia.ariadne.entry import *
from graia.saya import Channel
from graia.ariadne.util.interrupt import FunctionWaiter

from Config import bot_Admin

channel = Channel.current()

channel.name("friends_events")
channel.author("miraclejzd")
channel.description("好友事件处理")


@channel.use(
    ListenerSchema(
        listening_events=[NewFriendRequestEvent]
    ),
)
async def new_friend_request(app: Ariadne, event: NewFriendRequestEvent):
    source_group = event.source_group
    group_name = "未知群组"

    if source_group:
        group = await app.get_group(source_group)
        group_name = group.name if group is not None else "未知群组"

    quote_message: ActiveMessage = await app.send_friend_message(
        bot_Admin,
        MessageChain(
            Plain(f'有人想添加小bot为好友！\nQQ：{event.supplicant}\n昵称：{event.nickname}\n'),
            Plain(f'来自群：{group_name}({source_group})\n') if source_group else Plain('\n来自好友搜索\n'),
            Plain(event.message) if event.message else Plain('无附加信息'),
            Plain('\n\n请在24h内发送 Y 或 N (不做处理为S)，否则自动拒绝'),
        )
    )

    async def waiter(f: Friend, mess: MessageChain) -> Optional[str]:
        if f.id == bot_Admin:
            q_list = mess.get(Quote)
            if q_list and q_list[0].id != quote_message.id:
                return None

            mess = mess.display.strip().casefold()
            if mess in ['y', 'n', 's']:
                return mess
            else:
                await app.send_friend_message(
                    bot_Admin,
                    MessageChain(
                        Plain(f'请输入 Y 、 N 或 S')
                    ),
                    quote=quote_message.id
                )

    result = await FunctionWaiter(waiter, [FriendMessage]).wait(timeout=86400)
    if result is None:
        await app.send_friend_message(
            bot_Admin,
            MessageChain(Plain(f'超时啦，已经帮你自动拒绝了哦~')),
            quote=quote_message.id
        )
    elif result == 'y':
        await event.accept()
        await app.send_friend_message(
            bot_Admin,
            MessageChain(Plain(f'已成功添加好友！')),
            quote=quote_message.id
        )
    elif result == 'n':
        await event.reject()
        await app.send_friend_message(
            bot_Admin,
            MessageChain(Plain(f'已拒绝其添加好友请求！')),
            quote=quote_message.id
        )
    else:
        await app.send_friend_message(
            bot_Admin,
            MessageChain(Plain(f'好滴!我不做处理！')),
            quote=quote_message.id
        )
