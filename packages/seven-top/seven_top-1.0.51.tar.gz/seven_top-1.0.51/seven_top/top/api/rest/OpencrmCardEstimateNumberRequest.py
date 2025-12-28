'''
Created by auto_sdk on 2022.03.30
'''
from seven_top.top.api.base import RestApi
class OpencrmCardEstimateNumberRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.crowd_inst_id = None
		self.filter_black_list = None
		self.mobile_acquisition_rule = None
		self.template_id = None

	def getapiname(self):
		return 'taobao.opencrm.card.estimate.number'
