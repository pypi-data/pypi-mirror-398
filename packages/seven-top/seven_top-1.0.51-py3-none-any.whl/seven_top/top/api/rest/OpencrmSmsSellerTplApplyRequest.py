'''
Created by auto_sdk on 2023.03.01
'''
from seven_top.top.api.base import RestApi
class OpencrmSmsSellerTplApplyRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.request_list = None

	def getapiname(self):
		return 'taobao.opencrm.sms.seller.tpl.apply'
