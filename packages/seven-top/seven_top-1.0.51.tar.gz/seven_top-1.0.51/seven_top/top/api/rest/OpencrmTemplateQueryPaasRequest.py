'''
Created by auto_sdk on 2022.02.17
'''
from seven_top.top.api.base import RestApi
class OpencrmTemplateQueryPaasRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.cur_page = None
		self.id = None
		self.msg_type = None
		self.page_size = None
		self.type = None

	def getapiname(self):
		return 'taobao.opencrm.template.query.paas'
