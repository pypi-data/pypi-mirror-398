'''
Created by auto_sdk on 2018.07.26
'''
from seven_top.top.api.base import RestApi
class TmallCrmMemberPointChangeRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.biz_code = None
		self.biz_detail = None
		self.point = None
		self.type = None
		self.user_nick = None

	def getapiname(self):
		return 'tmall.crm.member.point.change'
