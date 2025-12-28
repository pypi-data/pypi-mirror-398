'''
Created by auto_sdk on 2022.11.22
'''
from seven_top.top.api.base import RestApi
class AlibabaMemberPointChangeSyncRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.sync_member_point_change_dto = None

	def getapiname(self):
		return 'alibaba.member.point.change.sync'
