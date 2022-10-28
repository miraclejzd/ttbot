import os
from typing import List, Dict, Optional, Union

from graia.ariadne.entry import *
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import ParamMatch
from graia.ariadne.util.interrupt import FunctionWaiter

from utils import Permission, Forward_generator, safe_send_message

saya = Saya.current()
channel = Channel.current()

channel.name("modules_control")
channel.author("miraclejzd")

des = ["插件管理\n\n" +
       "命令格式： -m  option  (module)  (-f)",

       "option 可选项\n\n" +
       "loaded:  查看所有已加载插件\n" +
       "unloaded:  查看所有未加载插件\n" +
       "load:  加载插件\n" +
       "reload:  重载插件\n" +
       "unload:  卸载插件\n",

       "module 可选项\n\n" +
       "1、插件名 （可从-m  loaded/unloaded获取）\n" +
       "2、插件编号 （即插件前的数字序号）\n" +
       "3、*  表示全部内容"
       ]
channel.description("".join(txt for txt in des))


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage],
    inline_dispatchers=[
        Twilight([
            UnionMatch(['-m', '-module']),
            ParamMatch(optional=True) @ "option",
            ParamMatch(optional=True) @ "module",
            ArgumentMatch("-f", action="store_true", optional=True) @ "force"
        ])
    ]
))
async def modules_manager(
        app: Ariadne,
        option: RegexResult,
        module: RegexResult,
        force: ArgResult,
        event: Union[GroupMessage, FriendMessage]
):
    if not Permission(event).get():
        return

    option = option.result.display if option.matched else None
    module = module.result.display if module.matched else None
    force = force.matched
    result = await management(app, event, option, module, force)

    if isinstance(result, str):
        await safe_send_message(app, event, MessageChain(result))
    elif isinstance(result, list):
        fwd = Forward_generator(app.account, "ttbot", result)
        await safe_send_message(app, event, MessageChain(fwd))


def get_all_modules(ignore_dirs: List = None) -> List[str]:
    ignore = ["__init__.py", "__pycache__", "modules_control.py"]
    dirs = ["modules", "control"]
    if ignore_dirs:
        set_dirs = set(dirs) ^ set(ignore_dirs)
        dirs = list(set_dirs)
    modules = []

    for path in dirs:
        for module in os.listdir(path):
            if module in ignore:
                continue
            if os.path.isdir(module):
                modules.append(f"{path.replace('/', '.')}.{module}")
            else:
                modules.append(f"{path.replace('/', '.')}.{module.split('.')[0]}")
    return modules


def get_loaded_modules(ignore_dirs: List = None) -> List[str]:
    keys = list(saya.channels.keys())
    if ignore_dirs:
        for path in ignore_dirs:
            for module in os.listdir(path):
                if os.path.isdir(module):
                    p = f"{path.replace('/', '.')}.{module}"
                else:
                    p = f"{path.replace('/', '.')}.{module.split('.')[0]}"
                if p in keys:
                    keys.remove(p)
    else:
        if "control.modules_control" in keys:
            keys.remove("control.modules_control")
    return keys


def get_unloaded_modules() -> List[str]:
    loaded_modules = get_loaded_modules()
    all_modules = get_all_modules()
    return [module for module in all_modules if module not in loaded_modules]


def load_modules(modules: Union[str, List[str]]) -> Dict[str, Exception]:
    ignore = ["__init__.py", "__pycache__"]
    exceptions = {}
    if isinstance(modules, str):
        modules = [modules]
    with saya.module_context():
        for module in modules:
            if module in ignore:
                continue
            try:
                saya.require(module)
            except Exception as e:
                exceptions[module] = e
    return exceptions


def unload_modules(modules: Union[str, List[str]]) -> Dict[str, Exception]:
    exceptions = {}
    if isinstance(modules, str):
        modules = [modules]
    loaded_channels = get_loaded_channels()
    modules_to_unload = [module for module in modules if module in loaded_channels]
    with saya.module_context():
        for module in modules_to_unload:
            try:
                saya.uninstall_channel(loaded_channels[module])
            except Exception as e:
                exceptions[module] = e
    return exceptions


def reload_modules(modules: Union[str, List[str]]) -> Dict[str, Exception]:
    exceptions = {}
    if isinstance(modules, str):
        modules = [modules]
    loaded_channels = get_loaded_channels()
    modules_to_unload = [module for module in modules if module in loaded_channels]
    with saya.module_context():
        for module in modules_to_unload:
            try:
                saya.reload_channel(loaded_channels[module])
            except Exception as e:
                exceptions[module] = e
    return exceptions


def get_loaded_channels() -> Dict[str, Channel]:
    return saya.channels


def get_channel(module: str) -> Optional[Channel]:
    return saya.channels.get(module)


async def management(
        app: Ariadne,
        event: Union[GroupMessage, FriendMessage],
        option: str,
        module: Optional[str],
        force: bool
) -> Union[str, List[str], None]:
    # print("in management")
    if option is None:
        return des

    elif (option := option.strip()) == "loaded":
        ld_modules = get_loaded_modules()
        ld_modules.sort()

        back = []
        num = 0
        for mod in ld_modules:
            chan = get_channel(mod)
            num += 1
            back.append(str(num) + f"、{chan._name}\n\n插件描述: {chan._description}")
        return back

    elif option == "unloaded":
        uld_modules = get_unloaded_modules()
        uld_modules.sort()

        back = []
        num = 0
        for mod in uld_modules:
            num += 1
            back.append(str(num) + f"、{mod}")
        return back

    elif option == "load":
        if module is None:
            return f"没有输入待加载插件！！"

        module = module.strip()
        uld_modules = get_unloaded_modules()
        tar_modules: Union[str, List[str]]
        if module.isdigit():
            uld_modules.sort()
            ID = int(module) - 1
            if not (0 <= ID < len(uld_modules)):
                return f"错误的编号！请检查一下重新发送！"
            tar_modules = uld_modules[ID]
        else:
            if module == "*":
                tar_modules = uld_modules
            else:
                for mod in uld_modules:
                    if mod == module or mod.split('.')[-1] == module:
                        tar_modules = mod
                        break
                else:
                    return f"名称错误，或该插件已被加载，请检查一下重新发送！"

        async def waiter(event: Union[GroupMessage, FriendMessage], mess: MessageChain) -> Optional[bool]:
            if Permission(event).get():
                q_list = mess.get(Quote)
                if q_list and q_list[0].id != quote_message.messageId:
                    return None

                mess = mess.display.strip().casefold()
                if mess == 'y':
                    return True
                elif mess == 'n':
                    return False
                else:
                    await app.send_message(
                        event,
                        MessageChain(
                            Plain(f'请输入 Y / N')
                        ),
                        quote=quote_message.messageId
                    )

        if not force:
            quote_message = await app.send_message(event, MessageChain(f"确定要加载插件 {module} 吗? Y / N"))
            res = await FunctionWaiter(waiter, [GroupMessage, FriendMessage]).wait(timeout=60)
            if res is None:
                await app.send_message(
                    event,
                    MessageChain(Plain(f'超时啦，已取消~')),
                    quote=quote_message.messageId
                )
                return None
            elif not res:
                return f"已取消！"

        result = load_modules(tar_modules)
        if result:
            if module != "*":
                return f"发生错误啦: {result[tar_modules]}"
            else:
                await app.send_message(event, MessageChain(f"发生错误啦！"))
                back = []
                for key in result.keys():
                    back.append(f"{result[key]}")
                return back
        else:
            return f"加载成功！"

    elif option == "reload" or option == "unload":
        if module is None:
            return f"没有输入待加载插件！！"

        ld_modules = get_loaded_modules()
        tar_modules: Union[str, List[str]]
        if module.isdigit():
            ld_modules.sort()
            ID = int(module) - 1
            if not (0 <= ID < len(ld_modules)):
                return f"错误的编号！请检查一下重新发送！"
            tar_modules = ld_modules[ID]
        else:
            if module == "*":
                tar_modules = ld_modules
            else:
                for mod in ld_modules:
                    if mod == module or mod.split('.')[-1] == module:
                        tar_modules = mod
                        break
                else:
                    return f"名称错误，或该插件未被加载，请检查一下重新发送！"

        tar_load = "重载" if option == "reload" else "卸载"

        async def waiter(event: Union[GroupMessage, FriendMessage], mess: MessageChain) -> Optional[bool]:
            if Permission(event).get():
                q_list = mess.get(Quote)
                if q_list and q_list[0].id != quote_message.messageId:
                    return None

                mess = mess.display.strip().casefold()
                if mess == 'y':
                    return True
                elif mess == 'n':
                    return False
                else:
                    await app.send_message(
                        event,
                        MessageChain(
                            Plain(f'请输入 Y / N')
                        ),
                        quote=quote_message.messageId
                    )

        if not force:
            quote_message = await app.send_message(event,
                                                   MessageChain(f"确定要" + tar_load + f"插件 {module} 吗? Y / N"))
            res = await FunctionWaiter(waiter, [GroupMessage, FriendMessage]).wait(timeout=60)
            if res is None:
                await app.send_message(
                    event,
                    MessageChain(Plain(f'超时啦，已取消~')),
                    quote=quote_message.messageId
                )
                return None
            elif not res:
                return f"已取消！"

        result = reload_modules(tar_modules) if option == "reload" else unload_modules(tar_modules)
        if result:
            if module != "*":
                return f"发生错误啦: {result[tar_modules]}"
            else:
                await app.send_message(event, MessageChain(f"发生错误啦！"))
                back = []
                for key in result.keys():
                    back.append(f"{result[key]}")
                return back
        else:
            return tar_load + f"成功！"
