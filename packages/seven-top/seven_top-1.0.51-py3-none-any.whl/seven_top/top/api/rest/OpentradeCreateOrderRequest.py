'''
Created by auto_sdk on 2021.03.30
'''
from seven_top.top.api.base import RestApi
class OpentradeCreateOrderRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.address = None
		self.buyer_memo = None
		self.full_name = None
		self.item_infos = None
		self.mobile = None
		self.open_user_id = None
		self.out_id = None
		self.seller_memo = None

	def getapiname(self):
		return 'taobao.opentrade.create.order'
