'''
Created by auto_sdk on 2020.10.13
'''
from seven_top.top.api.base import RestApi
class UserSellerGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.fields = None

	def getapiname(self):
		return 'taobao.user.seller.get'
