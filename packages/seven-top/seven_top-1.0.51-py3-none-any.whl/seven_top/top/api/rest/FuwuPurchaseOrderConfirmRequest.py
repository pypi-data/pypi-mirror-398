'''
Created by auto_sdk on 2018.07.25
'''
from seven_top.top.api.base import RestApi
class FuwuPurchaseOrderConfirmRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.param_order_confirm_query_d_t_o = None

	def getapiname(self):
		return 'taobao.fuwu.purchase.order.confirm'
