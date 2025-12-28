'''
Created by auto_sdk on 2020.08.13
'''
from seven_top.top.api.base import RestApi
class JstSmsExtendcodeQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.extend_code_query_request = None

	def getapiname(self):
		return 'taobao.jst.sms.extendcode.query'
