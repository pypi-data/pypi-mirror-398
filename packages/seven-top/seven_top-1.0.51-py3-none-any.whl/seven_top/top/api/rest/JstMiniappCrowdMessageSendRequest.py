'''
Created by auto_sdk on 2020.11.26
'''
from seven_top.top.api.base import RestApi
class JstMiniappCrowdMessageSendRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.content = None
		self.crowd_code = None
		self.sign_name = None
		self.template_code = None
		self.url = None

	def getapiname(self):
		return 'taobao.jst.miniapp.crowd.message.send'
