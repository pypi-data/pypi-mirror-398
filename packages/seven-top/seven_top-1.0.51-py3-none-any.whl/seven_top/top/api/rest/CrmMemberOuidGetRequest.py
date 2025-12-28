'''
Created by auto_sdk on 2021.11.24
'''
from seven_top.top.api.base import RestApi
class CrmMemberOuidGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.user_nick = None

	def getapiname(self):
		return 'taobao.crm.member.ouid.get'
