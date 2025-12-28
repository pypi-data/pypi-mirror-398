'''
Created by auto_sdk on 2021.08.12
'''
from seven_top.top.api.base import RestApi
class CrmPointAvailableGetPrivyCpRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.ouid = None

	def getapiname(self):
		return 'taobao.crm.point.available.get.privy.cp'
