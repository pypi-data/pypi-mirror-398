'''
Created by auto_sdk on 2022.02.18
'''
from seven_top.top.api.base import RestApi
class SellercenterSubusersPageRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.account_status = None
		self.nick = None
		self.page_num = None
		self.page_size = None

	def getapiname(self):
		return 'taobao.sellercenter.subusers.page'
