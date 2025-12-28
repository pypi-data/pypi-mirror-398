'''
Created by auto_sdk on 2023.02.09
'''
from seven_top.top.api.base import RestApi
class OpencrmCversionDigtplCreateupdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.digital_sms_template_content_dto = None
		self.status = None
		self.template_id = None
		self.template_name = None
		self.type = None

	def getapiname(self):
		return 'taobao.opencrm.cversion.digtpl.createupdate'
