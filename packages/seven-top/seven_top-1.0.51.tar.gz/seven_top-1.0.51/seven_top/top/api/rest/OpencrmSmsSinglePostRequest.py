'''
Created by auto_sdk on 2022.02.17
'''
from seven_top.top.api.base import RestApi
class OpencrmSmsSinglePostRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.task_content = None

	def getapiname(self):
		return 'taobao.opencrm.sms.single.post'
