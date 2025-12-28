# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2025-06-09 10:18:16
@LastEditTime: 2025-06-09 11:43:02
@LastEditors: HuangJianYi
@Description: 
"""
'''
Created by auto_sdk on 2025.05.09
'''
from seven_top.top.api.base import RestApi


class OpencrmSignatureVerifySubmitRequest(RestApi):
    def __init__(self,domain='gw.api.taobao.com',port=80):
        RestApi.__init__(self,domain, port)
        self.signature_request = None

    def getapiname(self):
        return 'taobao.opencrm.signature.verify.submit'
