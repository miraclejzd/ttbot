import traceback
from typing import Union
from loguru import logger

from graia.ariadne.entry import *
from graia.saya.channel import Channel

from utils import Permission, TXSDK, safe_send_message

channel = Channel.current()

channel.name("translate")
channel.author("miraclejzd")
channel.description("/翻译 xxxx： 进行文本翻译")


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, TempMessage, FriendMessage],
    inline_dispatchers=[Twilight(
        ElementMatch(At, optional=True),
        FullMatch("/"),
        UnionMatch("翻译", "译", "tr"),
        WildcardMatch() @ "text"
    )],
    decorators=[Permission.require(channel.module)]
))
async def translate(
        app: Ariadne, text: RegexResult, msg: MessageChain, source: Source,
        evt: Union[GroupMessage, TempMessage, FriendMessage]
):
    if msg.has(Quote):
        quote = msg.get_first(Quote)
        try:
            ori_evt: MessageEvent
            if isinstance(evt, FriendMessage):
                ori_evt = await app.get_message_from_id(quote.id, evt.sender)
            else:
                ori_evt = await app.get_message_from_id(quote.id, evt.sender.group)
        except Exception as e:
            logger.error(traceback.format_exc())
            return await safe_send_message(app, evt, MessageChain(f"出现了一点错误哦:\n{str(e)}"))
        ori_msg = ori_evt.message_chain
        text = " ".join(plain.text for plain in ori_msg.get(Plain))
    else:
        text = text.result.display.strip()

    lang_data = {
        "Text": text,
        "ProjectId": 0
    }
    lang_resp = await TXSDK.language_detect.async_get_resp(lang_data)
    if "error" in lang_resp:
        return await safe_send_message(app, evt, MessageChain(f"出现了一点错误:\n{lang_resp['error']}"), source)
    else:
        ori_lang = lang_resp["Lang"]
        if ori_lang == "zh":
            tar_lang = "en"
        else:
            tar_lang = "zh"

        trans_data = {
            "SourceText": text,
            "Source": ori_lang,
            "Target": tar_lang,
            "ProjectId": 0
        }
        trans_resp = await TXSDK.text_translate.async_get_resp(trans_data)

        if "error" in lang_resp:
            return await safe_send_message(app, evt, MessageChain(f"出现了一点错误:\n{trans_resp['error']}"), source)
        await safe_send_message(
            app, evt,
            MessageChain(trans_resp['TargetText']),
            source
        )
