'''
Created by auto_sdk on 2021.11.23
'''
from seven_top.top.api.base import RestApi
class OpencrmCtagUploadPrivyRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.encrypt = None
		self.id = None
		self.members = None
		self.open_ids = None
		self.status = None
		self.type = None

	def getapiname(self):
		return 'taobao.opencrm.ctag.upload.privy'
