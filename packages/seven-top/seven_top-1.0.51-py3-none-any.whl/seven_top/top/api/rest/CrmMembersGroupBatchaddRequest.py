'''
Created by auto_sdk on 2018.07.25
'''
from seven_top.top.api.base import RestApi
class CrmMembersGroupBatchaddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.buyer_nicks = None
		self.group_ids = None

	def getapiname(self):
		return 'taobao.crm.members.group.batchadd'
