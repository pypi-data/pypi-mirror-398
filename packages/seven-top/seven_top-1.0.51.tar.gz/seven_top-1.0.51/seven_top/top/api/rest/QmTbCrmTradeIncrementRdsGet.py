# -*- coding: utf-8 -*-
'''
Created by auto_sdk on 2021.09.14 奇门增量获取卖家订单
'''
from seven_top.top.api.base import RestApi


class QmTbCrmTradeIncrementRdsGet(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.trade_info = ""

    def getapiname(self):
        return 'taobao.trade.increment.rds.get'
