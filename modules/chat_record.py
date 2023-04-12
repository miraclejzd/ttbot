from loguru import logger
from typing import Optional

from graia.ariadne.entry import *
from graia.saya import Channel

from graia.ariadne.message.parser.twilight import SpacePolicy
from graia.ariadne.util.interrupt import FunctionWaiter
from graia.ariadne.exception import AccountMuted

from Config import bot_Admin

from utils.RecordSaver import RecordSaver
from utils import Permission, safe_send_message

channel = Channel.current()

channel.name("chat_record")
channel.author("miraclejzd")
channel.description("聊天记录保存插件")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(
            ElementMatch(At, optional=True),
            UnionMatch("入典", "添加语录")
        )],
        decorators=[Permission.require(channel.module, admin_special=False)]
    ),
)
async def add_record(app: Ariadne, group: Group, message: MessageChain, source: Source):
    if Quote not in message:
        message = message.display.strip()
        if message == "入典" or message == "添加语录":
            return await safe_send_message(
                app, group, MessageChain("请 引用（回复） 待添加的消息再输入 \"入典\" 或 \"添加语录\" 哦~"), source
            )

    quote = message.get_first(Quote)
    ori_id = quote.id
    try:
        ori_event = await app.get_message_from_id(ori_id, group)
    except Exception as e:
        logger.error(e)
        return await safe_send_message(app, group, MessageChain("出于某种原因，小bot添加不了哦~"), source)

    ori_chain = ori_event.message_chain
    saver = RecordSaver(group=group.id)
    docList = await saver.to_docList(ori_chain)
    status, msg = saver.add(quote.sender_id, docList, source.time)

    if status == 0:
        await safe_send_message(app, group, MessageChain("已添加"), source)
    else:
        await safe_send_message(app, group, MessageChain("添加失败,error:" + str(msg)), source)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(UnionMatch("随机语录", "抽卡"))],
        decorators=[Permission.require(channel.module, admin_special=False)]
    )
)
async def random_record(app: Ariadne, group: Group, source: Source):
    saver = RecordSaver(group=group.id)
    back = saver.rand_doc()

    if back is not None:
        member = await app.get_member(group, back['QQ'])
        nickname = member.name

        msgList = [nickname, ":\n"]
        msgList.extend(RecordSaver.to_MessageChain(back['docList']))
    else:
        msgList = ["目前没有任何语录哦~"]
    await safe_send_message(app, group, MessageChain(msgList), quote=source)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[
            DetectPrefix("查询语录"),
            Permission.require(channel.module, admin_special=False)
        ],
    )
)
async def find_record(app: Ariadne, group: Group, message: MessageChain, source: Source):
    msg = message.display.strip()
    if At in message:
        at = message.get_first(At)

        if msg.find('-') != -1:
            List = msg.split('-')
            maxLen = eval(List[1])
        else:
            maxLen = 5

        saver = RecordSaver(group=group.id)
        backList = saver.find_QQ(at.target, maxLen)

        msgList = []
        if len(backList) != 0:
            member: Member = await app.get_member(group, at.target)
            msgList.append(member.name + ":\n")
            for i in range(0, len(backList)):
                msgList.extend(saver.to_MessageChain(backList[i]))
                msgList.append("\n")
            msgList.append("...")
        else:
            msgList.append("ta还没有入典语录哦")

        await safe_send_message(app, group, MessageChain(msgList), source)
    elif msg.find('-') != -1:
        List = msg.split('-')
        words = List[1]

        saver = RecordSaver(group=group.id)
        if len(List) < 3:
            records = saver.find_words(words)
        else:
            maxLen = eval(List[2])
            records = saver.find_words(words, maxLen)

        msgList = []
        if len(records) != 0:
            msgList.append("查询到记录如下:")
            for i in range(0, len(records)):
                member = await app.get_member(group, records[i]['QQ'])
                msgList.append('\n' + member.name + ":\n")
                msgList.extend(saver.to_MessageChain(docList=records[i]['docList']))
                msgList.append('\n')
        else:
            msgList.append("还没有这种语录哦")

        await safe_send_message(app, group, MessageChain(msgList), quote=source)
    else:
        txt = ["查询人物：查询语录@ta(-条数)\n\n", "查询内容：查询语录-待查询内容（-条数）\n"]
        await safe_send_message(app, group, MessageChain(txt), quote=source)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(
            FullMatch("清空语录").space(SpacePolicy.PRESERVE),
            "force" @ FullMatch("-f", optional=True).space(SpacePolicy.PRESERVE)
        )],
        decorators=[Permission.require_admin()]
    )
)
async def drop_collection(app: Ariadne, group: Group, sender: Member, force: MatchResult, source: Source):
    if force.matched:
        saver = RecordSaver(group=group.id)
        sta, msg = saver.drop()
        try:
            if sta == 0:
                await app.send_message(group, MessageChain("已清空所有语录！"))
            else:
                print("Error: ", msg)
                await app.send_message(group, MessageChain("出于某种原因，清空失败啦！"))
        except AccountMuted:
            if sta == 0:
                await app.send_friend_message(bot_Admin, MessageChain(f'群：{group.name}({group.id})\n已清空所有语录！'))
            else:
                print("Error: ", msg)
                await app.send_friend_message(bot_Admin, MessageChain(
                    f"群：{group.name}({group.id})\n出于某种原因，清空语录失败啦！"))
        return

    try:
        quote_message = await app.send_message(group, MessageChain("确定清空本群语录吗？Y/N"), quote=source)
    except AccountMuted:
        return

    async def waiter(g: Group, s: Member, mess: MessageChain) -> Optional[bool]:
        if g.id == group.id and s.id == sender.id:
            mess = mess.display.strip().casefold()
            if mess == 'y':
                return True
            elif mess == 'n':
                return False
            else:
                await app.send_message(group, MessageChain("请输入 Y 或 N"), quote=quote_message.messageId)
                # return None

    result = await FunctionWaiter(waiter, [GroupMessage]).wait(timeout=10)

    if result is None:
        await app.send_message(group, MessageChain("超时啦，不理你了！"))
    elif result:
        saver = RecordSaver(group=group.id)
        sta, msg = saver.drop()
        if sta == 0:
            await app.send_message(group, MessageChain("已清空所有语录！"))
        else:
            print("Error: ", msg)
            await app.send_message(group, MessageChain("出于某种原因，清空失败啦！"))
    else:
        await app.send_message(group, MessageChain("已取消！要善待已保存的语录哦。"))
