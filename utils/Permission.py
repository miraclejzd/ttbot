from typing import Union, Optional

from graia.ariadne.model import Group, Friend, Member
from graia.ariadne.event.message import MessageEvent, GroupMessage, FriendMessage, TempMessage
from Config import config_data, permission_data


class Permission:
    group: Optional[int] = None
    friend: Optional[int] = None

    def __init__(self,
                 target: Optional[Union[MessageEvent, Group, Friend, Member]] = None,
                 group_id: Optional[int] = None,
                 friend_id: Optional[int] = None
                 ):
        if target:
            if isinstance(target, Group):
                self.group = target.id
            elif isinstance(target, (Member, Friend)):
                self.friend = target.id
            elif isinstance(target, (GroupMessage, TempMessage)):
                self.group = target.sender.group.id
                self.friend = target.sender.id
            elif isinstance(target, FriendMessage):
                self.friend = target.sender.id
        else:
            self.group = group_id
            self.friend = friend_id

    def get(self, module: Optional[str] = None) -> bool:
        if self.friend in config_data['AdminLists']:
            return True

        if (g := self.group) in config_data['GroupLists']:
            if module in permission_data[g]:
                return permission_data[g][module]

        return False

    @classmethod
    def module(cls, name: str):
        pass
