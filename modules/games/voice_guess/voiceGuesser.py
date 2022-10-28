import random
import aiohttp
import contextlib
from lxml import etree
from typing import List

from modules.genshin.genshin_info_guide.query_char import get_char_data

char_id_url = "https://api-static.mihoyo.com/common/blackboard/ys_obc/v1/home/content/list?app_sn=ys_obc&channel_id=189"
voice_list_url = 'https://api-static.mihoyo.com/common/blackboard/ys_obc/v1/content/info?app_sn=ys_obc&content_id={}'

char_id_dic = {}


async def get_voice_dict():
    global char_id_dic
    async with aiohttp.ClientSession() as session:
        async with session.get(char_id_url) as resp:
            resp = await resp.json()
    if resp["retcode"] != 0:
        raise ValueError("原神角色语音获取失败！")
    id_data = resp["data"]["list"][0]["children"][0]["list"]
    char_id_dic = {c["title"]: c["content_id"] for c in id_data}


class voiceGuesser:
    lang: str
    char_name: str
    Ans: List[str]
    info: str
    data_url: str

    def __init__(
            self,
            lang: str
    ):
        self.lang = lang
        char_data = get_char_data()
        self.char_name = random.sample(char_data.keys(), 1)[0]
        while "旅行者" in self.char_name:
            self.char_name = random.sample(char_data.keys(), 1)[0]
        self.Ans = []
        for alias in char_data[self.char_name]["alias"]:
            self.Ans.append(alias)

    async def init(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(voice_list_url.format(char_id_dic[self.char_name])) as resp_voi:
                data = await resp_voi.json()

        if data['retcode'] != 0:
            raise ValueError("获取角色语音请求失败"+data["message"])
        data = data['data']['content']['contents'][2]

        html = etree.HTML(data['text'])
        for i in range(1, 5):
            voice_type = html.xpath(
                f'//*[@class="obc-tmpl__part obc-tmpl-character obc-tmpl__part--voiceTab obc-tmpl__part--align-banner"]/ul[1]/li[{i}]/text()')[
                0]
            voice_type = voice_type[0] if voice_type[0] != '汉' else '中'
            if voice_type == self.lang:
                voice_list = html.xpath(
                    f'//*[@class="obc-tmpl__part obc-tmpl-character obc-tmpl__part--voiceTab obc-tmpl__part--align-banner"]/ul[2]/li[{i}]/table[2]/tbody/tr')
                voice = random.choice(voice_list)
                with contextlib.suppress(IndexError):
                    self.info = voice.xpath('./td/text()')[0]
                    self.data_url = voice.xpath('./td/div/div/audio/source/@src')[0]
                break
