'''
Created by auto_sdk on 2022.04.01
'''
from seven_top.top.api.base import RestApi
class OpencrmAllDomainCrowdUploadRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.crowd_id = None
		self.encrypt = None
		self.members = None
		self.type = None

	def getapiname(self):
		return 'taobao.opencrm.all.domain.crowd.upload'
