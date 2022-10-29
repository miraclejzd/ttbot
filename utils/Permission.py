from typing import Union, Optional

from graia.ariadne.entry import *
from Config import config_data, permission_data


class Permission:
    @classmethod
    def get(
            cls,
            evt: Union[MessageEvent, NudgeEvent, Friend, Group, Member],
            module: str,
            admin_special: bool = True
    ) -> bool:
        """
            显示判断，获取插件的使用权限.
            :params
                evt (Union[MessageEvent, NudgeEvent]): 对应Event事件.
                module (str): 插件名.
                admin_special (bool): sender为admin用户是否无条件执行.
            :returns
                (bool) 是否有权限
        """
        if isinstance(evt, (FriendMessage, Friend)):
            return True
        else:
            if isinstance(evt, NudgeEvent):
                group = evt.group_id
                friend = evt.friend_id
            elif isinstance(evt, MessageEvent):
                group = evt.sender.group.id
                friend = evt.sender.id
            elif isinstance(evt, Member):
                group = evt.group.id
                friend = evt.id
            else:
                group = evt.id
                friend = None

            if admin_special and friend in config_data['AdminLists']:
                return True
            if group in config_data['GroupLists'] and module in permission_data[group]:
                return permission_data[group][module]
            return False

    @classmethod
    def get_admin(
            cls,
            evt: Union[MessageEvent, NudgeEvent, Friend, Member]
    ) -> bool:
        """
            显示判断，获取是否有管理员权限。
            :params
                evt (Union[MessageEvent, NudgeEvent]): 对应Event事件.
            :returns
                (bool) 是否有权限

        """
        if isinstance(evt, NudgeEvent):
            Id = evt.friend_id
        elif isinstance(evt, MessageEvent):
            Id = evt.sender.id
        else:
            Id = evt.id
        return Id in config_data['AdminLists']

    @classmethod
    def require(
            cls,
            module: str,
            admin_special: bool = True
    ) -> Depend:
        """
            依赖注入，获取插件的使用权限。
            :paras
                module (str): 插件名.
                admin_special (bool): sender为admin用户是否无条件执行.
            :returns
                (Depend) 是否有权限
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
            :returns
                (Depend) 是否有权限
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
