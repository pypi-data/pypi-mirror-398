'''
Created by auto_sdk on 2022.06.29
'''
from seven_top.top.api.base import RestApi
class OpencrmSellerOrderActivateStatusQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)

	def getapiname(self):
		return 'taobao.opencrm.seller.order.activate.status.query'
