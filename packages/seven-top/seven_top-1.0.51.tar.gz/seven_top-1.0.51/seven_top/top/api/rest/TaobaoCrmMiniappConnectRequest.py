'''
Author: LiuXin
Date: 2024-01-30 21:35:38
LastEditTime: 2024-01-31 16:13:04
LastEditors: LiuXin
Description: 
'''
'''
Created by auto_sdk on 2021.09.17
'''
from seven_top.top.api.base import RestApi
class TaobaoCrmMiniappConnectRequest(RestApi):
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
		self.target_appkey = None

	def getapiname(self):
		return 'qimen.taobao.crm.miniapp.connect'
