import asyncio
from asyncio import Lock
from loguru import logger
from typing import Union, NoReturn

from graia.ariadne.entry import *
from graia.saya import Channel
from graia.broadcast.interrupt.waiter import Waiter
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.parser.twilight import RegexResult, ArgResult

from utils import safe_send_message
from .wordGuesser import WordGuesser, word_list, word_dics
from ..util import get_game_id

saya = Saya.current()
channel = Channel.current()

inc = InterruptControl(saya.broadcast)
mutex = Lock()

game_word_dic = {}
DEFAULT_DIC = "CET4"


class WordGuessWaiter(Waiter.create([GroupMessage, TempMessage, FriendMessage])):
    """word_guess Waiter"""

    def __init__(
            self,
            wg_instance: WordGuesser,
            game_id: int
    ):
        self.guesser = wg_instance
        self.game_id = game_id

    async def detected_event(
            self,
            app: Ariadne,
            ev: Union[GroupMessage, TempMessage, FriendMessage],
            message: MessageChain,
            message_source: Source,
    ):
        word = message.display.strip()
        if self.game_id == (game_id := get_game_id(ev)):
            if word in ("/giveup", "/g"):
                dic = game_word_dic[game_id]
                word_data = word_list[dic][len(self.guesser.word)][self.guesser.word]
                explain = "\n".join(f"【{key}】：{word_data[key]}" for key in word_data)
                await app.send_message(
                    ev,
                    MessageChain(
                        [
                            Image(data_bytes=self.guesser.get_board_bytes()),
                            Plain("很遗憾，没有猜出来呢~\n" + f"单词：{self.guesser.word}\n{explain}"),
                        ]
                    ),
                    quote=message_source,
                )
                return True

            if word == "/hint":
                await app.send_message(
                    ev,
                    MessageChain([Image(data_bytes=self.guesser.draw_hint())]),
                    quote=message_source,
                )
                return False

            if word.encode("utf-8").isalpha():
                if (w_l := len(word)) != (g_l := self.guesser.length):
                    await app.send_message(
                        ev,
                        MessageChain(f"答案长度为 {g_l} ，这个单词却是 {w_l} 呢"),
                        quote=message_source
                    )
                    return False

                else:
                    async with self.guesser.draw_mutex:
                        result = self.guesser.guess(word)

                    if not result:
                        return True
                    if result[0]:
                        dic = game_word_dic[game_id]
                        word_data = word_list[dic][len(self.guesser.word)][self.guesser.word]
                        explain = "\n".join(
                            f"【{key}】：{word_data[key]}" for key in word_data
                        )
                        await app.send_message(
                            ev,
                            MessageChain(
                                [
                                    Image(data_bytes=self.guesser.get_board_bytes()),
                                    Plain(
                                        f"\n{'恭喜你猜出了单词！' if result[1] else '很遗憾，没有猜出来呢'}\n"
                                        f"【单词】：{self.guesser.word}\n{explain}"
                                    ),
                                ]
                            ),
                            quote=message_source,
                        )
                        return True
                    elif not result[2]:
                        await app.send_message(
                            ev,
                            MessageChain(f"你确定 {word} 是一个合法的单词吗？"),
                            quote=message_source,
                        )
                    elif result[3]:
                        await app.send_message(
                            ev, MessageChain("你已经猜过这个单词了呢"), quote=message_source
                        )
                    else:
                        await app.send_message(
                            ev,
                            MessageChain([Image(data_bytes=self.guesser.get_board_bytes())]),
                            quote=message_source,
                        )
                    return False


async def word_guess(
        app: Ariadne,
        ev: Union[GroupMessage, TempMessage, FriendMessage],
        source: Source,
        dic: RegexResult,
        length: ArgResult,
        get_help: ArgResult,
        game_id: int
) -> NoReturn:
    if get_help.matched:
        await safe_send_message(
            app, ev,
            MessageChain(
                "WordGuess游戏\n"
                "答案为指定长度单词，发送对应长度单词即可\n"
                "灰色块代表此单词中没有此字母\n"
                "黄色块代表此单词中有此字母，但该字母所处位置不对\n"
                "绿色块代表此单词中有此字母且位置正确\n"
                "猜出单词或用光次数则游戏结束\n"
                "发起游戏：/word l=5 d=SAT，其中l/length为单词长度，d/dic为指定词典，默认为5和CET4\n"
                "查看提示：/hint\n"
                "中途放弃：/g 或 /giveup\n"
                f"注：目前包含词典：{'、'.join(word_dics)}"
            ),
            source
        )
        return

    if dic.matched:
        dic = dic.result.display.split("=")[1].strip()
        if dic not in word_dics:
            await safe_send_message(app, ev, MessageChain(f"没有找到名为{dic}的字典！已有字典：{'、'.join(word_dics)}"),
                                    source)
            return
        else:
            game_word_dic[game_id] = dic
    elif game_id not in game_word_dic:
        game_word_dic[game_id] = DEFAULT_DIC

    length = int(length.result.display.split("=")[1].strip()) if length.matched else 5
    if length not in word_list[game_word_dic[game_id]].keys():
        await safe_send_message(
            app, ev,
            MessageChain(
                f"单词长度错误，词库中没有长度为{length}的单词=！"
                f"目前词库（{game_word_dic[game_id]}）中"
                f"只有长度为{'、'.join([str(i) for i in sorted(word_list[game_word_dic[game_id]].keys())])}的单词！"
            ),
            source
        )
        return

    wg_instance = WordGuesser(length, dic=game_word_dic[game_id])
    logger.success(f"成功创建 WordGuesser 实例，单词为：{wg_instance.word}")
    await safe_send_message(
        app, ev,
        MessageChain(
            [
                Image(data_bytes=wg_instance.get_board_bytes()),
                Plain(
                    f"\n你有{wg_instance.row}次机会猜出单词，单词长度为{wg_instance.length}，请发送单词"
                ),
            ]
        ),
        quote=source,
    )
    game_end = False
    try:
        while not game_end:
            game_end = await inc.wait(
                WordGuessWaiter(wg_instance, game_id),
                timeout=300,
            )
    except asyncio.exceptions.TimeoutError:
        await safe_send_message(app, ev, MessageChain("游戏超时，进程结束"), quote=source)
