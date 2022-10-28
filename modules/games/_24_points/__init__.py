import re
import asyncio
from loguru import logger
from typing import Union

from graia.ariadne.entry import *
from graia.broadcast.interrupt.waiter import Waiter
from graia.broadcast.interrupt import InterruptControl

from utils import safe_send_message
from .gameSolver import gameSolver
from ..util import get_game_id

saya = Saya.current()
inc = InterruptControl(saya.broadcast)


class gameWaiter(Waiter.create([GroupMessage, TempMessage, FriendMessage])):
    def __init__(
            self,
            solver: gameSolver,
            game_id: int
    ):
        self.solver = solver
        self.game_id = game_id

    async def detected_event(
            self,
            app: Ariadne,
            evt: Union[GroupMessage, FriendMessage, TempMessage],
            msg: MessageChain,
            source: Source
    ):
        exp = msg.display.strip()
        if self.game_id == get_game_id(evt):
            if exp in ("/giveup", "/g"):
                await safe_send_message(
                    app, evt,
                    MessageChain("很遗憾，没有做出来呢~\n" + f"答案为：{self.solver.Ans}"),
                    quote=source,
                )
                return True

            # 判断算式是否合法
            pattern = "|".join(
                [" ", "\d", "\+", "\-", "\*", "/", "//", "&", "\|", "<<", ">>", "\(", "\)", "（", "）"])
            pattern = "^(" + pattern + ")+$"
            illegal = re.match(pattern, exp)
            if illegal:
                # 判断数字是否为题目所给的4个数
                numbers = re.findall("\d+", exp)
                for i, x in enumerate(numbers):
                    numbers[i] = int(numbers[i])
                if len(set(numbers) ^ set(self.solver.numbers)) != 0:
                    await safe_send_message(
                        app, evt, MessageChain("输入的数字和题目不符哦~"), source
                    )
                    return False

                try:
                    if (val := int(round(eval(exp), 7))) == 24:
                        await safe_send_message(
                            app, evt,
                            MessageChain(f"恭喜你凑出了 24 ！\n修Bot算出的答案是：{self.solver.Ans}，也能凑成24哦~"),
                            source
                        )
                        return True
                    else:
                        await safe_send_message(
                            app, evt, MessageChain(f"这个算式的结果是 {val} 哦，再想想~"), source
                        )
                        return False
                except Exception:
                    await safe_send_message(
                        app, evt, MessageChain("这个算式不合法哦..."), source
                    )
                    return False


async def twenty_four_points(
        app: Ariadne,
        evt: Union[GroupMessage, FriendMessage, TempMessage],
        source: Source,
        game_id: int
):
    solver = gameSolver()
    logger.success(f"成功创建 gameSolver 实例，题目为：{' '.join(str(x) for x in solver.numbers)}，答案为：{solver.Ans}")
    await safe_send_message(
        app, evt,
        MessageChain(f"题目是: \n{' '.join(str(x) for x in solver.numbers)}\n你可以随意调换数字的顺序，并可以使用括号~"),
        source
    )

    game_end = False
    try:
        while not game_end:
            game_end = await inc.wait(
                gameWaiter(solver, game_id),
                timeout=300,
            )
    except asyncio.exceptions.TimeoutError:
        await safe_send_message(app, evt, MessageChain("游戏超时，进程结束"), quote=source)
