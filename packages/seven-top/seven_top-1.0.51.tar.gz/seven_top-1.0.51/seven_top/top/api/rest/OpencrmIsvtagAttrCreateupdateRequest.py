'''
Created by auto_sdk on 2021.11.09
'''
from seven_top.top.api.base import RestApi
class OpencrmIsvtagAttrCreateupdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.attr_id = None
		self.attr_name = None
		self.operation = None
		self.tag_name = None

	def getapiname(self):
		return 'taobao.opencrm.isvtag.attr.createupdate'
