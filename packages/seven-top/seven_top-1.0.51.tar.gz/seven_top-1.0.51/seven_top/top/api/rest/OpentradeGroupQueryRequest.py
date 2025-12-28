'''
Created by auto_sdk on 2021.01.13
'''
from seven_top.top.api.base import RestApi
class OpentradeGroupQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.group_activity_id = None
		self.item_id = None
		self.open_user_id = None
		self.order_by = None
		self.page_index = None
		self.page_size = None
		self.with_expire = None

	def getapiname(self):
		return 'taobao.opentrade.group.query'
