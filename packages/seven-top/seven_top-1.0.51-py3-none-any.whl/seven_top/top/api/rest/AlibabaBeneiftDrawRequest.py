'''
Created by auto_sdk on 2019.08.26
'''
from seven_top.top.api.base import RestApi
class AlibabaBeneiftDrawRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.app_name = None
		self.ename = None
		self.ip = None

	def getapiname(self):
		return 'alibaba.beneift.draw'
