# -*- coding: utf-8 -*-
'''
Created by auto_sdk on 2024.10.11 奇门增量添加商品
'''
from seven_top.top.api.base import RestApi


class QmTandyCrmRdsItemAdd(RestApi):
    def __init__(self, domain='o6587eg60m.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.data = ""

    def getapiname(self):
        return 'tandy.crm.rds.item.add'
