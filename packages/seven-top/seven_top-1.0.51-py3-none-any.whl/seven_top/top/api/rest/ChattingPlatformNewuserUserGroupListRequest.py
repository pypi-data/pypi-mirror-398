'''
Created by auto_sdk on 2021.11.23
'''
from seven_top.top.api.base import RestApi
class ChattingPlatformNewuserUserGroupListRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.app_code = None
		self.app_secret = None
		self.user_id = None
		self.user_nick = None

	def getapiname(self):
		return 'taobao.chatting.platform.newuser.user.group.list'
