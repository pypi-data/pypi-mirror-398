'''
Created by auto_sdk on 2020.10.14
'''
from seven_top.top.api.base import RestApi
class AlibabaBenefitSendRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.app_name = None
		self.ip = None
		self.receiver_id = None
		self.right_ename = None
		self.unique_id = None
		self.user_type = None

	def getapiname(self):
		return 'alibaba.benefit.send'
