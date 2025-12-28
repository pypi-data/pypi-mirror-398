'''
Created by auto_sdk on 2021.11.22
'''
from seven_top.top.api.base import RestApi
class OpencrmTemplateUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.status = None
		self.template = None

	def getapiname(self):
		return 'taobao.opencrm.template.update'
