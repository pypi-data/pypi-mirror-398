'''
Created by auto_sdk on 2021.11.25
'''
from seven_top.top.api.base import RestApi
class OpencrmCrowdinstLiteUploadBachRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.open_crowd_user_d_t_o = None

	def getapiname(self):
		return 'taobao.opencrm.crowdinst.lite.upload.bach'
