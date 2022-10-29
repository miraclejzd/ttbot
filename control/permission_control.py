from datetime import datetime
from typing import Union, Optional, List, Dict

from graia.ariadne.entry import *

from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import ParamMatch

from Config import config_data, permission_data, save_config
from control.modules_control import get_all_modules, get_loaded_modules, get_channel
from utils import Permission, Forward_generator, safe_send_message

channel = Channel.current()

channel.name("permission_control")
channel.author("miraclejzd")

des = ["插件权限管理\n\n" +
       "命令格式：\n -p  (ID)  option  (module)",

       "option 可选项\n\n" +
       "add_admin:  添加用户ID至AdminLists\n" +
       "add_group:  添加群ID至GroupLists\n" +
       "remove_admin:  将用户ID移除AdminLists\n" +
       "remove_group:  将群ID移除GroupLists\n" +
       "update:  更新群ID所有插件权限" +
       "info:  显示群ID插件权限信息\n" +
       "open:  开启群ID module 插件权限\n" +
       "close:  关闭群ID module 插件权限\n" +
       "switch:  切换群ID module 插件权限\n",

       "module 可选项\n\n" +
       "1、用户ID 或 群聊ID  \n" +
       "2、插件名（可从-m loaded/unloaded获取）\n" +
       "3、*  表示全部内容"
       ]
channel.description(des[0])


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage],
    inline_dispatchers=[
        Twilight([
            UnionMatch(['-p', '-permission']),
            RegexMatch(r"([1-9][0-9]{4,10})|(\*)", optional=True) @ "ID",
            ParamMatch(optional=True) @ "option",
            ParamMatch(optional=True) @ "module"
        ])
    ],
    decorators=[Permission.require_admin()]
))
async def permission_control(
        app: Ariadne,
        event: Union[GroupMessage, FriendMessage],
        ID: RegexResult,
        option: RegexResult,
        module: RegexResult,
        source: Source
):
    ID = ID.result.display if ID.matched else None
    module = module.result.display if module.matched else None
    option = option.result.display if option.matched else None
    result = await management(app, event, ID, option, module)

    if isinstance(result, str):
        await safe_send_message(app, event, MessageChain(result), quote=source)
    elif isinstance(result, list):
        fwd = Forward_generator(app.account, "ttbot", result)
        await safe_send_message(app, event, MessageChain(fwd))


def add(ID: int, Listname: str) -> Optional[str]:
    if Listname == "admin":
        if ID in config_data['AdminLists']:
            return f"用户 {ID} 已经是bot管理员啦！"
        else:
            config_data['AdminLists'].append(ID)
            save_config()
            return f"好消息！用户 {ID} 加入bot管理员籍！"
    elif Listname == "group":
        if ID in config_data['GroupLists']:
            return f"群 {ID} 已经在列表里！！"
        else:
            config_data['GroupLists'].append(ID)
            modules = get_all_modules(ignore_dirs=["control"])
            permission_data[ID] = {}
            for mod in modules:
                # mod = mod.split('.')[-1]
                permission_data[ID][mod] = True
            save_config()
            return f"已将群 {ID} 添加至列表！"


def remove(ID: int, Listname: str) -> Optional[str]:
    if Listname == "admin":
        if ID not in config_data['AdminLists']:
            return f"用户 {ID} 并不是bot管理员哦。"
        else:
            config_data['AdminLists'].remove(ID)
            save_config()
            return f"已将用户 {ID} 开除bot管理员籍！"
    elif Listname == "group":
        if ID not in config_data['GroupLists']:
            return f"群 {ID} 并不在列表里！！"
        else:
            config_data['GroupLists'].remove(ID)
            del permission_data[ID]
            save_config()
            return f"已将群 {ID} 开除！"


def update(g: int) -> Optional[str]:
    if g not in config_data['GroupLists']:
        return f"群 {g}不在列表内！"
    ld_modules = get_all_modules(ignore_dirs=["control"])
    perm_d: Dict = permission_data[g]

    set_ldm = set(ld_modules)
    set_perm = set(perm_d.keys())
    add_mod = list(set_ldm ^ (set_ldm & set_perm))
    del_mod = list(set_perm ^ (set_ldm & set_perm))

    for mod in add_mod:
        perm_d[mod] = True
    for mod in del_mod:
        perm_d.pop(mod)

    save_config()


def open(g: int, module: str) -> Optional[str]:
    if g not in config_data['GroupLists']:
        return f"群 {g}不在列表内！"
    elif module not in permission_data[g]:
        return f"不存在模块 {module}！"
    else:
        permission_data[g][module] = True
    save_config()


def close(g: int, module: str) -> Optional[str]:
    if g not in config_data['GroupLists']:
        return f"群 {g}不在列表内！"
    elif module not in permission_data[g]:
        return f"不存在模块 {module}！"
    else:
        permission_data[g][module] = False
    save_config()


def switch(g: int, module: str) -> Optional[str]:
    if g not in config_data['GroupLists']:
        return f"群 {g}不在列表内！"
    elif module not in permission_data[g]:
        return f"不存在模块 {module}！"
    else:
        permission_data[g][module] = not permission_data[g][module]
    save_config()


def info(g: int) -> Union[str, List[str]]:
    if g not in config_data['GroupLists']:
        return f"群 {g} 不在列表内！"

    perm_d: Dict = permission_data[g]
    keys = list(set(perm_d.keys()) & set(get_loaded_modules()))
    keys.sort()

    back = [f"群 {g} 插件权限如下:"]
    num = 0
    for key in keys:
        num += 1
        ch = get_channel(key)
        back.append(f"{str(num)}、{ch._name}\n\n插件描述: {ch._description if perm_d[key] else ' 关闭'}")
    return back


async def management(
        app: Ariadne,
        event: Union[GroupMessage, FriendMessage],
        ID: Optional[str],
        option: Optional[str],
        module: Optional[str],
) -> Union[str, List[str], None]:
    if option is None:
        return des

    elif (option := option.strip()) == "update":
        if ID is None:
            if isinstance(event, FriendMessage):
                return f"未指定群聊ID !"
            g = event.sender.group.id
        elif ID == "*":
            back = []
            for g in config_data['GroupLists']:
                res = update(g)
                if res:
                    back.append(res)
            if back:
                await safe_send_message(app, event, MessageChain(f"发生错误啦！"))
                return back
            else:
                return f"已成功更新 GroupLists所有群聊 插件权限！"
        elif ID.isdigit():
            g = int(ID)
        else:
            return f"ID错误！bot没办法解析指令哦~"

        res = update(g)
        return res if res else f"已更新 群聊{g} 插件权限！"

    elif ID is None and not isinstance(event, GroupMessage):
        return f"未指定 ID !"

    elif option in ["add_group", "remove_group"]:
        if ID is None:
            g = event.sender.group.id
        elif ID.isdigit():
            g = int(ID)
        else:
            return f"ID错误！bot没办法解析指令哦~"
        return add(g, "group") if option == "add_group" else remove(g, 'group')

    elif option in ["add_admin", "remove_admin"]:
        if ID is None:
            return f"缺少ID！bot没办法解析指令哦~"
        elif not ID.isdigit():
            return f"ID错误！bot没办法解析指令哦~"
        f = int(ID)
        return add(f, "admin") if option == "add_admin" else remove(f, 'admin')

    elif option == "info":
        if ID is None:
            g = event.sender.group.id
        elif ID.isdigit():
            g = int(ID)
        else:
            return f"ID错误！bot没办法解析指令哦~"

        res = info(g)
        return res

    elif option in ["open", "close", "switch"]:
        if module is None:
            return f"缺少module！bot没办法解析指令哦~"

        if ID is None:
            g = event.sender.group.id
        elif ID.isdigit():
            g = int(ID)
        else:
            return f"ID错误！bot没办法解析指令哦~"

        perm_d: Dict = permission_data[g]
        keys = list(set(perm_d.keys()) & set(get_loaded_modules()))
        tar_modules: List[str]

        if module.isdigit():
            keys.sort()
            ID = int(module) - 1
            if not (0 <= ID < len(keys)):
                return f"错误的编号！请检查一下重新发送！"
            tar_modules = [keys[ID]]
        else:
            if module == "*":
                tar_modules = keys
            else:
                for key in keys:
                    if module == key or module == key.split('.')[-1]:
                        tar_modules = [key]
                        break
                else:
                    return f"插件名称错误！请检查一下重新发送！"

        back = []
        for mod in tar_modules:
            if option == "open":
                res = open(g, mod)
            elif option == "close":
                res = close(g, mod)
            else:
                res = switch(g, mod)

            if res:
                if module != "*":
                    return f"发生错误啦：\n {res}"
                else:
                    back.append(res)
        if back:
            await safe_send_message(app, event, MessageChain(f"发生错误啦！"))
            return back
        else:
            return f"已成功更新群 {g} {'所有' if module == '*' else module}插件权限！"
