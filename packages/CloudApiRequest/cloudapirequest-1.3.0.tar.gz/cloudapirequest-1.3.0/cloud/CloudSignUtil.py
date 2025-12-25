import hashlib
import time

from cloud.CloudLogUtil import log


class CloudSignUtil:
    """
    cloud签名工具类 - 基于MD5的签名算法
    鉴权方式：MD5({enterpriseId}+{timestamp}+{token})
    """
    
    @staticmethod
    def _generate_md5_hash(sign_string):
        """
        生成MD5签名的内部方法
        :param sign_string: 签名字符串
        :return: 32位小写MD5签名
        """
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_md5_signature(enterprise_id, timestamp, token):
        """
        生成MD5签名（按企业编号）
        :param enterprise_id: 企业ID
        :param timestamp: 时间戳
        :param token: 访问token
        :return: 32位小写MD5签名
        """
        # 构建签名字符串：{enterpriseId}+{timestamp}+{token}
        sign_string = f"{enterprise_id}{timestamp}{token}"
        return CloudSignUtil._generate_md5_hash(sign_string)
    
    @staticmethod
    def generate_md5_signature_by_validate_type(validate_type, enterprise_id, department_id, timestamp, token):
        """
        根据验证类型生成MD5签名
        :param validate_type: 验证类型 (1=部门编号, 2=企业编号)
        :param enterprise_id: 企业ID
        :param department_id: 部门编号
        :param timestamp: 时间戳
        :param token: 访问token
        :return: 32位小写MD5签名
        """
        if validate_type == 1:
            # validateType=1时，sign=MD5({departmentId}+{timestamp}+{部门token值})
            sign_string = f"{department_id}{timestamp}{token}"
        else:
            # validateType=2时，sign=MD5({enterpriseId}+{timestamp}+{企业token值})
            sign_string = f"{enterprise_id}{timestamp}{token}"
        
        signature = CloudSignUtil._generate_md5_hash(sign_string)
        log.info(f"签名计算: validateType={validate_type}, sign_string={sign_string}, signature={signature}")
        
        return signature
    
    @staticmethod
    def generate_headers(method, url, params, enterprise_id, token, body=None):
        """
        生成云服务请求头 - 基于MD5签名
        :param method: 请求方法
        :param url: 请求URL
        :param params: 查询参数
        :param enterprise_id: 企业ID
        :param token: 访问token
        :param body: 请求体（用于POST/PUT请求）
        :return: 请求头字典
        """
        # 获取当前时间戳（秒级）
        timestamp = int(time.time())
        
        # 生成MD5签名
        signature = CloudSignUtil.generate_md5_signature(enterprise_id, timestamp, token)
        
        # 构建请求头
        headers = {
            'Authorization': f"Cloud {token}:{signature}",
            'X-Timestamp': str(timestamp),
            'Content-Type': 'application/json',
            'User-Agent': 'CloudAPISDK/1.0'
        }
        
        # 添加企业ID到请求头（如果需要）
        headers['X-Enterprise-Id'] = str(enterprise_id)
        
        return headers
    
    @staticmethod
    def generate_params_with_signature(enterprise_id, token, additional_params=None):
        """
        生成带签名的请求参数
        :param enterprise_id: 企业ID
        :param token: 访问token
        :param additional_params: 额外参数
        :return: 包含签名的参数字典
        """
        # 获取当前时间戳（秒级）
        timestamp = int(time.time())
        
        # 检查验证类型
        validate_type = 2  # 默认按企业编号验证
        department_id = None
        
        if additional_params:
            validate_type = int(additional_params.get('validateType', 2))
            department_id = additional_params.get('departmentId')
        
        # 根据验证类型生成签名
        if validate_type == 1 and department_id:
            # 按部门编号验证
            signature = CloudSignUtil.generate_md5_signature_by_validate_type(
                validate_type, enterprise_id, department_id, timestamp, token
            )
        else:
            # 按企业编号验证
            signature = CloudSignUtil.generate_md5_signature(enterprise_id, timestamp, token)
        
        # 构建基础参数
        params = {
            'enterpriseId': enterprise_id,
            'timestamp': timestamp,
            'sign': signature
        }
        
        # 添加额外参数
        if additional_params:
            params.update(additional_params)
        
        return params
    
    @staticmethod
    def validate_signature(enterprise_id, timestamp, token, received_signature):
        """
        验证签名
        :param enterprise_id: 企业ID
        :param timestamp: 时间戳
        :param token: 访问token
        :param received_signature: 接收到的签名
        :return: 验证结果
        """
        # 生成期望的签名
        expected_signature = CloudSignUtil.generate_md5_signature(enterprise_id, timestamp, token)
        
        # 比较签名
        is_valid = expected_signature == received_signature
        
        log.info(f"签名验证结果: {is_valid}")
        log.info(f"期望签名: {expected_signature}")
        log.info(f"接收签名: {received_signature}")
        
        return is_valid 