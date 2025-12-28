'''
Created by auto_sdk on 2025.02.21
'''
from seven_top.top.api.base import RestApi
class IndustryTrendyGachaponBatchAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.trendy_toy_gachapon_transaction_insert_request = None

	def getapiname(self):
		return 'taobao.industry.trendy.gachapon.batch.add'
