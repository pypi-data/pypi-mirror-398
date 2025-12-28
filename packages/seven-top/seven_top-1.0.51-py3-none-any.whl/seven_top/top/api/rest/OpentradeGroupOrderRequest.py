'''
Created by auto_sdk on 2021.01.13
'''
from seven_top.top.api.base import RestApi
class OpentradeGroupOrderRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.group_id = None

	def getapiname(self):
		return 'taobao.opentrade.group.order'
