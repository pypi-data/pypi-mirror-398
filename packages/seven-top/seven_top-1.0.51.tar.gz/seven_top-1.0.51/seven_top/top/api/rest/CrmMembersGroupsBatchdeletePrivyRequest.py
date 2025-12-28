'''
Created by auto_sdk on 2022.09.19
'''
from seven_top.top.api.base import RestApi
class CrmMembersGroupsBatchdeletePrivyRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.group_ids = None
		self.ouids = None

	def getapiname(self):
		return 'taobao.crm.members.groups.batchdelete.privy'
