'''
Created by auto_sdk on 2022.09.19
'''
from seven_top.top.api.base import RestApi
class CrmMemberinfoUpdatePrivyRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.city = None
		self.close_trade_amount = None
		self.close_trade_count = None
		self.grade = None
		self.group_ids = None
		self.item_num = None
		self.ouid = None
		self.province = None
		self.status = None
		self.trade_amount = None
		self.trade_count = None

	def getapiname(self):
		return 'taobao.crm.memberinfo.update.privy'
