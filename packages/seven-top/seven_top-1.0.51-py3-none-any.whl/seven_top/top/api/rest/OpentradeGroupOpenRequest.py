'''
Created by auto_sdk on 2021.01.12
'''
from seven_top.top.api.base import RestApi
class OpentradeGroupOpenRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.group_activity_id = None
		self.item_id = None
		self.open_user_id = None

	def getapiname(self):
		return 'taobao.opentrade.group.open'
