'''
Created by auto_sdk on 2022.02.17
'''
from seven_top.top.api.base import RestApi
class OpencrmSignatureQueryPaasRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.signature_query = None

	def getapiname(self):
		return 'taobao.opencrm.signature.query.paas'
