import time
import base64
import traceback
import httpx

import numpy as np
from io import BytesIO
from asyncio import Lock
from typing import Union
from pathlib import Path
from PIL import Image as IMG
from loguru import logger

from graia.ariadne.entry import *
from graia.ariadne.util.interrupt import FunctionWaiter
from graia.saya.channel import Channel

try:
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet

    enable = True
except ImportError:
    enable = False

from utils import Permission, safe_send_message, TXSDK

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
loop = bcc.loop

channel.name("super_resolution")
channel.author("miraclejzd")
channel.description("图片超分辨率处理，发送 /超分 进行使用。")

events = Union[GroupMessage, FriendMessage, TempMessage]

max_size = 2073600
mutex = Lock()
processing = False


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage, TempMessage],
    inline_dispatchers=[Twilight(
        FullMatch("/超分")
    )]
))
async def super_resolution(app: Ariadne, event: events, message: MessageChain, source: Source):
    if not Permission(event).get(channel.module):
        return

    if not enable:
        return await safe_send_message(app, event, MessageChain("超分功能未开启！"), quote=source)

    global processing
    if processing:
        return await safe_send_message(app, event, MessageChain("有任务正在处理中，请稍后重试"), quote=source)

    async def waiter(evt: events, mess: MessageChain):
        if judge(event, evt):
            if mess.has(Image):
                return mess.get_first(Image)
            else:
                return False

    image: Union[None, Image, bool]
    if Quote in message:
        quote = message.get_first(Quote)
        try:
            ori_evt: MessageEvent
            if isinstance(event, FriendMessage):
                ori_evt = await app.get_message_from_id(quote.id, event.sender)
            else:
                ori_evt = await app.get_message_from_id(quote.id, event.sender.group)
        except Exception as e:
            logger.error(str(e))
            return await safe_send_message(app, event, MessageChain(f"出现了一点错误哦:\n{str(e)}"))
        ori_msg = ori_evt.message_chain
        image = ori_msg.get_first(Image) if ori_msg.has(Image) else None
    else:
        await safe_send_message(app, event, MessageChain("请在30s内发送要处理的图片."), quote=source)
        image = await FunctionWaiter(waiter, [GroupMessage, FriendMessage, TempMessage]).wait(30)

    if image is None:
        return await safe_send_message(app, event, MessageChain("图片等待超时，进程退出."), quote=source)
    elif not image:
        return await safe_send_message(app, event, MessageChain("未检测到图片，请重新发送，进程退出."), quote=source)

    if processing:
        return await safe_send_message(app, event, MessageChain("有任务正在处理中，请稍后重试"), quote=source)
    async with mutex:
        processing = True
    await safe_send_message(app, event, MessageChain("已收到图片，正在处理."), quote=source)
    try:
        await safe_send_message(
            app,
            event,
            await get_super_resolution(await image.get_bytes()),
            quote=source
        )
    except RuntimeError as e:
        async with mutex:
            processing = False
        # logger.error(e)
        logger.error(traceback.format_exc())
        await safe_send_message(app, event, MessageChain(str(e)), quote=source)


async def get_super_resolution(img_data: bytes) -> MessageChain:
    global processing

    start = time.time()
    image = IMG.open(BytesIO(img_data))
    image_size = image.size[0] * image.size[1]

    resize = False
    # 重载图片大小
    if image_size > max_size:
        resize = True
        length = 1
        for b in str(max_size / image_size).split(".")[1]:
            if b == "0":
                length += 1
            else:
                break
        magnification = round(max_size / image_size, length + 1)
        image = image.resize(
            (round(image.size[0] * magnification), round(image.size[1] * magnification))
        )

    result = await by_local(image)
    # result = await by_api(image)
    async with mutex:
        processing = False

    return MessageChain(
        [
            Plain(text=f"超分完成！处理用时：{round(time.time() - start, 2)}s\n"),
            Plain(text="由于像素过大，图片已进行缩放，结果可能不如原图片清晰\n" if resize else ""),
            # Image(data_bytes=result),
            Image(data_bytes=result)
        ]
    )


async def by_local(image: IMG.Image) -> bytes:
    UpSampler = RealESRGANer(
        scale=4,
        model_path=str(
            Path(__file__).parent.joinpath("RealESRGAN_x4plus_anime_6B.pth")
        ),
        model=RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=6,
            num_grow_ch=32,
            scale=4,
        ),
        tile=100,
        tile_pad=10,
        pre_pad=0,
        half=False,
    )

    result = BytesIO()
    # noinspection PyTypeChecker
    image_array: np.ndarray = np.array(image)
    output, _ = await loop.run_in_executor(None, UpSampler.enhance, image_array, 2)
    img = IMG.fromarray(output)
    img.save(result, format="PNG")  # format: PNG / JPEG
    del UpSampler
    return result.getvalue()


async def by_api(image: IMG.Image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    b64_str = base64.b64encode(buffer.getvalue()).decode()

    # gradio-demo:
    url = "https://akhaliq-real-esrgan.hf.space/api/predict/"
    body = {
        "fn_index": 0,
        "data": [f"image/png;base64,{b64_str}", "anime"],
        "session_hash": "rcb1j9p7lql"
    }
    async with httpx.AsyncClient() as session:
        resp = (await session.post(url, json=body, timeout=100, follow_redirects=True)).json()
    resp_b64_str = resp['data'][0].split("base64,")[1]
    result = BytesIO()
    img = IMG.open(BytesIO(base64.b64decode(resp_b64_str)))
    img.save(result, format='PNG')
    return result.getvalue()
    # return base64.b64decode(b64_str)

    # # 腾讯SDK:
    # resp = await TXSDK.image_enhance.async_get_resp({"ImageBase64": b64_str})
    # if "error" in resp:
    #     return buffer.getvalue()
    # else:
    #     resp_b64_str = resp["EnhancedImage"]
    #     result = BytesIO()
    #     img = IMG.open(BytesIO(base64.b64decode(resp_b64_str)))
    #     img.save(result, format='PNG')
    #     return result.getvalue()
    #     # return base64.b64decode(resp_b64_str)


def judge(evt1: events, evt2: events) -> bool:
    if type(evt1) != type(evt2):
        return False

    if isinstance(evt1, FriendMessage):
        return evt1.id == evt2.id
    else:
        return evt1.sender == evt2.sender and evt1.sender.group == evt2.sender.group
