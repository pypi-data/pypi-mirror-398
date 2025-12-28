'''
Created by auto_sdk on 2020.08.12
'''
from seven_top.top.api.base import RestApi
class OpentradeSpecialUsersQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.item_id = None
		self.open_user_ids = None
		self.page_index = None
		self.page_size = None
		self.sku_id = None
		self.status = None

	def getapiname(self):
		return 'taobao.opentrade.special.users.query'
