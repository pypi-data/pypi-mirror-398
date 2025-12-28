'''
Created by auto_sdk on 2021.11.18
'''
from seven_top.top.api.base import RestApi
class CrmGrouptaskCheckRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.group_id = None

	def getapiname(self):
		return 'taobao.crm.grouptask.check'
