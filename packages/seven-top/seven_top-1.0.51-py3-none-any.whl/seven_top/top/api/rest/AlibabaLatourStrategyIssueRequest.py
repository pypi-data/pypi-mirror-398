'''
Created by auto_sdk on 2020.10.13
'''
from seven_top.top.api.base import RestApi
class AlibabaLatourStrategyIssueRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.channel = None
		self.extra_data = None
		self.failover_algorithm_result = None
		self.idempotent_id = None
		self.need_identify_risk = None
		self.selected_benefit_code = None
		self.strategy_code = None
		self.transformed_user_type = None
		self.user_id = None
		self.user_nick = None
		self.user_type = None

	def getapiname(self):
		return 'alibaba.latour.strategy.issue'
