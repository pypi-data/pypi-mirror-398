# -*- coding: utf-8 -*-
'''
Created by auto_sdk on 2021.09.14 卖家历史库订单查询
'''
from seven_top.top.api.base import RestApi
class TaobaoTradesSoldHistoryGet(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.fields = ""
		# self.start_created = ""
		# self.end_created = ""
		# self.status = ""
		# self.ouid = ""
		# self.type = ""
		# self.ext_type = ""
		# self.rate_status = ""
		# self.tag = ""
		# self.page_no = ""
		# self.page_size = ""
		# self.use_has_next = ""


	def getapiname(self):
		return 'taobao.trades.sold.history.get'