'''
Created by auto_sdk on 2021.11.23
'''
from seven_top.top.api.base import RestApi
class OpencrmCrowdsQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.crowd_name = None
		self.page = None
		self.page_size = None

	def getapiname(self):
		return 'taobao.opencrm.crowds.query'
