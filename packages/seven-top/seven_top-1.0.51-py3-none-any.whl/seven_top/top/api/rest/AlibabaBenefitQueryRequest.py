'''
Created by auto_sdk on 2020.10.14
'''
from seven_top.top.api.base import RestApi
class AlibabaBenefitQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.app_name = None
		self.award_type = None
		self.ename = None

	def getapiname(self):
		return 'alibaba.benefit.query'
