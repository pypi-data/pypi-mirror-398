'''
Created by auto_sdk on 2020.12.14
'''
from seven_top.top.api.base import RestApi
class OpenTradeGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.fields = None
		self.tid = None

	def getapiname(self):
		return 'taobao.open.trade.get'
