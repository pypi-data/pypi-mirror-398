from cloud.CloudAPIRequest import CloudAPIRequest
from cloud.CloudApiConfig import config, CloudDataGenerator
from cloud.CloudRequestUtil import CloudHttpClient

# 创建config实例
config = config()
# 初始化配置实例
config.methObj = CloudDataGenerator()
config.Session = CloudHttpClient() 