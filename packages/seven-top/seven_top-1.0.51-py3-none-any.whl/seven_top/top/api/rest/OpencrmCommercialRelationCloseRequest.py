'''
Created by auto_sdk on 2022.04.18
'''
from seven_top.top.api.base import RestApi
class OpencrmCommercialRelationCloseRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.crm_isv_charge_relation_dto = None

	def getapiname(self):
		return 'taobao.opencrm.commercial.relation.close'
