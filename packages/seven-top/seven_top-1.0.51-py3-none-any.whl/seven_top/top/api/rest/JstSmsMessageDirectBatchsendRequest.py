'''
Created by auto_sdk on 2021.01.14
'''
from seven_top.top.api.base import RestApi
class JstSmsMessageDirectBatchsendRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.extend_num = None
		self.rec_num = None
		self.sign_name = None
		self.sms_content = None
		self.sms_template_code = None
		self.task_code = None
		self.task_sign = None
		self.url = None

	def getapiname(self):
		return 'taobao.jst.sms.message.direct.batchsend'
