'''
Created by auto_sdk on 2023.06.21
'''
from seven_top.top.api.base import RestApi
class TopEventSubscriptionQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.trigger_code = None

	def getapiname(self):
		return 'taobao.top.event.subscription.query'
