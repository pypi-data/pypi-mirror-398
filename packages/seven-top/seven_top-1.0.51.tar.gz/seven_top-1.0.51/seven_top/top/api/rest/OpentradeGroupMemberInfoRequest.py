'''
Created by auto_sdk on 2020.11.23
'''
from seven_top.top.api.base import RestApi
class OpentradeGroupMemberInfoRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.group_id = None
		self.open_user_id = None

	def getapiname(self):
		return 'taobao.opentrade.group.member.info'
