'''
Created by auto_sdk on 2021.11.22
'''
from seven_top.top.api.base import RestApi
class OpencrmCtagUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.id = None
		self.name = None
		self.operation = None

	def getapiname(self):
		return 'taobao.opencrm.ctag.update'
