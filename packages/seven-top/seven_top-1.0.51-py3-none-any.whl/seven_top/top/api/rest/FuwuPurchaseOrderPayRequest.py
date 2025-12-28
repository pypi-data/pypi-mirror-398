'''
Created by auto_sdk on 2022.09.20
'''
from seven_top.top.api.base import RestApi
class FuwuPurchaseOrderPayRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.appkey = None
		self.device_type = None
		self.order_id = None
		self.out_order_id = None

	def getapiname(self):
		return 'taobao.fuwu.purchase.order.pay'
