'''
Created by auto_sdk on 2023.12.19
'''
from seven_top.top.api.base import RestApi
class PictureIsreferencedGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.picture_id = None

	def getapiname(self):
		return 'taobao.picture.isreferenced.get'
