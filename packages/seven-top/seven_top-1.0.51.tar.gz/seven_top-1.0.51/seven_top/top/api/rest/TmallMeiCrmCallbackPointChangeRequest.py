'''
Created by auto_sdk on 2021.11.23
'''
from seven_top.top.api.base import RestApi
class TmallMeiCrmCallbackPointChangeRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.error_code = None
		self.ext_info = None
		self.mix_mobile = None
		self.point = None
		self.record_id = None
		self.result = None

	def getapiname(self):
		return 'tmall.mei.crm.callback.point.change'
