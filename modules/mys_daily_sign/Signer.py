import json
import asyncio
import aiohttp
from loguru import logger
from typing import Optional, NoReturn, List

from graia.ariadne.entry import *

from .utils import *


class Signer(object):
    def __init__(
            self,
            uid: Optional[int] = None,
            cookie_string: Optional[str] = None,
            notice_QQ: Optional[int] = None,
            notice_Group: Optional[int] = None,
            stuid: Optional[str] = None,
            stoken: Optional[str] = None
    ):
        if not cookie_string:
            raise ValueError("Cookie是必须要的！")
        self.uid = uid
        self.cookie = cookie_string
        self.notice_QQ = notice_QQ
        self.notice_Group = notice_Group
        self.login_ticket = cookie_str2dict(cookie_string)["login_ticket"]
        self.stuid = stuid
        self.stoken = stoken

    async def get_stuid(self) -> Optional[str]:
        if self.stuid:
            return self.stuid

        print("login_ticket:", self.login_ticket)
        async with aiohttp.ClientSession() as session:
            async with session.get(url=bbs_Cookie_url.format(self.login_ticket)) as resp:
                res = await resp.json()
            print("res:", res)
            if "成功" in res["data"]["msg"]:
                logger.success(f'uid: <{self.uid}> 成功获取stuid！')
                return res["data"]["cookie_info"]["account_id"]
            else:
                logger.error(f'uid: <{self.uid}> 获取stuid失败！')
                raise ValueError("获取stuid失败！")

    async def get_stoken(self) -> Optional[str]:
        if self.stoken:
            return self.stoken

        if not self.stuid:
            logger.error(f'uid: <{self.uid}> 获取stoken失败，因为不存在stuid！')
            return None

        async with aiohttp.ClientSession() as session:
            async with session.get(url=bbs_Cookie_url2.format(self.login_ticket, self.stuid)) as resp:
                res = await resp.json()
        # print("res:", res)
        if res["data"]["list"][0].get("token"):
            logger.success(f'uid: <{self.uid}> 成功获取stoken！')
            return res["data"]["list"][0]["token"]
        else:
            logger.error(f'uid: <{self.uid}> 获取stoken失败！')
            raise ValueError("获取stoken失败！")

    # 米游社-原神板块的签到
    async def genshin_sign(self):
        uid = self.uid
        server_id = "cn_qd01" if str(uid)[0] == "5" else "cn_gf01"
        try:
            cookie = self.cookie
            headers['DS'] = get_ds(web=True)
            headers['Referer'] = 'https://webstatic.mihoyo.com/bbs/event/signin-ys/index.html?bbs_auth_required=true' \
                                 f'&act_id={genshin_Act_id}&utm_source=bbs&utm_medium=mys&utm_campaign=icon'
            headers['Cookie'] = cookie
            headers['x-rpc-device_id'] = get_device_id(cookie)
            async with aiohttp.ClientSession() as session:
                async with session.post(url=genshin_Signurl, headers=headers,
                                        json={"act_id": genshin_Act_id, "uid": uid, "region": server_id}) as resp:
                    data = await resp.json()
            if not data or data["message"] != "OK":
                logger.error(f"uid: <{self.uid}> 原神签到发生错误: {data}")
                raise ValueError(f"原神签到发生错误: {data}")
            else:
                logger.success(f"uid: <{self.uid}> 原神板块签到成功")

        except Exception as e:
            logger.error(f"米游社签到发生错误 UID：{uid} {type(e)}：{e}")
            raise ValueError(f"米游社签到发生错误 UID：{uid} {type(e)}：{e}")

    # 米游社评论区签到、看贴、点赞、分享
    async def mys_sign(self):
        uid = self.uid
        cookie = self.cookie
        stuid = self.stuid = await self.get_stuid()
        stoken = self.stoken = await self.get_stoken()
        mys_signer = Mys_Signer(uid=uid, stuid=stuid, stoken=stoken, cookie=cookie)

        await mys_signer.refresh_list()
        await mys_signer.sign()
        await mys_signer.read_posts()
        await mys_signer.like_posts()
        await mys_signer.share_post()

    # 原神+米游社签到
    async def sign(self):
        try:
            # await self.genshin_sign()
            await self.mys_sign()
            await self.notice()
        except Exception as e:
            logger.error(e)
            await self.notice(f"原神签到失败，原因:{e}")

    async def notice(self, msg: str = None):
        if not msg:
            msg = "米游社签到成功"
        if self.notice_Group:
            await Ariadne.current().send_temp_message(
                group=self.notice_Group,
                target=self.notice_QQ,
                message=MessageChain(msg)
            )
        else:
            await Ariadne.current().send_friend_message(self.notice_QQ, message=MessageChain(msg))


class Mys_Signer(object):
    def __init__(self, uid: int, stuid: str, stoken: str, cookie: str) -> NoReturn:
        self.uid = uid
        self.headers = {
            "DS": get_ds(web=False),
            "cookie": f'stuid={stuid};stoken={stoken}',
            "x-rpc-client_type": mihoyobbs_Client_type,
            "x-rpc-app_version": mihoyobbs_Version,
            "x-rpc-sys_version": "6.0.1",
            "x-rpc-channel": "miyousheluodi",
            "x-rpc-device_id": get_device_id(cookie=cookie),
            "x-rpc-device_name": random_text(random.randint(1, 10)),
            "x-rpc-device_model": "Mi 10",
            "Referer": "https://app.mihoyo.com",
            "Host": "bbs-api.mihoyo.com",
            "User-Agent": "okhttp/4.8.0"
        }
        self.postsList = None

    # 创建Mys_Signer必须要执行refresh_list()！！
    async def refresh_list(self):
        self.postsList = await self.get_list()

    # 获取帖子列表
    async def get_list(self) -> List:
        temp_list = []
        async with aiohttp.ClientSession() as session:
            async with session.get(url=bbs_List_url.format(mihoyobbs_List_Use[0]["forumId"]),
                                   headers=self.headers) as resp:
                data = await resp.json()
                data = data["data"]["list"]

        for n in range(5):
            r_l = random.choice(data)
            while r_l["post"]["subject"] in str(temp_list):
                r_l = random.choice(data)
            temp_list.append([r_l["post"]["post_id"], r_l["post"]["subject"]])

        logger.info("已获取{}个帖子".format(len(temp_list)))
        return temp_list

    # 评论区签到
    async def sign(self):
        header = {}
        header.update(self.headers)
        for i in mihoyobbs_List_Use:
            header["DS"] = get_ds2("", json.dumps({"gids": i["id"]}))
            async with aiohttp.ClientSession() as session:
                async with session.post(url=bbs_Sign_url, json={"gids": i["id"]}, headers=header) as resp:
                    data = await resp.json()
            if "err" not in data["message"]:
                logger.info(str(i["name"] + data["message"]))
                await asyncio.sleep(random.randint(2, 8))
            else:
                logger.error(f"签到失败，uid: <{self.uid}> 的cookie可能已过期，请重新设置cookie。")
                raise ValueError('Cookie过期')

    # 看帖子
    async def read_posts(self):
        for i in range(4):
            async with aiohttp.ClientSession() as session:
                async with session.get(url=bbs_Detail_url.format(self.postsList[i][0]), headers=self.headers) as resp:
                    data = await resp.json()
            if data["message"] == "OK":
                logger.debug(f"uid: <{self.uid}>" + "看帖：{} 成功".format(self.postsList[i][1]))
            await asyncio.sleep(random.randint(2, 8))

    # 点赞帖子
    async def like_posts(self):
        for i in range(5):
            async with aiohttp.ClientSession() as session:
                async with session.post(url=bbs_Like_url, headers=self.headers,
                                        json={"post_id": self.postsList[i][0], "is_cancel": False}) as resp:
                    data = await resp.json()
            if data["message"] == "OK":
                logger.debug(f"uid: <{self.uid}>" + "点赞：{} 成功".format(self.postsList[i][1]))
            else:
                logger.warning(f"uid: <{self.uid}>  点赞出现问题： {data}")
            await asyncio.sleep(random.randint(2, 8))

    # 分享帖子
    async def share_post(self) -> NoReturn:
        for i in range(3):
            async with aiohttp.ClientSession() as session:
                async with session.get(url=bbs_Share_url.format(self.postsList[0][0]), headers=self.headers) as resp:
                    data = await resp.json()
            if data["message"] == "OK":
                logger.debug(f"uid: <{self.uid}>" + "分享：{} 成功".format(self.postsList[0][1]))
                logger.info("分享任务执行成功！")
                await asyncio.sleep(random.randint(2, 8))
                return
            else:
                logger.debug(f"uid: <{self.uid}> 分享帖子执行失败，即将执行第{i + 2}次")
                await asyncio.sleep(random.randint(2, 8))
        logger.error(f"uid: <{self.uid}> 分享帖子失败！")
