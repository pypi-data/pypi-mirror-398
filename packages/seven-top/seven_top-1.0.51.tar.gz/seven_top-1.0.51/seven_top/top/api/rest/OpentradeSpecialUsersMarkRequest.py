'''
Created by auto_sdk on 2020.10.14
'''
from seven_top.top.api.base import RestApi
class OpentradeSpecialUsersMarkRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.hit = None
		self.item_id = None
		self.limit_num = None
		self.open_user_ids = None
		self.sku_id = None
		self.status = None

	def getapiname(self):
		return 'taobao.opentrade.special.users.mark'
