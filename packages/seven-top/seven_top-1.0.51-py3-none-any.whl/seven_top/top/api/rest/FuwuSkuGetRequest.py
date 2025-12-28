'''
Created by auto_sdk on 2022.09.20
'''
from seven_top.top.api.base import RestApi
class FuwuSkuGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.article_code = None
		self.nick = None

	def getapiname(self):
		return 'taobao.fuwu.sku.get'
