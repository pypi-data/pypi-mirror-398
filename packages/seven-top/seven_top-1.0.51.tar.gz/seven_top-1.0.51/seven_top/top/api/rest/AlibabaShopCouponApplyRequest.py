'''
Created by auto_sdk on 2021.07.28
'''
from seven_top.top.api.base import RestApi
class AlibabaShopCouponApplyRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.open_id = None
		self.uuid = None

	def getapiname(self):
		return 'alibaba.shop.coupon.apply'
