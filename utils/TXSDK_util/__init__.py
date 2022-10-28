import json
import asyncio
import traceback
from enum import Enum
from loguru import logger

from tencentcloud.common import credential
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

from .settings import *


class TXSDK_response(Enum):
    async def async_get_resp(self, data):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_resp, data)

    def get_resp(self, data):
        info = INFO[self.value]
        try:
            cred = credential.Credential(user_data["secret_id"], user_data["secret_key"])
            http_profile = HttpProfile()
            http_profile.endpoint = info["endpoints"]

            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile
            client = info["client"](cred, "ap-guangzhou", client_profile)

            req = info["req"]
            req.from_json_string(json.dumps(data))
            try:
                func = getattr(client, info["resp_func"])
            except AttributeError:
                logger.error(traceback.format_exc())
                return f"client对象不存在方法 {info['resp_func']}"
            resp = func(req)
            return json.loads(resp.to_json_string())

        except TencentCloudSDKException as e:
            logger.error(traceback.format_exc())
            return {'error': str(e)}


class TXSDK(TXSDK_response):
    NLP = "NLP"
    text_recognize = "Text_recognize"
    image_enhance = "image_enhance"
    language_detect = "language_detect"
    text_translate = "text_translate"
