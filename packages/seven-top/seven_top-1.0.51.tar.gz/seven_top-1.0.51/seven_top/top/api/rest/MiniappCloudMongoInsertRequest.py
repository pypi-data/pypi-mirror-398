'''
Created by auto_sdk on 2020.09.17
'''
from seven_top.top.api.base import RestApi
class MiniappCloudMongoInsertRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.record = None
		self.collection = None
		self.env = None

	def getapiname(self):
		return 'taobao.miniapp.cloud.mongo.insert'
