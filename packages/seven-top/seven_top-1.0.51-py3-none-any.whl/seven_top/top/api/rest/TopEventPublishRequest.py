'''
Created by auto_sdk on 2023.03.31
'''
from seven_top.top.api.base import RestApi
class TopEventPublishRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.content = None
		self.trigger_code = None

	def getapiname(self):
		return 'taobao.top.event.publish'
