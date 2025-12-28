'''
Created by auto_sdk on 2021.11.22
'''
from seven_top.top.api.base import RestApi
class OpencrmRuleCafullruleRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)

	def getapiname(self):
		return 'taobao.opencrm.rule.cafullrule'
