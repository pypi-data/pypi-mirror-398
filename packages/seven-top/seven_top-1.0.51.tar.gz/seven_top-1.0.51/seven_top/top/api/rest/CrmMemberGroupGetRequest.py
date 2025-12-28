'''
Created by auto_sdk on 2022.09.21
'''
from seven_top.top.api.base import RestApi
class CrmMemberGroupGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.buyer_nick = None

	def getapiname(self):
		return 'taobao.crm.member.group.get'
