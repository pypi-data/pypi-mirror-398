'''
Created by auto_sdk on 2022.09.19
'''
from seven_top.top.api.base import RestApi
class CrmServiceChannelShortlinkCreateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.link_type = None
		self.short_link_data = None
		self.short_link_name = None

	def getapiname(self):
		return 'taobao.crm.service.channel.shortlink.create'
