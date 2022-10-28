import json
import aiohttp
from enum import Enum
from typing import Dict, Union, Any

from Config import config_data
from .settings import *


class BDC_response(Enum):
    async def fetch_token(self) -> Dict:
        AK = config_data['BaiduCloud'][self.value]['API_key']
        SK = config_data['BaiduCloud'][self.value]['secret_key']
        url = token_url.format(AK, SK)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp = await resp.json()
                return resp

    async def get_resp(self, params) -> Union[str, Dict]:
        token_res = await self.fetch_token()
        if 'error' in token_res:
            return token_res["error_description"]
        token = token_res['access_token']
        url = resp_url[self.value] + f"?access_token={token}"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=params) as resp:
                resp = await resp.read()
                resp = json.loads(resp)
                return resp


class BDC(BDC_response):
    Image_audit = "Image_audit"
    Text_recognize = "Text_recognize"
