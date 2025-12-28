'''
Created by auto_sdk on 2022.09.19
'''
from seven_top.top.api.base import RestApi
class TmallMeiCrmMemberSyncPrivyRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.extend = None
		self.level = None
		self.level_expire_time = None
		self.level_point = None
		self.level_type = None
		self.mobile = None
		self.ouid = None
		self.point = None
		self.version = None

	def getapiname(self):
		return 'tmall.mei.crm.member.sync.privy'
