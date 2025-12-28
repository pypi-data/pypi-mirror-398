'''
Created by auto_sdk on 2022.10.13
'''
from seven_top.top.api.base import RestApi
class OpencrmShortmessageSendRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.task_content = None

	def getapiname(self):
		return 'taobao.opencrm.shortmessage.send'
