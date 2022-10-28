from typing import Optional, Union

from graia.ariadne.entry import *
from graia.saya import Channel
from graia.ariadne.util.interrupt import FunctionWaiter
from graia.ariadne.event.mirai import BotLeaveEventDisband, BotMuteEvent, BotUnmuteEvent

from Config import bot_Admin

channel = Channel.current()

channel.name("groups_events")
channel.author("miraclejzd")
channel.description("群组事件处理")


@channel.use(ListenerSchema(listening_events=[BotInvitedJoinGroupRequestEvent]))
async def new_group_invited_request(app: Ariadne, event: BotInvitedJoinGroupRequestEvent):
    quote_message = await app.send_friend_message(
        bot_Admin,
        MessageChain(
            Plain(f'有人想拉小bot进群！\n'),
            Plain(f'目标群：{event.group_name}({event.source_group})\n'),
            Plain(f'邀请人QQ：{event.supplicant}\n昵称：{event.nickname}\n'),
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
            MessageChain(Plain(f'已成功入群！')),
            quote=quote_message.id
        )
    elif result == 'n':
        await event.reject()
        await app.send_friend_message(
            bot_Admin,
            MessageChain(Plain(f'已拒绝入群！')),
            quote=quote_message.id
        )
    else:
        await app.send_friend_message(
            bot_Admin,
            MessageChain(Plain(f'好滴!我不做处理！')),
            quote=quote_message.id
        )


@channel.use(ListenerSchema(listening_events=[BotJoinGroupEvent]))
async def join_group(app: Ariadne, event: BotJoinGroupEvent):
    group = event.group
    inviter = event.inviter

    await app.send_friend_message(
        bot_Admin,
        MessageChain(
            Plain(f'小bot被拉进群啦！\n'),
            Plain(f'目标群：{group.name}({group.id})\n'),
            Plain(f'邀请人QQ：{inviter.id}\n昵称：{inviter.name}')
        )
    )


@channel.use(ListenerSchema(listening_events=[BotLeaveEventKick, BotLeaveEventDisband]))
async def leave_group(app: Ariadne, event: Union[BotLeaveEventKick, BotLeaveEventDisband]):
    group = event.group

    await app.send_friend_message(
        bot_Admin,
        MessageChain(
            Plain(f'小bot被踢出群了quq') if isinstance(event, BotLeaveEventKick) else Plain(f'呜呜呜，群被解散了quq'),
            Face(name='流泪'), Face(name='流泪'),
            Plain(f'\n\n目标群：{group.name}({group.id})\n')
        )
    )

# @channel.use(
#     ListenerSchema(listening_events=[BotMuteEvent])
# )
# async def bot_muted(group: Group):
#     if group.id in GroupLists:
#         permission_data[group.id]['mute'] = True
#         save_config()
#
#
# @channel.use(
#     ListenerSchema(listening_events=[BotUnmuteEvent])
# )
# async def bot_unmuted(group: Group):
#     if group.id in GroupLists:
#         permission_data[group.id]['mute'] = False
#         save_config()
