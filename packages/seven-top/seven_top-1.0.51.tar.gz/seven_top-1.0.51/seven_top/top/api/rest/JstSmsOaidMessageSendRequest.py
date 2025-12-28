'''
Created by auto_sdk on 2021.04.22
'''
from seven_top.top.api.base import RestApi
class JstSmsOaidMessageSendRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.param_send_message_by_o_a_i_d_request = None

	def getapiname(self):
		return 'taobao.jst.sms.oaid.message.send'
