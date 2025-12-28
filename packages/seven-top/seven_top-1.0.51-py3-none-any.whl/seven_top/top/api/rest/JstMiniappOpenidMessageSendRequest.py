'''
Created by auto_sdk on 2020.12.02
'''
from seven_top.top.api.base import RestApi
class JstMiniappOpenidMessageSendRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.content = None
		self.crowd_code = None
		self.extend_num = None
		self.open_id = None
		self.seller_app_key = None
		self.sign_name = None
		self.template_code = None
		self.url = None

	def getapiname(self):
		return 'taobao.jst.miniapp.openid.message.send'
