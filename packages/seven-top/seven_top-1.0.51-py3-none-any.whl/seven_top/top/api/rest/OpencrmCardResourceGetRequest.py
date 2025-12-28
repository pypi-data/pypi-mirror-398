'''
Created by auto_sdk on 2021.12.09
'''
from seven_top.top.api.base import RestApi
class OpencrmCardResourceGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.extend_info = None
		self.file_size = None
		self.memo = None
		self.oss_key = None
		self.resource_type = None

	def getapiname(self):
		return 'taobao.opencrm.card.resource.get'
