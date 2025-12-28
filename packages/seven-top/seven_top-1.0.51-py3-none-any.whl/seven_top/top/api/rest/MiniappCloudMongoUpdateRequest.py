'''
Created by auto_sdk on 2020.09.17
'''
from seven_top.top.api.base import RestApi
class MiniappCloudMongoUpdateRequest(RestApi):
    def __init__(self,domain='gw.api.taobao.com',port=80):
        RestApi.__init__(self,domain, port)
        self.collection = None
        self.filter = None
        self.record = None
        self.env = None

    def getapiname(self):
        return 'taobao.miniapp.cloud.mongo.update'
