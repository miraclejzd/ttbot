from graia.ariadne.event.message import GroupMessage, TempMessage, FriendMessage

from typing import Union


def get_game_id(ev: Union[GroupMessage, TempMessage, FriendMessage]) -> int:
    if isinstance(ev, GroupMessage):
        return hash((ev.sender.group.id, None))
    elif isinstance(ev, TempMessage):
        return hash((ev.sender.group.id, ev.sender.id))
    else:
        return hash((None, ev.sender.id))
