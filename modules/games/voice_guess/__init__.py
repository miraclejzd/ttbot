import asyncio
import traceback
from typing import Union
from loguru import logger

from graia.ariadne.entry import *

from utils import safe_send_message
from modules.genshin.genshin_info_guide.query_char import is_char
from .voiceGuesser import voiceGuesser, get_voice_dict
from ..util import get_game_id

saya = Saya.current()
inc = InterruptControl(saya.broadcast)

mutex = asyncio.Lock()


class gameWaiter(Waiter.create([GroupMessage, TempMessage, FriendMessage])):
    def __init__(
            self,
            vg: voiceGuesser,
            game_id: int
    ):
        self.vg = vg
        self.game_id = game_id

    async def detected_event(
            self,
            app: Ariadne,
            evt: Union[GroupMessage, FriendMessage, TempMessage],
            msg: MessageChain,
            source: Source
    ):
        msg = msg.display.strip()
        if self.game_id == get_game_id(evt):
            async with mutex:
                if msg in ("/giveup", "/g"):
                    await safe_send_message(
                        app, evt,
                        MessageChain("很遗憾，没有猜出来呢~\n" + f"角色为：{self.vg.char_name}\n语音情景为：{self.vg.info}"),
                        source
                    )
                    return True
                if is_char(msg):
                    if msg in self.vg.Ans:
                        await safe_send_message(
                            app, evt,
                            MessageChain("恭喜你猜对啦！\n" + f"角色为：{self.vg.char_name}\n语音情景为：{self.vg.info}"),
                            source
                        )
                        return True
                    else:
                        await safe_send_message(
                            app, evt, MessageChain("不对哦，再想想~"), source
                        )
                        return False


async def voice_guess(
        app: Ariadne,
        evt: Union[GroupMessage, FriendMessage, TempMessage],
        lang: RegexResult,
        source: Source,
        game_id: int
):
    lang = lang.result.display.strip() if lang.matched else "中"
    if lang not in ["中", "英", "日", "韩"]:
        return await safe_send_message(app, evt, MessageChain("没有该语种的语音信息哦~\n目前只有 中、英、日、韩 "), source)

    try:
        vg = voiceGuesser(lang)
        await vg.init()
    except Exception as e:
        logger.error(traceback.format_exc())
        return await safe_send_message(app, evt, MessageChain(f"初始化游戏失败：\n{str(e)}"), source)

    logger.success(f"成功创建 voiceGuesser 实例，人物为：{vg.char_name}，语音背景为：{vg.info}")
    await safe_send_message(
        app, evt,
        MessageChain(Voice(url=vg.data_url))
    )

    game_end = False
    try:
        while not game_end:
            game_end = await inc.wait(
                gameWaiter(vg, game_id),
                timeout=300,
            )
    except asyncio.exceptions.TimeoutError:
        await safe_send_message(app, evt, MessageChain("游戏超时，进程结束"), quote=source)
