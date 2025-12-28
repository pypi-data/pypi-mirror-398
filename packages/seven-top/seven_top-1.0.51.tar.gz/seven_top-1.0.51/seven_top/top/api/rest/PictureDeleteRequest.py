'''
Created by auto_sdk on 2019.01.21
'''
from seven_top.top.api.base import RestApi
class PictureDeleteRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.picture_ids = None

	def getapiname(self):
		return 'taobao.picture.delete'
