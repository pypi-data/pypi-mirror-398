'''
Created by auto_sdk on 2022.10.11
'''
from seven_top.top.api.base import RestApi
class OpencrmGradeBatchaddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.member_grade_list = None

	def getapiname(self):
		return 'taobao.opencrm.grade.batchadd'
