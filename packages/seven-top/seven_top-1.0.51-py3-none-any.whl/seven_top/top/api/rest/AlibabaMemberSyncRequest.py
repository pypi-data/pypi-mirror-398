'''
Created by auto_sdk on 2022.10.25
'''
from seven_top.top.api.base import RestApi
class AlibabaMemberSyncRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.sync_member = None

	def getapiname(self):
		return 'alibaba.member.sync'
