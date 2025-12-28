'''
Created by auto_sdk on 2022.04.21
'''
from seven_top.top.api.base import RestApi
class OpencrmOrderRecordAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.order_record_dto = None

	def getapiname(self):
		return 'taobao.opencrm.order.record.add'
