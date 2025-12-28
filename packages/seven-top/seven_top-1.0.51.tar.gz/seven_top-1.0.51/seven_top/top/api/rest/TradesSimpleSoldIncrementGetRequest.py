'''
Created by auto_sdk on 2023.12.19
'''
from seven_top.top.api.base import RestApi
class TradesSimpleSoldIncrementGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.buyer_nick = None
		self.buyer_open_uid = None
		self.end_modified = None
		self.ext_type = None
		self.fields = None
		self.page_no = None
		self.page_size = None
		self.rate_status = None
		self.start_modified = None
		self.status = None
		self.tag = None
		self.type = None
		self.use_has_next = None

	def getapiname(self):
		return 'taobao.trades.simple.sold.increment.get'
