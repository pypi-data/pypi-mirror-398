'''
Created by auto_sdk on 2025.05.09
'''
from seven_top.top.api.base import RestApi


class OpencrmSignatureVerifyInfoGetRequest(RestApi):
    def __init__(self,domain='gw.api.taobao.com',port=80):
        RestApi.__init__(self,domain, port)
        self.signature_request = None

    def getapiname(self):
        return 'taobao.opencrm.signature.verify.info.get'
