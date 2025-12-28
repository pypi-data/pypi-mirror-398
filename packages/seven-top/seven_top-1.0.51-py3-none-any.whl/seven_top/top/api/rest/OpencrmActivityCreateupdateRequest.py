'''
Created by auto_sdk on 2023.12.19
'''
from seven_top.top.api.base import RestApi
class OpencrmActivityCreateupdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.activity_id = None
		self.des = None
		self.end_time = None
		self.name = None
		self.schedule_mode = None
		self.start_time = None
		self.status = None

	def getapiname(self):
		return 'taobao.opencrm.activity.createupdate'
