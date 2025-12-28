'''
Created by auto_sdk on 2020.12.17
'''
from seven_top.top.api.base import RestApi
class MiniappItemsGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.fields = None
		self.num_iids = None

	def getapiname(self):
		return 'taobao.miniapp.items.get'
