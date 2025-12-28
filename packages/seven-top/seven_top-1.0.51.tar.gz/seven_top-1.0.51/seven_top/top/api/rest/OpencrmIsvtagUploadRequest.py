'''
Created by auto_sdk on 2021.11.23
'''
from seven_top.top.api.base import RestApi
class OpencrmIsvtagUploadRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.attr_value = None
		self.members = None
		self.mix_nicks = None
		self.open_ids = None
		self.status = None
		self.tag_name = None
		self.type = None

	def getapiname(self):
		return 'taobao.opencrm.isvtag.upload'
