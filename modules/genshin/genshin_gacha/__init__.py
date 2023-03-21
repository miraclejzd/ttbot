from typing import Union

from graia.ariadne.entry import *
from graia.saya import Channel

from .settings import *
from utils.Permission import Permission
from utils.MessageChain_util import Forward_generator

channel = Channel.current()


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage, TempMessage],
    inline_dispatchers=[Twilight(
        FullMatch("/"),
        RegexMatch(r"(((角色|武器|常驻)(单抽|十连)\d?)|(抽卡|十连))\s?$") @ "command"
    )],
    decorators=[Permission.require(channel.module)]
))
async def genshin_gacha(
        app: Ariadne, evt: Union[GroupMessage, FriendMessage, TempMessage],
        command: RegexResult,
        source: Source
):
    cmd = command.result.display.strip()
    if cmd == "十连":
        Fwd = Forward_generator(app.account, "ttbot", [
            "/角色单抽  对第一个UP池进行单抽",
            "/角色十连 对第一个UP池进行十连抽卡",
            "/角色单抽n 对第n个UP池进行单抽",
            "/角色十连n 对第n个UP池进行十连抽卡",
            "/武器单抽 对武器池进行单抽",
            "/武器十连 对武器池进行十连抽卡",
            "/常驻单抽 对常驻池进行单抽",
            "/常驻十连 对常驻池进行十连抽卡"
        ])
        await app.send_message(evt, MessageChain(Fwd))

    else:
        senderID = evt.sender.id
        idx = int(cmd[-1]) - 1 if cmd[-1].isdigit() else DefaultIndex
        gacha_num = cmd[2:4]
        gacha_type = cmd[:2]
        url = ApiUrl.format(addr_mid[gacha_type], addr_last[gacha_num], senderID, idx)

        session = Ariadne.service.client_session
        async with session.get(url=url, headers=headers) as resp:
            resp = await resp.json()

        if resp["code"] != 0:
            await app.send_message(evt, MessageChain(f"获取Http请求出现错误：\n{resp['message']}"))
        else:
            data = resp["data"]
            await app.send_message(
                evt,
                MessageChain(
                    f'当前卡池子为: {"+".join(char["goodsName"] for char in data["star5Up"])}，',
                    f'距离下次小保底还剩{data["role90Surplus"]}抽，大保底还剩{data["role180Surplus"]}抽' if gacha_type == "角色" else f'距离下次保底还剩{data["arm80Surplus"] if gacha_type == "武器" else data["perm90Surplus"]}抽',
                    Image(url=data["imgHttpUrl"])
                ),
                quote=source
            )

            if data["star5Cost"] != 0:
                name = evt.sender.nickname if isinstance(evt, FriendMessage) else evt.sender.name
                await app.send_message(
                    evt,
                    MessageChain(
                        f'{name} 通过{cmd}获得了{"+".join(char["goodsName"] for char in data["star5Goods"])}，',
                        f'累计消耗{data["star5Cost"]}抽'
                    )
                )
