'''
Author: LiuXin
Date: 2024-01-30 21:35:38
LastEditTime: 2024-01-31 16:13:55
LastEditors: LiuXin
Description: 
'''
'''
Created by auto_sdk on 2021.09.14
'''
from seven_top.top.api.base import RestApi
class TaobaoMiniappCrmConnectRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.bizValue = None
		self.buyer = None
		self.createTime = None
		self.description = None
		self.eventType = None
		self.messageId = None
		self.seller = None
		self.shopId = None

	def getapiname(self):
		return 'qimen.taobao.miniapp.crm.connect'
