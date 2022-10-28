from tencentcloud.nlp.v20190408 import nlp_client
from tencentcloud.nlp.v20190408 import models as nlp_model
from tencentcloud.ocr.v20181119 import ocr_client
from tencentcloud.ocr.v20181119 import models as ocr_model
from tencentcloud.tiia.v20190529 import tiia_client
from tencentcloud.tiia.v20190529 import models as tiia_model
from tencentcloud.tmt.v20180321 import tmt_client
from tencentcloud.tmt.v20180321 import models as tmt_model

from Config import config_data

user_data = config_data['TencentCloud']

INFO = {
    "NLP": {
        "endpoints": "nlp.tencentcloudapi.com",
        "client": nlp_client.NlpClient,
        "req": nlp_model.ChatBotRequest(),
        "resp_func": "ChatBot"
    },
    "Text_recognize": {
        "endpoints": "ocr.tencentcloudapi.com",
        "client": ocr_client.OcrClient,
        "req": ocr_model.GeneralAccurateOCRRequest(),
        "resp_func": "GeneralAccurateOCR"
    },
    "image_enhance": {
        "endpoints": "tiia.tencentcloudapi.com",
        "client": tiia_client.TiiaClient,
        "req": tiia_model.EnhanceImageRequest(),
        "resp_func": "EnhanceImage"
    },
    "language_detect": {
        "endpoints": "tmt.tencentcloudapi.com",
        "client": tmt_client.TmtClient,
        "req": tmt_model.LanguageDetectRequest(),
        "resp_func": "LanguageDetect"
    },
    "text_translate": {
        "endpoints": "tmt.tencentcloudapi.com",
        "client": tmt_client.TmtClient,
        "req": tmt_model.TextTranslateRequest(),
        "resp_func": "TextTranslate"
    }
}
