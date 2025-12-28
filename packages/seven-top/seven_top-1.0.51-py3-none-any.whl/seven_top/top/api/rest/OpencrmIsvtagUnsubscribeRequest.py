'''
Created by auto_sdk on 2021.11.09
'''
from seven_top.top.api.base import RestApi
class OpencrmIsvtagUnsubscribeRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.nick = None
		self.tag_name = None

	def getapiname(self):
		return 'taobao.opencrm.isvtag.unsubscribe'
