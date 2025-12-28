'''
Created by auto_sdk on 2018.07.25
'''
from seven_top.top.api.base import RestApi
class CrmMemberIdentityGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.extra_info = None
		self.mix_nick = None
		self.nick = None

	def getapiname(self):
		return 'taobao.crm.member.identity.get'
