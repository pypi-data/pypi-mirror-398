'''
Created by auto_sdk on 2020.10.13
'''
from seven_top.top.api.base import RestApi
class AlibabaLatourStrategyShowRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.channel = None
		self.current_page = None
		self.filter_crowd = None
		self.filter_empty_inventory = None
		self.need_identify_risk = None
		self.page_size = None
		self.skip_with_had_win = None
		self.strategy_code = None
		self.transformed_user_type = None
		self.user_id = None
		self.user_nick = None
		self.user_type = None
		self.with_test_benefit = None

	def getapiname(self):
		return 'alibaba.latour.strategy.show'
