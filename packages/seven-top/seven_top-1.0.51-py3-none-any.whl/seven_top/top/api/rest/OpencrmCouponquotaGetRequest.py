'''
Created by auto_sdk on 2023.12.19
'''
from seven_top.top.api.base import RestApi
class OpencrmCouponquotaGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)

	def getapiname(self):
		return 'taobao.opencrm.couponquota.get'
