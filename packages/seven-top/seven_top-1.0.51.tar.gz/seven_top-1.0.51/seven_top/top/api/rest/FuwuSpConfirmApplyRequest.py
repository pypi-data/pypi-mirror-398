'''
Created by auto_sdk on 2022.09.20
'''
from seven_top.top.api.base import RestApi
class FuwuSpConfirmApplyRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.param_income_confirm_d_t_o = None

	def getapiname(self):
		return 'taobao.fuwu.sp.confirm.apply'
