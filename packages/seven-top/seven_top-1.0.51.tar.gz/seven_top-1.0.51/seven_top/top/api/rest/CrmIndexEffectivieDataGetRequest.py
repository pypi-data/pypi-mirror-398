'''
Created by auto_sdk on 2021.11.23
'''
from seven_top.top.api.base import RestApi
class CrmIndexEffectivieDataGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.query = None

	def getapiname(self):
		return 'taobao.crm.index.effectivie.data.get'
