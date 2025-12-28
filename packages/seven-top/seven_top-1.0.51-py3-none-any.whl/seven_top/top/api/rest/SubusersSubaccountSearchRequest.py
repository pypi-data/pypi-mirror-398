'''
Created by auto_sdk on 2022.03.25
'''
from seven_top.top.api.base import RestApi
class SubusersSubaccountSearchRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.filter_key = None
		self.main_nick = None
		self.page_num = None
		self.page_size = None

	def getapiname(self):
		return 'taobao.subusers.subaccount.search'
