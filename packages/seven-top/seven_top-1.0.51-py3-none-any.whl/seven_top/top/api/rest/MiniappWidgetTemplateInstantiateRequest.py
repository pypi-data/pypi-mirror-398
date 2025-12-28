'''
Created by auto_sdk on 2022.01.19
'''
from seven_top.top.api.base import RestApi
class MiniappWidgetTemplateInstantiateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.param_mini_app_instantiate_template_app_simple_request = None

	def getapiname(self):
		return 'taobao.miniapp.widget.template.instantiate'
