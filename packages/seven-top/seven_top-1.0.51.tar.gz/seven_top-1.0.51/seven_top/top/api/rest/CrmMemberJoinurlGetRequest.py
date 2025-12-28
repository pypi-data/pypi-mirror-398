'''
Created by auto_sdk on 2019.07.25
'''
from seven_top.top.api.base import RestApi
class CrmMemberJoinurlGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.callback_url = None
		self.extra_info = None

	def getapiname(self):
		return 'taobao.crm.member.joinurl.get'
