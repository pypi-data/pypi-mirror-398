'''
Created by auto_sdk on 2022.05.24
'''
from seven_top.top.api.base import RestApi
class CrmGroupsGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.current_page = None
		self.page_size = None

	def getapiname(self):
		return 'taobao.crm.groups.get'
