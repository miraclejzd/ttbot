import asyncio
from loguru import logger
from datetime import datetime
from typing import List, Union, Optional
from graia.ariadne.entry import *
from graia.ariadne.message.chain import MessageContainer
from graia.ariadne.exception import RemoteException

"""
    转发消息生成器
    
    :param
        tar (int):    发送者ID
        name (str):   发送者昵称
        msgList (List[Union[MessageChain, Element, str, List]]):    消息列表
    
    :return
        Forward:    生成的转发消息
"""


def Forward_generator(tar: int, name: str, msgList: List[Union[MessageChain, Element, str, List]]) -> Forward:
    fwd_list = []
    for msg in msgList:
        if isinstance(msg, MessageChain):
            info = msg
        elif isinstance(msg, Element) or isinstance(msg, str):
            info = MessageChain(msg)
        else:
            info = MessageChain(Forward_generator(tar, name, msg))

        fwd_list.append(
            ForwardNode(
                target=tar,
                name=name,
                time=datetime.now(),
                message=info
            )
        )

    return Forward(fwd_list)


"""
    再封装的Ariadne.send_message
        1. 捕捉禁言的Exception;
        2. 出现消息被吞的情况，将发送spare消息。
    
    :param
        target (Union[MessageEvent, Group, Friend, Member]): 消息发送目标.
        message (MessageContainer): 要发送的消息链.
        quote (Union[bool, int, Source, MessageChain]): 若为布尔类型, 则会尝试通过传入对象解析要回复的消息, \
            否则会视为 `messageId` 处理.
        spare (Union[None, Plain, str]): 若消息被吞，则发送spare消息。
        recall (Optional[int])：经过多少秒后撤回，默认为None
"""


async def safe_send_message(
        app: Ariadne,
        target: Union[MessageEvent, Group, Friend, Member],
        message: MessageContainer,
        quote: Union[bool, int, Source, MessageChain] = False,
        spare: Union[None, Plain, str] = None,
        recall: Union[None, int] = None
):
    try:
        msgID = await app.send_message(target, message, quote=quote)
        if msgID.id != -1:
            if recall:
                await asyncio.sleep(min(recall, 120))
                await app.recall_message(msgID)
        else:
            logger.warning(f"原消息没有发出去: {message.display} ")
            if spare:
                return await app.send_message(target, MessageChain(spare), quote=quote)
        return msgID

    except AccountMuted:
        if isinstance(target, MessageEvent):
            group = target.sender.group
        elif isinstance(target, Group):
            group = target
        else:
            group = target.group

        logger.warning(f'Bot 在群组  {group.name} ({group.id})  被禁言！')

    except RemoteException as e:
        logger.warning(f'send_message 出现错误: {str(e)}')
        if spare:
            return await app.send_message(target, MessageChain(spare), quote=quote)
        else:
            return await app.send_message(target, MessageChain(f'发送消息出现错误: \n{str(e)}'), quote=quote)


"""
    再封装的Ariadne.send_group_message
        1. 捕捉禁言的Exception;
        2. 出现消息被吞的情况，将发送spare消息。

    :param
        target (Union[Group, Member, int]): 消息发送目标.
        message (MessageContainer): 要发送的消息链.
        quote (Union[bool, int, Source, MessageChain]): 若为布尔类型, 则会尝试通过传入对象解析要回复的消息, \
            否则会视为 `messageId` 处理.
        spare (Union[None, Plain, str]): 若消息被吞，则发送spare消息。
        recall (Optional[int])：经过多少秒后撤回，默认为None
"""


async def safe_send_group_message(
        app: Ariadne,
        target: Union[Group, Member, int],
        message: MessageContainer,
        quote: Optional[Union[Source, int, MessageChain]] = None,
        spare: Union[None, Plain, str] = None,
        recall: Optional[int] = None
):
    try:
        msgID = await app.send_group_message(target, message, quote=quote)
        if msgID.id != -1:
            if recall:
                await asyncio.sleep(min(recall, 120))
                await app.recall_message(msgID)
        else:
            logger.warning(f"原消息没有发出去: {message.display} ")
            if spare:
                return await app.send_group_message(target, MessageChain(spare), quote=quote)
        return msgID

    except AccountMuted:
        if isinstance(target, Group):
            group = target
        elif isinstance(target, Member):
            group = target.group
        else:
            group = await app.get_group(target)
        logger.warning(f'Bot 在群组  {group.name} ({group.id})  被禁言！')

    except RemoteException as e:
        logger.warning(f'send_message 出现错误: {str(e)}')
        if spare:
            return await app.send_message(target, MessageChain(spare), quote=quote)
        else:
            return await app.send_message(target, MessageChain(f'发送消息出现错误: \n{str(e)}'), quote=quote)
