'''
Created by auto_sdk on 2022.05.09
'''
from seven_top.top.api.base import RestApi
class OpencrmShopDecorationQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.shop_decoration_query = None

	def getapiname(self):
		return 'taobao.opencrm.shop.decoration.query'
