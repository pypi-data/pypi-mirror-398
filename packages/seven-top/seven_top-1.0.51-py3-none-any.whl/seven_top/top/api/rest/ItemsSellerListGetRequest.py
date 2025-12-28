'''
Created by auto_sdk on 2020.07.21
'''
from seven_top.top.api.base import RestApi
class ItemsSellerListGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.fields = None
		self.num_iids = None

	def getapiname(self):
		return 'taobao.items.seller.list.get'
