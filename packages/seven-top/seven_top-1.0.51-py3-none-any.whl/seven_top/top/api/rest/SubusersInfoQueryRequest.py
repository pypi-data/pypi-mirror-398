'''
Created by auto_sdk on 2022.02.18
'''
from seven_top.top.api.base import RestApi
class SubusersInfoQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.site = None

	def getapiname(self):
		return 'taobao.subusers.info.query'
