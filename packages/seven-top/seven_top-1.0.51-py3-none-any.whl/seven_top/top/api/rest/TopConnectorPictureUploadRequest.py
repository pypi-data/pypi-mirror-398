'''
Created by auto_sdk on 2023.11.23
'''
from seven_top.top.api.base import RestApi
class TopConnectorPictureUploadRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.image_data = None

	def getapiname(self):
		return 'taobao.top.connector.picture.upload'

	def getMultipartParas(self):
		return ['image_data']
