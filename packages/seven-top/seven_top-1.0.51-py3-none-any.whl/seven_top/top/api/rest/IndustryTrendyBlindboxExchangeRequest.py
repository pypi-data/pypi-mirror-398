'''
Created by auto_sdk on 2025.07.07
'''
from seven_top.top.api.base import RestApi
class IndustryTrendyBlindboxExchangeRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.trendy_toy_exchange_request = None

	def getapiname(self):
		return 'taobao.industry.trendy.blindbox.exchange'
