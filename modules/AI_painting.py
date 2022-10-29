import re
import time
import httpx
from typing import Union
from loguru import logger

from graia.ariadne.entry import *
from graia.saya.channel import Channel

from utils import Permission, safe_send_message, get_context

channel = Channel.current()

channel.name("AI_painting")
channel.author("miraclejzd")
channel.description("AI画图插件，发送 /画图 xxx 即可")

URL = "https://api.smoe.me/api/access"


@channel.use(ListenerSchema(
    listening_events=[GroupMessage, FriendMessage, TempMessage],
    inline_dispatchers=[Twilight(
        FullMatch("/"),
        UnionMatch("t2i", "画图", "绘图"),
        ArgumentMatch("-n", "-N", action="store_true", optional=True) @ "neg",
        WildcardMatch().flags(re.S) @ "tags"
    )],
    decorators=[Permission.require(channel.module)]
))
async def AI_painting(
        app: Ariadne, tags: RegexResult, neg: ArgResult, source: Source,
        evt: Union[GroupMessage, FriendMessage, TempMessage]
):
    tags = tags.result.display.strip() if tags.matched else ""
    if len(tags) == 0:
        return await safe_send_message(app, evt, MessageChain("需要有一些描述词才可以开始绘画哦~"), source)

    try:
        st = time.time()
        b64_data = await get_img_b64_api(tags, neg=neg.matched)
        await safe_send_message(
            app, evt, quote=source,
            message=MessageChain(
                Image(base64=b64_data),
                Plain(f"用时: {round(time.time() - st, 2)}s\n")
            ),
        )
    except Exception as e:
        logger.error(e)
        await safe_send_message(app, evt, MessageChain(f"出现错误：\n{str(e)}"), source)


async def get_img_b64_api(tags: str, neg: bool):
    url = "https://api.smoe.me/api/access/api/predict"

    body = {
        "fn_index": 12,
        "data": [tags,
                 "lowers, bad anatomy, bad hands, text, error, missing fingers, "
                 "extra digit, fewer digits, cropped, worst quality, low quality, "
                 "normal quality, jpeg artfacts, signature, watermark, username, blurry, "
                 "bad feet, multiple breasts, (mutated hands and fingers:1.5 ), (long body "
                 ":1.3), (mutation, poorly drawn :1.2) , black-white, bad anatomy, "
                 "liquid body, liquid tongue, disfigured, malformed, mutated, anatomical "
                 "nonsense, text font ui, error, malformed hands, long neck, blurred, "
                 "lowers, lowres, bad anatomy, bad proportions, bad shadow, uncoordinated "
                 "body, unnatural body, fused breasts, bad breasts, huge breasts, "
                 "poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, "
                 "missing breasts, huge haunch, huge thighs, huge calf, bad hands, "
                 "fused hand, missing hand, disappearing arms, disappearing thigh, "
                 "disappearing calf, disappearing legs, fused ears, bad ears, poorly drawn "
                 "ears, extra ears, liquid ears, heavy ears, missing ears, fused animal "
                 "ears, bad animal ears, poorly drawn animal ears, extra animal ears, "
                 "liquid animal ears, heavy animal ears, missing animal ears, text, ui, "
                 "error, missing fingers, missing limb, fused fingers, one hand with more "
                 "than 5 fingers, one hand with less than 5 fingers, one hand with more "
                 "than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, "
                 "fused digit, missing digit, bad digit, liquid digit, colorful tongue, "
                 "black tongue, cropped, watermark, username, blurry, JPEG artifacts, "
                 "signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, "
                 "extra feet, bad feet, poorly drawn feet, fused feet, missing feet, "
                 "extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn "
                 "shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, "
                 "poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, "
                 "big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, "
                 "big face, long face, bad eyes, fused eyes poorly drawn eyes, extra eyes, "
                 "malformed limbs, more than 2 nipples, missing nipples, different nipples, "
                 "fused nipples, bad nipples, poorly drawn nipples, black nipples, "
                 "colorful nipples, gross proportions. short arm, (((missing arms))), "
                 "missing thighs, missing calf, missing legs, mutation, duplicate, morbid, "
                 "mutilated, poorly drawn hands, more than 1 left hand, more than 1 right "
                 "hand, deformed, (blurry), disfigured, missing legs, extra arms, "
                 "extra thighs, more than 2 thighs, extra calf, fused calf, extra legs, "
                 "bad knee, extra knee, more than 2 legs, bad tails, bad mouth, "
                 "fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, "
                 "too long tongue, black tongue, big mouth, cracked mouth, bad mouth, "
                 "dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, "
                 "fused cloth, poorly drawn cloth, bad pantie, yellow teeth, thick lips, "
                 "bad cameltoe, colorful cameltoe, bad asshole, poorly drawn asshole, "
                 "fused asshole, missing asshole, bad anus, bad pussy, bad crotch, "
                 "bad crotch seam, fused anus, fused pussy, fused anus, fused crotch, "
                 "poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, "
                 "poorly drawn crotch, poorly drawn crotch seam, bad thigh gap, "
                 "missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh "
                 "gap, poorly drawn anus, bad collarbone, fused collarbone, "
                 "missing collarbone, liquid collarbone, strong girl, obesity, "
                 "worst quality, low quality, normal quality, liquid tentacles, "
                 "bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, "
                 "missing clit, bad clit, fused clit, colorful clit, black clit, "
                 "liquid clit, QR code, bar code, censored, safety panties, "
                 "safety knickers, beard, furry ,pony, pubic hair, mosaic, excrement, "
                 "faeces, shit, futa, testis" if neg else "",
                 "None", "None", 20, "Euler a", False, False, 1, 1, 7, -1, -1, 0, 0, 0,
                 False, 512, 512, False, False, 0.7, "None", False, False, None, "", "Seed", "", "Steps", "",
                 True, False, None, "", ""],
        "session_hash": "6vlpnoiyejh"
    }

    async with httpx.AsyncClient() as session:
        for _ in range(3):
            try:
                resp = (await session.post(url, json=body, timeout=100, follow_redirects=True)).json()
                pic = resp["data"][0][0].replace("data:image/png;base64,", "", 1)
                return pic
            except Exception:
                pass
        resp = (await session.post(url, json=body, timeout=100, follow_redirects=True)).json()
        pic = resp["data"][0][0].replace("data:image/png;base64,", "", 1)
        return pic


async def get_img_b64_browser(tags: str):
    context = await get_context()
    page = await context.new_page()

    url = URL
    await page.goto(url, timeout=60000)

    await page.fill("#txt2img_prompt [data-testid=\"textbox\"]", tags)
    await page.locator("#txt2img_generate").click(timeout=60000)
    src = await page.locator("#txt2img_gallery button > img").get_attribute("src")
    b64_data = src.split("base64,")[1]
    await page.close()
    await context.close()

    return b64_data
