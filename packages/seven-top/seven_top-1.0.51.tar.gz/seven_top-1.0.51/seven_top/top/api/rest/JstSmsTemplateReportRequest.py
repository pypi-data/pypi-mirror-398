'''
Created by auto_sdk on 2021.12.14
'''
from seven_top.top.api.base import RestApi
class JstSmsTemplateReportRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.sms_template_request = None

	def getapiname(self):
		return 'taobao.jst.sms.template.report'
