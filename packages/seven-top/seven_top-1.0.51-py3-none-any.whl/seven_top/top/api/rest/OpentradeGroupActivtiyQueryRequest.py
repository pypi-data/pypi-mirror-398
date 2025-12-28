'''
Created by auto_sdk on 2021.01.13
'''
from seven_top.top.api.base import RestApi
class OpentradeGroupActivtiyQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.group_activity_id = None
		self.item_id = None
		self.page_index = None
		self.page_size = None

	def getapiname(self):
		return 'taobao.opentrade.group.activtiy.query'
