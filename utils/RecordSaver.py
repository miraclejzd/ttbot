from sshtunnel import SSHTunnelForwarder
import pymongo
import datetime
import random
from typing import Dict, Optional

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image, Face

# client = pymongo.MongoClient("localhost", 27017)
server = SSHTunnelForwarder(
    "43.143.15.88",
    ssh_username="Administrator",
    ssh_password="jzd6341149jzd.",
    remote_bind_address=('127.0.0.1', 27017)
)

server.start()

client = pymongo.MongoClient("127.0.0.1", server.local_bind_port)
db = client['Database']


def get_time():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class RecordSaver(object):
    """创建实例"""
    '''参数：
            group: 群号 or None
            friend: QQ号 or None
        
        若为群聊聊天记录，则group不为None
    '''

    def __init__(self, group=None, friend=None):
        if group is not None:
            self.collection = db['Group-' + str(group)]
        elif friend is not None:
            self.collection = db['Friend-' + str(friend)]

    '''添加QQ号的聊天记录'''
    ''' 参数：
            QQ: QQ号
            docList:    聊天记录列表，['type1', 'doc1', 'type2', 'doc2' ...]
            time:   时间
    
    
        返回值：
            status: 状态码     0:成功    1:失败
            msg:    错误信息
    '''

    def add(self, QQ, docList, time):
        collection = self.collection

        try:
            collection.insert_one({"QQ": QQ, "docList": docList, "time": time})
        except Exception as e:
            return 1, e

        return 0, 'Success'

    '''查询QQ号的maxLen条聊天记录，maxLen默认为5'''
    '''返回值:
        back[]: 聊天记录列表 数组
    '''

    def find_QQ(self, QQ, maxLen=5):
        collection = self.collection
        res = collection.find({"QQ": QQ}).limit(maxLen).sort([("time", -1)])

        back = []
        if res is not None:
            for record in res:
                back.append(record['docList'])
        return back

    '''查找包含words的maxLen条聊天记录，maxLen默认为5'''
    '''返回值:
        back[]: 
        {
            'QQ': QQ号
            'docList':  聊天记录列表
        }
    '''

    def find_words(self, words="", maxLen=5):
        collection = self.collection
        res = collection.find({'docList': {'$regex': str(words)}}).limit(maxLen).sort([("time", -1)])

        back = []
        if res is not None:
            for record in res:
                back.append({'QQ': record['QQ'], 'docList': record['docList']})

        return back

    '''随机聊天记录'''
    '''返回值：
        存在语录：
            back={
                QQ:     QQ号
                docList:    聊天记录列表
            }
            
        无语录：
            None
    '''

    def rand_doc(self) -> Optional[Dict]:
        collection = self.collection
        res = collection.find()
        cnt = collection.estimated_document_count()

        if cnt == 0:
            return None

        rd = random.randint(0, cnt - 1)
        record = res[rd]

        back = {
            'QQ': record['QQ'],
            'docList': record['docList']
        }
        return back

    """清空群聊所有记录"""
    """
        返回值：
        status: 状态码     0:成功    1:失败
        msg:    错误信息
    """

    def drop(self):
        collection = self.collection
        try:
            collection.drop()
        except Exception as e:
            return 1, e

        return 0, 'Success'

    """MessageChain转化成聊天记录列表"""
    """参数：
            message: MessageChain
        返回值：
            back:   聊天记录列表
    """

    @staticmethod
    async def to_docList(message: MessageChain) -> list:
        back = []
        for ele in message:
            if ele.type == "Source" or ele.type == "Quote":
                continue
            if ele.type == "Plain":
                back.append("Plain")
                back.append(ele.text)
            elif ele.type == "Image":
                back.append("Image")
                img_byte = await ele.get_bytes()
                back.append(img_byte)
            elif ele.type == "Face":
                back.append("Face")
                back.append(str(ele.faceId))

        return back

    """聊天记录列表转化成MessageChain"""
    """参数：
            docList: 聊天记录列表
        返回值：
            back:   MessageChain列表
    """

    @staticmethod
    def to_MessageChain(docList: list) -> list:
        back = []
        L = len(docList)
        tp = ""
        for i in range(0, L):
            if i % 2 == 0:
                tp = docList[i]
            else:
                if tp == "Plain":
                    back.append(Plain(docList[i]))
                elif tp == "Image":
                    back.append(Image(data_bytes=docList[i]))
                elif tp == "Face":
                    back.append(Face(id=eval(docList[i])))
        return back
