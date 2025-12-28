'''
Created by auto_sdk on 2022.04.19
'''
from seven_top.top.api.base import RestApi
class OpencrmCommercialChargeEstimateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.charge_type = None
		self.end_date = None
		self.start_date = None

	def getapiname(self):
		return 'taobao.opencrm.commercial.charge.estimate'
