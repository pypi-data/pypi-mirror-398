'''
Created by auto_sdk on 2021.12.28
'''
from seven_top.top.api.base import RestApi
class JstSmsSignnameCreateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.add_sms_sign_request = None

	def getapiname(self):
		return 'taobao.jst.sms.signname.create'
