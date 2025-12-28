'''
Created by auto_sdk on 2022.10.13
'''
from seven_top.top.api.base import RestApi
class OpencrmCversionCardtplUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.status = None
		self.template_id = None
		self.template_params = None
		self.type = None

	def getapiname(self):
		return 'taobao.opencrm.cversion.cardtpl.update'
