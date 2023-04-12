import aiohttp
from io import BytesIO
from typing import List
from pathlib import Path
from PIL import Image as IMG

from graia.ariadne.entry import *
from graia.saya import Channel
from graia.ariadne.message.parser.twilight import ParamMatch

from utils import Permission, safe_send_message

channel = Channel.current()

channel.name("petpet")
channel.author("miraclejzd")
channel.description("一个摸摸插件，可以对指定的群友进行抚慰")

FRAMES_PATH = Path.cwd() / "data" / "image" / "PetPetFrames"


@channel.use(ListenerSchema(
    listening_events=[GroupMessage],
    inline_dispatchers=[Twilight(
        UnionMatch("摸摸", "摸爆") @ "tp",
        ParamMatch() @ "tar_str",
    )],
    decorators=[Permission.require(channel.module)]
))
async def petpet(
        app: Ariadne, sender: Member, group: Group, tar_str: RegexResult, tp: RegexResult,
        source: Source
):
    ID = -1
    if tar_str.result.has(At):
        ID = tar_str.result.get_first(At).target
    else:
        tar_str = tar_str.result.display
        if tar_str == "我":
            ID = sender.id
        else:
            member_list: List[Member] = await app.get_member_list(group)
            member_list.append(await app.get_member(group, 2927503271))  # 添加bot进member_list

            for member in member_list:
                if member.name.find(tar_str) != -1:
                    ID = member.id
                    break

    if ID == -1:
        await app.send_message(group, MessageChain("我不知道你要摸谁~"))
    else:
        duration = 90 if tp.result.display == "摸摸" else 50
        await safe_send_message(
            app, group, MessageChain(Image(data_bytes=await make_gif(ID, duration))),quote=source,
            spare=Plain("图片被QQ吞啦，可能是头像迷惑性太强，被认为是H图.")
        )


frame_spec = [
    (27, 31, 86, 90),
    (22, 36, 91, 90),
    (18, 41, 95, 90),
    (22, 41, 91, 91),
    (27, 28, 86, 91),
]

frames = tuple(FRAMES_PATH.joinpath(f"frame{i}.png") for i in range(5))


# 生成函数（非数学意味）
async def make_frame(avatar, i):
    # 读入位置
    spec = list(frame_spec[i])
    # 读取手
    hand = IMG.open(frames[i])

    # 将头像放缩成所需大小
    avatar = avatar.resize(
        (int((spec[2] - spec[0]) * 1.15), int((spec[3] - spec[1]) * 1.15)), IMG.ANTIALIAS
    ).quantize()
    # 并贴到空图像上
    gif_frame = IMG.new("RGB", (112, 112), (255, 255, 255))
    gif_frame.paste(avatar, (spec[0], spec[1]))
    # 将手覆盖
    gif_frame.paste(hand, (0, 0), hand)

    return gif_frame


async def make_gif(member_id, duration=60):
    url = f"http://q1.qlogo.cn/g?b=qq&nk={str(member_id)}&s=640"
    gif_frames = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp = await resp.read()

    avatar = IMG.open(BytesIO(resp))

    # 生成每一帧
    for i in range(5):
        gif_frames.append(await make_frame(avatar, i))
    # 输出

    image = BytesIO()
    gif_frames[0].save(
        image,
        format="GIF",
        append_images=gif_frames[1:],
        save_all=True,
        duration=duration,
        loop=0,
        optimize=False,
    )
    return image.getvalue()
