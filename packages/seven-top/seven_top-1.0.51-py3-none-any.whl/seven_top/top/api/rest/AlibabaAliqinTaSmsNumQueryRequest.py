'''
Created by auto_sdk on 2018.07.26
'''
from seven_top.top.api.base import RestApi
class AlibabaAliqinTaSmsNumQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.biz_id = None
		self.current_page = None
		self.page_size = None
		self.query_date = None
		self.rec_num = None

	def getapiname(self):
		return 'alibaba.aliqin.ta.sms.num.query'
