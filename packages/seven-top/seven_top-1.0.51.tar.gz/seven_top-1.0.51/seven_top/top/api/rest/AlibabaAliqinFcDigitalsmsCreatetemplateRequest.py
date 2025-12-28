'''
Created by auto_sdk on 2021.11.25
'''
from seven_top.top.api.base import RestApi
class AlibabaAliqinFcDigitalsmsCreatetemplateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.apply_remark = None
		self.template_contents = None
		self.template_name = None

	def getapiname(self):
		return 'alibaba.aliqin.fc.digitalsms.createtemplate'
