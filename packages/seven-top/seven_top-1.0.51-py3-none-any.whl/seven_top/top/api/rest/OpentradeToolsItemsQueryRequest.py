# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2022-06-23 16:11:05
@LastEditTime: 2024-01-25 16:56:17
@LastEditors: HuangJianYi
@Description: 
"""
'''
Created by auto_sdk on 2020.12.07
'''
from seven_top.top.api.base import RestApi
class OpentradeToolsItemsQueryRequest(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.miniapp_id = None
        self.page_index = None
        self.page_size = None

    def getapiname(self):
        return 'taobao.opentrade.tools.items.query'
