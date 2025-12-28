'''
Created by auto_sdk on 2021.08.12
'''
from seven_top.top.api.base import RestApi
class CrmMemberIdentityGetPrivyRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.extra_info = None
		self.ouid = None

	def getapiname(self):
		return 'taobao.crm.member.identity.get.privy'
