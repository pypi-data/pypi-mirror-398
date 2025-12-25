项目名称

Cloud API自动化测试框架,封装requests库.使用Yaml文件管理测试用例,支持数据驱动,支持多环境配置,支持多线程执行,支持测试报告生成.

当前版本 https://pypi.org/project/CloudApiRequest/

## 项目结构

```
├── dist # 打包目录 版本发布
├── test # 测试目录 测试类
├── cloud # 源码目录 框架源码
```

## 运行条件

Python 3.7+

```
pip install -r requirements.txt 
```

完成依赖安装

## 快速开始

```
进行测试
pytest -s
pytest -s ./testcase --env=bj  --tenv=gray -n=2   --alluredir ./result

--env   环境配置
-n      多线程执行
--alluredir allure报告生成目录

查看报告
allure serve ./result
.result 为allure报告生成目录
```

## 开发方式

导入cloudrequest库
```
pip install CloudApiRequest-v*.whl
```

更新版本
```
pip uninstall CloudApiRequest
pip install CloudApiRequest-v*.whl
```

引用CloudApiRequest
```
from cloud import config
# 平台与运行环境选择
def pytest_addoption(parser):
    parser.addoption(
        "--env", action="store", default="test", help="test：表示测试环境，默认测试环境"
    )
    parser.addoption(
        "--tenv", action="store", default="gray", help="tenv：表示蓝绿环境，默认gray灰度环境"
    )
# 配置环境
config.baseUrl = envConfig.urlPath   # 基础请求地址
config.token = envConfig.token  # token
config.commonTestCasePath = os.path.join(DATA_JSON_PATH, "common.yaml")   # common 公共用例路径
config.methObj=method() # 用于自定义"#{fun}"方法调用的函数 ,不想使用sdk自带的方法时,可以自定义方法,在yaml中使用
config.session=request.Session() # 用于传递请求session实体类,可以传递cookies
config.tEnv = request.config.getoption("tenv")  # 运行环境选择

```

```
from cloud import CloudAPIRequest
# 执行测试 传入yamlFile文件路径 传入Test_pyt测试类 也可以使用自定义commonfile文件，不是用全局配置的commonfile。直接写yaml文件即可
CloudAPIRequest('cloud_api.yaml').doRequest(yamlFile,Test_pyt)
```

## 用例示例

```yaml
id: create_client  # 用例id
name: 示例测试用例 # 用例名称
testcases: # 测试用例步骤 # 
  - sleep: 1 # 等待时间
  - skip: 1 # 跳过步骤
  - kind: common #用例类型  common去取公共用例,需要公共用例路径
    id: getQueues
    name: 获取队列信息
  - name: 查找队列信息 # 步骤名称
    id: list_queues # 步骤id
    api: /list_queues #  请求地址 # todo: 支持变量地址 ${args}
    headers: # 请求头 # todo: 支持变量
      Content-Type: application/json
      User-Agent: Chrome$${browser_version}
    authType: SIGN # 鉴权方式  SIGN  COOKIE   # todo AUTH bear xxx
    method: GET # GET  POST
    requestType: JSON  # JSON FORM FORM-DATA FORM-FILE FROM-MODEL JSON-TEXT # todo PARAMS
    stream_check: true  # 启用流式检查  默认为false或者不写  启用流式检查后，会将response中的answer字段进行拼接，返回完整的answer字段。
    parameter: # 请求参数 '#{}'取FAKER模拟数据方法   '${}' 取缓存变量  # todo '$${}' 取global变量  todo 方法传参数
      offset: 0
      limit: '#{get_sk_password}'  # 获取环境变量里 SK 加密密码
      cno: '#{random_number(args)}' # 生成随机数
      name: '[${queues}]'
      names: '$${names}'
      file: '..\..\..\data\files\知识图谱导出文件-物价编码.xlsx'  # 该字段填写 上传文件的相对路径 配合form-data使用
      MIME: 'image/gif'  # 该字段填写 文件的MIME类型 配合form-data使用
      model:  # 该字段 工单模块 使用多。上传文件使用
        "operator": 1223
        "content": "213213"
        "type": 1
      filename: file  # 该字段仅限于 FORM-FILE FROM-MODEL 使用  值为 文件入参字段
    assertFail: stop、continue  # 断言失败处理模式 stop程序直接终止 continue断言失败仍运行。默认为stop
    assert: # 断言 eq neq sge # todo 支持多个断言 eq ne gt lt ge le seq sne sgt slt sge sle in
      - status_code: 201
      - eq: [ '$.pageSize', '${size}' ]  # 判断 返回值 是否等于 预期
      - neq: [ '$.pageSize', '10' ]  # 判断 返回值 是否不等于 预期
      - sge: [ '$.queues[:2].id', 2 ]  # 判断 返回值数量 是否大于等于 预期
      - none : ['$.error']   # 判断 返回值 是否为空
      - nn: ['$.error']      # 判断 返回值 是否不为空
      - in: ['$.pageSize', '$${size}'] # 判断 返回值 是否包含 预期
      - not_found: [ '$.pageSize', ]  # 判断 指定数据是否不存在
      - len: [ '$.pageSize', 4 ]  # 判断 指定数据的长度
    saveData: # 缓存变量  global变量 #todo cookie变量 header变量  request变量
      - json: [ 'queues:str','$.queues[:2].id'] #:str 指定获取的值 type为str，暂不支持其他类型，有需要可提出优化。
      - json: [ 'names','$.name' ,'global']


  - name: 创建座席
    id: create_client
    api: ```````
```