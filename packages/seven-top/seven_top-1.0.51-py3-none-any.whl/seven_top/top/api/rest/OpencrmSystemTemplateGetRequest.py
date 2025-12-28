'''
Created by auto_sdk on 2023.01.17
'''
from seven_top.top.api.base import RestApi
class OpencrmSystemTemplateGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.channel = None
		self.channel_type = None

	def getapiname(self):
		return 'taobao.opencrm.system.template.get'
