import ujson
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Union, List

from graia.ariadne.entry import *
from graia.saya import Channel

from .Signer import Signer

channel = Channel.current()

channel.name("mys_daily_sign")
channel.author("miraclejzd")
channel.description("米游社每日签到（米游币，不包含原神签到）")


# @channel.use(SchedulerSchema(crontabify("0 6 * * *")))
# @channel.use(ListenerSchema(
#     listening_events=[GroupMessage]
# ))
async def mys_daily_sign():
    users = load_info()
    for user in users:
        await Signer(**user.dict()).sign()


class UserInfo(BaseModel):
    uid: Optional[int]
    cookie_string: Optional[str]
    notice_QQ: Optional[int]
    notice_Group: Optional[int]


def load_info(info_path: Optional[Union[Path, str]] = None) -> Optional[List[UserInfo]]:
    if not info_path:
        info_path = Path(__file__).parent / "info.json"
    elif isinstance(info_path, str):
        info_path = Path(info_path)
    if not info_path.is_file():
        raise ValueError(f"读取配置发生错误：未找到{info_path}")
    with open(info_path, "r", encoding="utf-8") as r:
        info = ujson.loads(r.read())
    return [UserInfo(**user) for user in info.get("users")]
