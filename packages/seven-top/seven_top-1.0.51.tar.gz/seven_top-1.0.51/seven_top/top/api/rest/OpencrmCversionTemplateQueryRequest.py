'''
Created by auto_sdk on 2021.11.24
'''
from seven_top.top.api.base import RestApi
class OpencrmCversionTemplateQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.cur_page = None
		self.page_size = None
		self.type = None

	def getapiname(self):
		return 'taobao.opencrm.cversion.template.query'
