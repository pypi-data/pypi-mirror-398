'''
Created by auto_sdk on 2024.05.22
'''
from seven_top.top.api.base import RestApi
class OpencrmComponentDataQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.open_data_component_query = None

	def getapiname(self):
		return 'taobao.opencrm.component.data.query'
