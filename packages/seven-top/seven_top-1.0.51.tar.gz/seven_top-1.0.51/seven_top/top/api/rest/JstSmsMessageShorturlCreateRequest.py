'''
Created by auto_sdk on 2021.01.04
'''
from seven_top.top.api.base import RestApi
class JstSmsMessageShorturlCreateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.batch_number = None
		self.need_https_prefix = None
		self.tag = None
		self.url = None

	def getapiname(self):
		return 'taobao.jst.sms.message.shorturl.create'
