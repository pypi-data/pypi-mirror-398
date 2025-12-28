'''
Created by auto_sdk on 2021.11.25
'''
from seven_top.top.api.base import RestApi
class PictureTokenRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.generate_token_request = None

	def getapiname(self):
		return 'taobao.picture.token'
