'''
Created by auto_sdk on 2021.12.30
'''
from seven_top.top.api.base import RestApi
class OpencrmCardStrategyListQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.out_node_inst_id = None

	def getapiname(self):
		return 'taobao.opencrm.card.strategy.list.query'
