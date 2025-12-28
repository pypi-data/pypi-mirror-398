'''
Created by auto_sdk on 2023.12.19
'''
from seven_top.top.api.base import RestApi
class OpencrmSmsservicestatusUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.operate_type = None

	def getapiname(self):
		return 'taobao.opencrm.smsservicestatus.update'
