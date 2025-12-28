'''
Created by auto_sdk on 2022.02.17
'''
from seven_top.top.api.base import RestApi
class OpencrmSellerBlacklistAdddeleteRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.action_type = None
		self.target_type = None
		self.targets = None

	def getapiname(self):
		return 'taobao.opencrm.seller.blacklist.adddelete'
