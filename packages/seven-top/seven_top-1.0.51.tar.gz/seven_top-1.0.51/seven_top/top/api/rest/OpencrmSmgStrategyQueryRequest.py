'''
Created by auto_sdk on 2022.05.25
'''
from seven_top.top.api.base import RestApi
class OpencrmSmgStrategyQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.out_node_inst_id = None

	def getapiname(self):
		return 'taobao.opencrm.smg.strategy.query'
