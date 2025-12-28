'''
Created by auto_sdk on 2021.11.23
'''
from seven_top.top.api.base import RestApi
class OpencrmMemberSellerFetchstatusRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.seller_nicks = None

	def getapiname(self):
		return 'taobao.opencrm.member.seller.fetchstatus'
