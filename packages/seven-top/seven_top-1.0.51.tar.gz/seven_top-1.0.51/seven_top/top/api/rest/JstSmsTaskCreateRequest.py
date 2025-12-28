'''
Created by auto_sdk on 2021.01.12
'''
from seven_top.top.api.base import RestApi
class JstSmsTaskCreateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.param_create_sms_task_request = None

	def getapiname(self):
		return 'taobao.jst.sms.task.create'
