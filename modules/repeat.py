import asyncio
from typing import Dict, Union

from graia.ariadne.entry import *
from graia.saya import Channel

from utils import Permission
from utils.reply_filter import filt

record: Dict[str, Dict[int, Union[None, MessageChain, int]]] = {
    'message': {},
    'chuochuo': {}
}
repeated: Dict[str, Dict[int, bool]] = {
    'message': {},
    'chuochuo': {}
}

channel = Channel.current()

channel.name("repeat")
channel.author("miraclejzd")
channel.description("复读机插件")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[Permission.require(channel.module)]
    ),
)
async def repeat_message(app: Ariadne, group: Group, message: MessageChain):
    gid = group.id
    rec = record['message']
    rep = repeated['message']
    if not filt(message.display.strip()):
        rec[gid] = None
        return
    try:
        last_message = rec[gid]
        if last_message == message:
            if not rep[gid]:
                rep[gid] = True
                await asyncio.sleep(2)
                await app.send_group_message(group, message)
        else:
            rep[gid] = False
            rec[gid] = message
    except KeyError:
        rec[gid] = message
        rep[gid] = False


@channel.use(
    ListenerSchema(
        listening_events=[NudgeEvent],
        decorators=[Permission.require(channel.module)]
    )
)
async def repeat_chuochuo(app: Ariadne, event: NudgeEvent):
    gid = event.group_id
    target = event.target
    if target == app.account:
        return

    rec = record['chuochuo']
    rep = repeated['chuochuo']
    try:
        last_chuochuo = rec[gid]
        if last_chuochuo == target:
            if not rep[gid]:
                rep[gid] = True
                await asyncio.sleep(2)
                await app.send_nudge(target, gid)
        else:
            rep[gid] = False
            rec[gid] = target
    except KeyError:
        rec[gid] = target
        rep[gid] = False
