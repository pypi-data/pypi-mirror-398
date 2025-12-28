'''
Created by auto_sdk on 2018.07.26
'''
from seven_top.top.api.base import RestApi
class AlibabaAliqinTaNumberSinglecallbyttsRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.called_num = None
		self.called_show_num = None
		self.params = None
		self.tts_code = None

	def getapiname(self):
		return 'alibaba.aliqin.ta.number.singlecallbytts'
