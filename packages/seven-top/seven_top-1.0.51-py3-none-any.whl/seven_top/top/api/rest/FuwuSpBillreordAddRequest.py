'''
Created by auto_sdk on 2021.11.26
'''
from seven_top.top.api.base import RestApi
class FuwuSpBillreordAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.param_bill_record_d_t_o = None

	def getapiname(self):
		return 'taobao.fuwu.sp.billreord.add'
