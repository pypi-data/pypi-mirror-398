'''
Created by auto_sdk on 2022.10.13
'''
from seven_top.top.api.base import RestApi
class OpencrmTesttmcSendRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.content_map = None
		self.target_app_key = None
		self.topic = None

	def getapiname(self):
		return 'taobao.opencrm.testtmc.send'
