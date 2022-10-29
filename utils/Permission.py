from typing import Union, Optional

from graia.ariadne.entry import *
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
    def require(
            cls,
            module: str,
            admin_special: bool = True
    ) -> Depend:
        """
            依赖注入，获取该群组的插件权限。
            :paras
                module (str): 插件名.
                admin_special (bool): sender为admin用户是否无条件执行.
        """

        async def judge(evt: Union[MessageEvent, NudgeEvent]):
            if isinstance(evt, FriendMessage):
                return
            else:
                if isinstance(evt, NudgeEvent):
                    group = evt.group_id
                    friend = evt.friend_id
                else:
                    group = evt.sender.group.id
                    friend = evt.sender.id

                if admin_special and friend in config_data['AdminLists']:
                    return
                if group in config_data['GroupLists']:
                    if module in permission_data[group] and permission_data[group][module]:
                        return
                raise ExecutionStop()

        return Depend(judge)

    @classmethod
    def require_admin(cls) -> Depend:
        """
             依赖注入，获取是否有管理员权限。
        """
        async def judge(evt: Union[MessageEvent, NudgeEvent]):
            if isinstance(evt, NudgeEvent):
                Id = evt.friend_id
            else:
                Id = evt.sender.id

            if Id in config_data['AdminLists']:
                return
            raise ExecutionStop()

        return Depend(judge)
