import asyncio
import random

from graia.ariadne.entry import *
from graia.saya import Channel
from graia.ariadne.message.parser.twilight import ElementMatch, ElementResult, WildcardMatch

from .words import AdminWords, MemberWords
from utils.Permission import Permission
from utils.reply_filter import filt
from utils.MessageChain_util import safe_send_group_message
from utils.TXSDK_util import TXSDK

channel = Channel.current()

channel.name("chat_reply")
channel.author("miraclejzd")
channel.description("bot智能回复")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([
                "at" @ ElementMatch(At, optional=True),
                WildcardMatch()
            ])
        ],
        decorators=[Permission.require(channel.module, admin_special=False)]
    )
)
async def chat_reply(app: Ariadne, group: Group, message: MessageChain, sender: Member, at: ElementResult):
    content = "".join(plain.text for plain in message.get(Plain)).strip().replace(" ", ", ")
    if at.matched and at.result.target == app.account:
        if content == "":
            await exec_empty_content(app=app, group=group, sender=sender)
        else:
            text = await get_API_response(content)
            if text:
                await asyncio.sleep(2)
                await safe_send_group_message(app, group, MessageChain([
                    Plain(text=f" {text}")
                ]))
    else:
        if content == "":
            return
        elif not filt(content):
            print("出现了过滤词，没有发出去哦~")
            return
        elif random.randint(0, 100) > 10:
            print("运气不好，没有发出去哦~")
            return
        else:
            print("运气不错哦~")
            text = await get_API_response(content)
            if text:
                await asyncio.sleep(2)
                await safe_send_group_message(app, group, MessageChain([
                    Plain(text=f" {text}")
                ]))


async def exec_empty_content(app: Ariadne, group: Group, sender: Member):
    if Permission.get_admin(sender):
        txt = AdminWords[random.randint(0, len(AdminWords) - 1)]
    else:
        txt = MemberWords[random.randint(0, len(MemberWords) - 1)]
    await safe_send_group_message(
        app,
        group,
        MessageChain(txt),
    )


async def get_API_response(content: str):
    resp = TXSDK.NLP.get_resp({"Query": content})
    return resp['error'] if 'error' in resp.keys() else resp['Reply']
