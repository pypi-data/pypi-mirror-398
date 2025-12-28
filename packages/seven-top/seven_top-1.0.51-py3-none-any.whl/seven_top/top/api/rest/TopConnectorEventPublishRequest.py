'''
Created by auto_sdk on 2023.11.15
'''
from seven_top.top.api.base import RestApi
class TopConnectorEventPublishRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.entry_list = None

	def getapiname(self):
		return 'taobao.top.connector.event.publish'
