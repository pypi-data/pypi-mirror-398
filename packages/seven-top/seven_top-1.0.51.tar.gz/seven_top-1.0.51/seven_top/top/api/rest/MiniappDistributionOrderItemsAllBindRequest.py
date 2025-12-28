'''
Created by auto_sdk on 2021.11.23
'''
from seven_top.top.api.base import RestApi
class MiniappDistributionOrderItemsAllBindRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.all_item_bind_request = None

	def getapiname(self):
		return 'taobao.miniapp.distribution.order.items.all.bind'
