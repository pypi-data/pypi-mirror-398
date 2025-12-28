'''
Created by auto_sdk on 2022.09.19
'''
from seven_top.top.api.base import RestApi
class TradesSimpleSoldGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.buyer_nick = None
		self.buyer_open_id = None
		self.end_created = None
		self.ext_type = None
		self.fields = None
		self.page_no = None
		self.page_size = None
		self.rate_status = None
		self.start_created = None
		self.status = None
		self.tag = None
		self.type = None
		self.use_has_next = None

	def getapiname(self):
		return 'taobao.trades.simple.sold.get'
