# -*- coding: utf-8 -*-
'''
Created by auto_sdk on 2021.09.14 会员历史备份数据分页查询（隐私号版）
'''
from seven_top.top.api.base import RestApi
class TaobaoOpencrmMemberHismemberdataGetPrivy(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.page_size = 100
		self.current_page = 1
		# self.backup_ds = ""
		# self.end_time = ""
		# self.start_time = ""

	def getapiname(self):
		return 'taobao.opencrm.member.hismemberdata.get.privy'