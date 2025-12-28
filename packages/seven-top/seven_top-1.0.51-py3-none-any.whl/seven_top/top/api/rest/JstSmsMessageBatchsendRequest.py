'''
Created by auto_sdk on 2020.08.06
'''
from seven_top.top.api.base import RestApi
class JstSmsMessageBatchsendRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.send_batch_message_request = None

	def getapiname(self):
		return 'taobao.jst.sms.message.batchsend'
