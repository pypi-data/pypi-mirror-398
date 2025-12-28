'''
Created by auto_sdk on 2022.03.24
'''
from seven_top.top.api.base import RestApi
class OpencrmRuleExeruleRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.biz_order_id = None
		self.biz_type = None
		self.buyer_nick = None
		self.end_date_by_year = None
		self.exclude_item = None
		self.freight_fee = None
		self.item_amount_map = None
		self.month_end_day = None
		self.month_start_day = None
		self.open_uid = None
		self.param_map = None
		self.query_end_date = None
		self.query_start_date = None
		self.special_item = None
		self.specify_amount = None
		self.specify_amount_by_date = None
		self.specify_amount_by_day = None
		self.specify_count_by_date = None
		self.specify_count_by_day = None
		self.start_date_by_year = None
		self.stat_type = None
		self.total_item_set = None
		self.total_pay_amount = None
		self.user_id = None
		self.week_end_day = None
		self.week_start_day = None

	def getapiname(self):
		return 'taobao.opencrm.rule.exerule'
