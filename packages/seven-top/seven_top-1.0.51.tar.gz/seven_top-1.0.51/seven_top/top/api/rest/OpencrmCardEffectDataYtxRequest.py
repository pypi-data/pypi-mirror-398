'''
Created by auto_sdk on 2022.03.10
'''
from seven_top.top.api.base import RestApi
class OpencrmCardEffectDataYtxRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.end_date = None
		self.start_date = None
		self.template_id = None

	def getapiname(self):
		return 'taobao.opencrm.card.effect.data.ytx'
