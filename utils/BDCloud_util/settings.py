token_url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={}&client_secret={}"

headers = {'content-type': 'application/x-www-form-urlencoded'}

resp_url = {
    "Image_audit": "https://aip.baidubce.com/rest/2.0/solution/v1/img_censor/v2/user_defined",
    "Text_recognize": "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"
}