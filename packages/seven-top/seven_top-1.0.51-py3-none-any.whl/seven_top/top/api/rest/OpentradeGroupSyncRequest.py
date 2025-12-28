'''
Created by auto_sdk on 2021.01.12
'''
from seven_top.top.api.base import RestApi
class OpentradeGroupSyncRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.allow_type = None
		self.allow_white_list = None
		self.discount_price = None
		self.end_time = None
		self.expiration = None
		self.fail_process = None
		self.goal = None
		self.group_activity_id = None
		self.group_type = None
		self.item_id = None
		self.open_limit = None
		self.start_time = None

	def getapiname(self):
		return 'taobao.opentrade.group.sync'
