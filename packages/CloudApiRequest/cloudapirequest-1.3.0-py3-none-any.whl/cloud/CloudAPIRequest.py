"""
cloud接口测试核心类
"""
import json
import os
import time
from urllib.parse import urlparse

import pytest
import allure
import jsonpath
from requests_toolbelt import MultipartEncoder
from cloud.CloudLogUtil import log
from cloud.CloudRequestUtil import CloudHttpClient
from cloud.CloudSignUtil import CloudSignUtil
from cloud.CloudYamlUtil import CloudReadYaml, CloudPlaceholderYaml
from cloud.CloudApiConfig import config


class CloudAPIRequest:
    """
    cloud接口测试核心类
    """

    def __init__(self, commonCase=None):
        """
        :param commonCase: 公共用例文件
        """
        self.commonCase = commonCase
        # 延迟初始化配置，避免循环导入
        self._config = None
        self.baseUrl = None
        self.token = None
        self.globalBean = None
        self.assertFail = 'stop'
        self.tenv = 'base'
    
    def _get_config(self):
        """延迟获取配置实例"""
        if self._config is None:
            from cloud import config
            self._config = config
            # 正确获取配置值，而不是property对象
            self.baseUrl = str(config._baseUrl) if hasattr(config, '_baseUrl') and config._baseUrl else None
            self.token = str(config._token) if hasattr(config, '_token') and config._token else None
            self.globalBean = config
            self.assertFail = str(config._assertFail) if hasattr(config, '_assertFail') and config._assertFail else 'stop'
            self.tenv = str(config._tEnv) if hasattr(config, '_tEnv') and config._tEnv else 'base'
        return self._config

    def doRequest(self, file, bean):
        """
        执行API请求测试
        """
        requestParameter = None
        dataSaveBean = bean
        yaml = CloudReadYaml(file).load_yaml()
        yamlId = yaml.get('id')
        yamlName = yaml.get('name')
        yamlTestcase = yaml.get('testcases')
        
        log.info(f"开始执行测试用例name: {yamlName}, id: {yamlId}")
        config_instance = self._get_config()
        clientSession = config_instance.Session
        
        for index, testcase in enumerate(yamlTestcase, 1):
            testcase_name = testcase.get('name', f'用例{index}')
            testcase_id = testcase.get('id', f'case_{index}')
            log.info(f"{'='*60}")
            log.info(f"正在执行第 {index} 个用例: {testcase_name} (ID: {testcase_id})")
            log.info(f"{'='*60}")
            
            with allure.step(testcase.get('name')):
                if testcase.get('skip'):
                    log.info(f"用例: {testcase.get('name')}跳过")
                    continue
                    
                sleeps = testcase.get('sleep')
                if sleeps:
                    time.sleep(int(sleeps))
                    log.info(f"当前用例: {testcase.get('name')}执行前等待{sleeps}秒")
                
                # 处理公共用例
                config_instance = self._get_config()
                if testcase.get('kind') and testcase.get('kind').lower() == 'common' and hasattr(config_instance, '_commonTestCasePath') and config_instance._commonTestCasePath is not None:
                    testcase = self.getCommonTestCase(testcase, config_instance._commonTestCasePath, testcase.get('id'))
                elif testcase.get('kind') and testcase.get('kind').lower() == 'common' and (not hasattr(config_instance, '_commonTestCasePath') or config_instance._commonTestCasePath is None):
                    log.error(f"commonPath路径未配置,请检查配置文件")
                    raise Exception(f"commonPath路径未配置,请检查配置文件")
                
                # 参数替换
                if testcase.get('requestType') is None:
                    requestType = 'json'
                else:
                    requestType = testcase.get('requestType')
                repParameter = self.replaceParameterAttr(dataSaveBean, testcase.get('parameter'), requestType)
                repApi = self.replaceParameterAttr(dataSaveBean, testcase.get('api'))
                headers = self.replaceParameterAttr(dataSaveBean, testcase.get('headers'))
                
                # 鉴权处理
                requestParameter, requestUrl, authHeaders = self.authType(testcase.get('authType'), repApi, testcase.get('method'), repParameter)
                
                # 请求类型处理
                dataRequestParameter, jsonRequestParameter, paramsData, ModelData, requestType = self.requestType(requestType, requestParameter)
                
                # 合并请求头
                if headers:
                    headers.update(authHeaders)
                else:
                    headers = authHeaders
                
                # 执行请求
                
                if dataRequestParameter is not None and requestType.lower() in ['form-data', 'form-file']:
                    headers['Content-Type'] = dataRequestParameter.content_type
                
                # 调试日志：打印实际发送的JSON数据
                if jsonRequestParameter is not None:
                    log.info(f"发送的JSON数据: {json.dumps(jsonRequestParameter, ensure_ascii=False)}")
                    log.info(f"JSON数据类型: {type(jsonRequestParameter)}")
                    if isinstance(jsonRequestParameter, dict):
                        for key, value in jsonRequestParameter.items():
                            log.info(f"  {key}: {value} (类型: {type(value)})")
                
                if testcase.get('stream_check'):
                    response = self.handle_stream_response(clientSession, testcase.get('method'), requestUrl, dataRequestParameter, jsonRequestParameter, paramsData, ModelData, headers)
                else:
                    response = clientSession.request(method=testcase.get('method'), url=requestUrl, data=dataRequestParameter, json=jsonRequestParameter, params=paramsData, files=ModelData, headers=headers)
                
                # 记录响应
                try:
                    response_json = response.json()
                    # 打印响应状态码
                    log.info(f"[{testcase_name}] 响应状态码: {response.status_code}")
                    # 打印完整的响应结果
                    log.info(f"[{testcase_name}] 响应结果: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
                except json.JSONDecodeError as e:
                    log.error(f"[{testcase_name}] JSON解析失败: {e}")
                    log.error(f"[{testcase_name}] 原始响应内容: {response.text}")
                    response_json = None
                except Exception as e:
                    log.error(f"[{testcase_name}] 响应处理异常: {e}")
                    response_json = None
                
                # 处理断言
                if testcase.get('assertFail'):
                    failtype = testcase.get('assertFail')
                else:
                    failtype = self.assertFail
                self.assertType(testcase.get('assert'), response, dataSaveBean, failtype)
                
                # 保存数据
                try:
                    if response_json is not None:
                        self.addAttrSaveBean(dataSaveBean, self.globalBean, testcase.get('saveData'), response_json)
                    else:
                        log.warning(f"[{testcase_name}] 响应不是JSON格式，跳过数据保存")
                except Exception as e:
                    log.error(f"[{testcase_name}] 数据保存异常: {e}")
                    self.addAttrSaveBean(dataSaveBean, self.globalBean, testcase.get('saveData'), response.text)
        
        return clientSession

    def assertType(self, assertType, response, bean, failType):
        """
        处理断言
        """
        if assertType is None:
            log.info(f"断言为空,跳过断言")
            return None
        
        for ass in assertType:
            key = list(ass.keys())[0]
            
            if 'status_code' in ass:
                if ass.get('status_code'):
                    self.assertChoose(str(response.status_code) == str(ass.get('status_code')), 
                                   f"status_code断言失败: {ass.get('status_code')}  ,response结果: {response.status_code}", failType)
                    continue
            
            # 安全地解析JSON响应
            try:
                response_data = response.json()
                jsonpathResults = jsonpath.jsonpath(response_data, ass.get(key)[0])
            except json.JSONDecodeError:
                # 尝试解析JSONP格式
                try:
                    response_text = response.text
                    # 检查是否是JSONP格式：callback(json_data)
                    if '(' in response_text and ')' in response_text:
                        # 提取JSON部分
                        start = response_text.find('(') + 1
                        end = response_text.rfind(')')
                        json_str = response_text[start:end]
                        
                        # 处理JSONP中的字符串转义（单引号包围的JSON）
                        if json_str.startswith("'") and json_str.endswith("'"):
                            json_str = json_str[1:-1]  # 移除首尾的单引号
                        
                        response_data = json.loads(json_str)
                        log.info(f"成功解析JSONP格式响应: {json_str}")
                        jsonpathResults = jsonpath.jsonpath(response_data, ass.get(key)[0])
                    else:
                        raise json.JSONDecodeError("不是JSONP格式", response_text, 0)
                except (json.JSONDecodeError, ValueError) as e:
                    log.error(f"JSON和JSONP解析都失败，无法执行断言: {ass.get(key)[0]}")
                    log.error(f"原始响应内容: {response.text}")
                    self.assertChoose(False, f"响应不是有效的JSON或JSONP格式，无法执行断言: {ass.get(key)[0]}", failType)
                    continue
            except Exception as e:
                log.error(f"断言处理异常: {e}")
                self.assertChoose(False, f"断言处理异常: {e}", failType)
                continue
                
            if jsonpathResults is False and 'not_found' not in ass:
                self.assertChoose(1 > 2, f"提取{ass.get(key)[0]}失败，断言失败", failType)
                continue
            
            if 'eq' in ass:
                expectedResults = CloudPlaceholderYaml(attrObj=bean, reString=ass.get('eq')[1]).replace().replaced_str
                assResults = str(expectedResults) in [str(item) for item in jsonpathResults]
                self.assertChoose(assResults is True, f"eq断言失败: {jsonpathResults} 不等于 {expectedResults}", failType)
            elif 'neq' in ass:
                expectedResults = CloudPlaceholderYaml(attrObj=bean, reString=ass.get('neq')[1]).replace().replaced_str
                assResults = str(expectedResults) not in [str(item) for item in jsonpathResults]
                self.assertChoose(assResults is True, f"neq断言失败: {jsonpathResults} 等于 {expectedResults}", failType)
            elif 'sge' in ass:
                expectedResults = CloudPlaceholderYaml(attrObj=bean, reString=ass.get('sge')[1]).replace().replaced_str
                self.assertChoose(len(jsonpathResults) >= int(expectedResults), f"sge断言失败: {jsonpathResults} 小于 {expectedResults}", failType)
            elif 'nn' in ass:
                self.assertChoose(jsonpathResults is not None, f"not none断言失败: {ass.get('nn')[0]}", failType)
            elif 'none' in ass:
                self.assertChoose(jsonpathResults is True, f"none断言失败: {ass.get('none')[0]}", failType)
            elif 'not_found' in ass:
                self.assertChoose(jsonpathResults is False, f"not_found断言失败,字段存在", failType)
            elif 'in' in ass:
                expectedResults = CloudPlaceholderYaml(attrObj=bean, reString=ass.get('in')[1]).replace().replaced_str
                self.assertChoose(str(expectedResults) in str(jsonpathResults), f"断言in失败: {expectedResults} 不在 {jsonpathResults} 内", failType)
            elif 'len' in ass:
                expectedResults = CloudPlaceholderYaml(attrObj=bean, reString=ass.get('len')[1]).replace().replaced_str
                jsonpathResults_len = len(jsonpathResults[0])
                self.assertChoose(jsonpathResults_len == int(expectedResults), f"断言len失败: {jsonpathResults_len} 长度不等于 {expectedResults}", failType)
            elif 'contains' in ass:
                expectedResults = CloudPlaceholderYaml(attrObj=bean, reString=ass.get('contains')[1]).replace().replaced_str
                self.assertChoose(str(expectedResults) in str(jsonpathResults), f"断言contains失败: {expectedResults} 不在 {jsonpathResults} 内", failType)

    def addAttrSaveBean(self, bean, globalBean, data: list, response):
        """
        保存响应数据到Bean
        """
        if data is None:
            return
        for d in data:
            if 'json' in d:
                jsonPath = d.get('json')[1]
                value = jsonpath.jsonpath(response, jsonPath)
                if value is False:
                    value = None
                
                saveBean = bean
                if d.get('json').__len__() == 3 and d.get('json')[2].lower() == 'global':
                    saveBean = globalBean
                
                key_parts = d.get('json')[0].split(':')
                d.get('json')[0] = key_parts[0]
                
                if value is not None and len(value) > 1:
                    setattr(saveBean, d.get('json')[0], list(value))
                elif value is not None and len(value) == 1:
                    if len(key_parts) > 1 and key_parts[1].lower() == 'str':
                        value[0] = str(value[0])
                    setattr(saveBean, d.get('json')[0], value[0])

    def replaceParameterAttr(self, bean, parameter, requestType='json'):
        """
        替换参数中的占位符
        """
        if parameter is None:
            return None
        
        # 获取配置实例
        config_instance = self._get_config()
        
        if requestType.lower() == 'json-text':
            repParameter = CloudPlaceholderYaml(yaml_str=parameter, attrObj=bean, methObj=config_instance.methObj, gloObj=config_instance).replace().textLoad()
        else:
            repParameter = CloudPlaceholderYaml(yaml_str=parameter, attrObj=bean, methObj=config_instance.methObj, gloObj=config_instance).replace().jsonLoad()
        
        return repParameter

    def requestType(self, requestType, data):
        """
        处理请求类型
        """
        jsonRequestParameter = None
        dataRequestParameter = None
        paramsData = None
        ModelData = None
        
        if isinstance(data, dict) and data.get('MIME'):
            MIME = data.get('MIME')
        else:
            MIME = 'application/octet-stream'
            
        if requestType is None:
            jsonRequestParameter = data
        elif requestType.lower() in ["json", "json-text"]:
            jsonRequestParameter = data
        elif requestType.lower() == "form-data":
            dataRequestParameter = MultipartEncoder(fields=data)
        elif requestType.lower() == "form-model":
            filename = data['filename']
            file_name = data[filename].split('\\')
            data[filename] = (file_name[-1], open(data[filename], 'rb'), MIME)
            for k, v in data.items():
                if type(v) == dict:
                    data[k] = (None, json.dumps(data[k]))
            ModelData = data
        elif requestType.lower() == "form-file":
            filename = data['filename']
            data[filename] = (os.path.basename(data[filename]), open(data[filename], 'rb'), MIME)
            dataRequestParameter = MultipartEncoder(fields=data)
        elif requestType == "PARAMS":
            paramsData = data
        elif requestType == "DATA":
            dataRequestParameter = data
        else:
            log.error("请求方式不支持")
            
        return dataRequestParameter, jsonRequestParameter, paramsData, ModelData, requestType

    def authType(self, authType, url, method, parameter):
        """
        处理鉴权方式
        """
        if self.baseUrl is None or self.isValidUrl(url):
            requestUrl = url
        else:
            requestUrl = self.baseUrl + url
        requestParameter = None
        authHeaders = {}
        
        if authType == "SIGN":
            # 云服务MD5签名鉴权
            config_instance = self._get_config()
            # 从config中获取企业ID
            enterprise_id = config_instance._enterpriseId if hasattr(config_instance, '_enterpriseId') else None
            if not enterprise_id:
                log.error("企业ID未配置，请在环境配置中设置enterpriseId")
                raise ValueError("企业ID未配置，请在环境配置中设置enterpriseId")
            
            if method.upper() == "GET":
                # GET请求：将签名参数添加到URL参数中
                # 添加默认的validateType参数
                if parameter is None:
                    parameter = {}
                if 'validateType' not in parameter:
                    parameter['validateType'] = config_instance._validateType if hasattr(config_instance, '_validateType') else '2'  # 从配置中获取验证类型
                
                signed_params = CloudSignUtil.generate_params_with_signature(
                    enterprise_id=enterprise_id,
                    token=config_instance._token if hasattr(config_instance, '_token') else None,
                    additional_params=parameter
                )
                # 构建带签名的URL
                from urllib.parse import urlencode
                query_string = urlencode(signed_params)
                if '?' in requestUrl:
                    requestUrl += '&' + query_string
                else:
                    requestUrl += '?' + query_string
                requestParameter = None
                log.info(f"GET请求URL: {requestUrl}")
            else:
                # POST/PUT/PATCH请求：签名信息放在请求头中，但URL中也需要包含签名参数
                # 添加签名参数到URL查询参数中
                url_params = {
                    'validateType': config_instance._validateType if hasattr(config_instance, '_validateType') else '2',
                    'enterpriseId': enterprise_id,
                    'timestamp': int(time.time()),
                    'sign': CloudSignUtil.generate_md5_signature(
                        enterprise_id, 
                        int(time.time()), 
                        config_instance._token if hasattr(config_instance, '_token') else None
                    )
                }
                
                # 如果parameter中包含validateType，使用parameter中的值
                if parameter and 'validateType' in parameter:
                    url_params['validateType'] = parameter.pop('validateType')
                
                # 构建URL（包含所有签名参数）
                from urllib.parse import urlencode
                query_string = urlencode(url_params)
                if '?' in requestUrl:
                    requestUrl += '&' + query_string
                else:
                    requestUrl += '?' + query_string
                log.info(f"POST请求URL: {requestUrl}")
                
                # 生成请求头签名（包含请求体内容）
                authHeaders = CloudSignUtil.generate_headers(
                    method=method,
                    url=requestUrl,
                    params=None,  # POST请求不需要URL参数签名
                    enterprise_id=enterprise_id,
                    token=config_instance._token if hasattr(config_instance, '_token') else None,
                    body=parameter
                )
                requestParameter = parameter
            
            return requestParameter, requestUrl, authHeaders
        elif authType == "COOKIE" or authType is None:
            requestParameter = parameter
            return requestParameter, requestUrl, authHeaders
        else:
            log.error("鉴权方式不支持")
        return requestParameter, requestUrl, authHeaders

    def getCommonTestCase(self, testcase, commonFile, caseId):
        """
        获取公共测试用例
        """
        if self.commonCase is None:
            commonFile = commonFile
        else:
            commonFile = os.path.join(commonFile.split('common')[0], f'common/{self.commonCase}')
        
        yaml = CloudReadYaml(commonFile).load_yaml()
        commonCase = yaml.get('testcases')
        
        for case in commonCase:
            if case.get('id') == caseId:
                case['assert'] = [item for item in (case.get('assert') or []) + (testcase.get('assert') or []) if item is not None]
                case['saveData'] = [item for item in (case.get('saveData') or []) + (testcase.get('saveData') or []) if item is not None]
                return case
        
        raise ValueError("Case with id {} not found".format(caseId))

    def assertChoose(self, ass, tips, type):
        """
        断言选择器
        """
        if type == 'stop':
            assert ass, tips
        elif type == 'continue':
            pytest.assume(ass, tips)

    def isValidUrl(self, url):
        """
        验证URL是否有效
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def handle_stream_response(self, clientSession, method, url, data, json_data, params, files, headers):
        """
        处理流式响应
        """
        try:
            response_dict = {}
            answer_count = 0
            complete_message = ""

            with clientSession.request(
                    method=method,
                    url=url,
                    data=data,
                    json=json_data,
                    params=params,
                    files=files,
                    headers=headers,
                    stream=True
            ) as response:
                for chunk in response.iter_lines():
                    if chunk:
                        data = chunk.decode('utf-8')
                        if data.startswith('data: '):
                            try:
                                json_str = data[6:]
                                if json_str.strip() == '[DONE]':
                                    if complete_message:
                                        response_dict["complete_message"] = complete_message
                                    continue

                                json_data = json.loads(json_str)

                                if 'answer' in json_data:
                                    answer_count += 1
                                    key = f"answer{answer_count}"
                                    response_dict[key] = json_data

                                    answer_content = json_data.get('answer', '')
                                    if isinstance(answer_content, list):
                                        answer_content = ''.join(str(item) for item in answer_content)
                                    elif not isinstance(answer_content, str):
                                        answer_content = str(answer_content)

                                    complete_message += answer_content

                            except json.JSONDecodeError as e:
                                log.error(f"JSON解析错误: {e}")
                                continue

                response.json = lambda: response_dict
                response._content = json.dumps(response_dict).encode()
                return response

        except Exception as e:
            log.error(f"流式处理错误: {e}")
            raise 