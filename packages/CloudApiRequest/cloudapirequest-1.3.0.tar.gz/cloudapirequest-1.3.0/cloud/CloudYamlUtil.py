import re
import yaml
import json
from cloud.CloudLogUtil import log
from cloud.CloudApiConfig import config


class CloudPlaceholderYaml:
    """
    用于替换yaml文件中的占位符
    """

    def __init__(self, yaml_str=None, reString=None, attrObj=config, methObj=None, gloObj=config):
        if yaml_str:
            self.yaml_str = json.dumps(yaml_str)
        else:
            self.yaml_str = str(reString)

        self.attrObj = attrObj
        
        # 修复methObj的初始化逻辑
        if methObj is not None:
            self.methObj = methObj
        elif hasattr(config, 'methObj') and config.methObj is not None:
            self.methObj = config.methObj
        else:
            # 如果都没有，创建一个默认的CloudDataGenerator实例
            from cloud.CloudApiConfig import CloudDataGenerator
            self.methObj = CloudDataGenerator()
            log.warning("methObj未配置，使用默认的CloudDataGenerator实例")
        
        self.gloObj = gloObj

    def replace(self):
        # 定义正则表达式模式
        # 用于匹配 ${attr} 和 #{method} 这样的占位符
        # $() #() 如果不匹配则报错
        pattern_attr = re.compile(r'\$\{(\w+)\}')
        pattern_method = re.compile(r'\#\{(.*?)\}')
        pattern_glo = re.compile(r'\$\$\{(\w+)\}')

        # 定义全局替换函数
        def replace_glo(match):
            # 获取占位符中的属性名
            attr_name = match.group(1)
            # 如果对象中有该属性，则返回该属性的值
            if hasattr(self.gloObj, attr_name):
                # 获取属性的值
                attr_value = getattr(self.gloObj, attr_name)
                # 如果属性的值是字符串，则返回该字符串
                if isinstance(attr_value, str):
                    return str(attr_value)
                # 如果属性的值是可调用对象，则返回方法名
                elif callable(attr_value):
                    return match.group(0)
                # 如果属性的值是字典，则返回该字典的字符串表示
                elif isinstance(attr_value, dict):
                    return str(attr_value)
                # 如果属性的值是列表，则返回该列表的字符串表示
                elif isinstance(attr_value, list):
                    return str(",".join(str(x) for x in attr_value))
                # 否则，返回属性的值（将其转换为字符串）
                else:
                    return str(attr_value)
            # 否则返回原字符串
            return match.group(0)

        # 定义替换函数
        def replace_attr(match):
            # 获取占位符中的属性名
            attr_name = match.group(1)
            # 如果对象中有该属性，则返回该属性的值
            if hasattr(self.attrObj, attr_name):
                # 获取属性的值
                attr_value = getattr(self.attrObj, attr_name)
                # 如果属性的值是字符串，则返回该字符串
                if isinstance(attr_value, str):
                    return str(attr_value)
                # 如果属性的值是可调用对象，则返回方法名
                elif callable(attr_value):
                    return match.group(0)
                # 如果属性的值是字典，则返回该字典的字符串表示
                elif isinstance(attr_value, dict):
                    return str(attr_value)
                # 如果属性的值是列表，则返回该列表的字符串表示
                elif isinstance(attr_value, list):
                    return str(",".join(str(x) for x in attr_value))
                # 否则，返回属性的值（将其转换为字符串）
                else:
                    return str(attr_value)
            # 否则返回原字符串
            return match.group(0)

        # 定义替换函数
        def replace_method(match):
            # 获取占位符中的方法名
            method_name = match.group(1)
            args = None
            if '(' in match.group(1):
                # 获取占位符中的方法名
                method_name = match.group(1).split('(')[0]
                # 获取参数列表
                args_str = match.group(1).split('(')[1][:-1]
                args = [arg.strip() for arg in args_str.split(',')]

            # 如果对象中有该方法，并且该方法是可调用的，则返回该方法的返回值
            if hasattr(self.methObj, method_name):
                # 获取方法
                method = getattr(self.methObj, method_name)
                # 如果方法是可调用对象，则调用该方法并返回其返回值的字符串表示
                if callable(method):
                    try:
                        if args:
                            method_value = method(*args)
                        else:
                            method_value = method()
                        if isinstance(method_value, str):
                            return str(method_value)
                        else:
                            return str(method_value)
                    except Exception as e:
                        log.error(f"调用方法 {method_name} 时出错: {e}")
                        return match.group(0)
                # 否则，返回方法的字符串表示
                else:
                    return str(method)
            else:
                log.warning(f"方法 {method_name} 在 methObj 中不存在，methObj类型: {type(self.methObj)}")
                log.warning(f"methObj 可用方法: {[attr for attr in dir(self.methObj) if not attr.startswith('_')]}")
            # 否则返回原字符串
            return match.group(0)

        # 判断是否有需要替换的再进行替换
        log.info(f"开始替换str中的占位符: {self.yaml_str}")
        log.info(f"使用的methObj: {type(self.methObj)}")
        # 先进行全局替换
        replaced_str = pattern_glo.sub(replace_glo, self.yaml_str)
        # 替换占位符中的属性
        replaced_str = pattern_attr.sub(replace_attr, replaced_str)
        # 替换占位符中的方法
        replaced_str = pattern_method.sub(replace_method, replaced_str)
        self.replaced_str = replaced_str
        log.info("替换后的str内容为：{}".format(replaced_str))
        return self

    def jsonLoad(self):
        # 先将单引号替换为双引号，None替换为null
        temp_str = self.replaced_str.replace("'", "\"").replace('None', 'null')
        
        # 在解析之前，检测并保护JSON字符串参数
        # 查找模式："key": "{...}" 或 "key": "[...]"
        # 将内部的引号转义，使其成为合法的JSON字符串
        def escape_json_string_values(match):
            key = match.group(1)
            json_str = match.group(2)
            # 转义内部的双引号
            escaped_json_str = json_str.replace('"', '\\"')
            return f'"{key}": "{escaped_json_str}"'
        
        # 匹配 "key": "{...}" 或 "key": "[...]" 的模式
        # 使用非贪婪匹配，并且只匹配value部分被双引号包裹的情况
        # .*? 可以匹配包含双引号的内容
        pattern = r'"(\w+)"\s*:\s*"(\{.*?\}|\[.*?\])"'
        temp_str = re.sub(pattern, escape_json_string_values, temp_str)
        log.info(f"转义后的字符串: {temp_str[:300]}")
        
        try:
            # 尝试直接解析
            parsed_result = json.loads(temp_str)
            log.info("替换后jsonLoad的str内容为：{}".format(parsed_result))
            return parsed_result
        except json.JSONDecodeError as e:
            # 如果直接解析失败，尝试旧的替换逻辑（兼容旧用例）
            log.warning(f"JSON解析失败: {e}, 尝试旧的替换逻辑")
            try:
                replaced_str = self.replaced_str.replace('"[', '[').replace(']"', ']').replace('"{', '{').replace('}"', '}').replace("'", "\"").replace('None','null')
                replaced_str = json.loads(replaced_str)
                log.info("替换后jsonLoad的str内容为：{}".format(replaced_str))
                return replaced_str
            except:
                log.info(f'*************替换失败-YAML,请检查格式{replaced_str}******************')

    def textLoad(self):
        return json.loads(self.replaced_str)


class CloudReadYaml:
    """
    用于读取yaml文件的工具类
    """

    def __init__(self, yaml_file):
        self.yaml_file = yaml_file

    def load_yaml(self):
        """
        读取yaml文件，并返回其中的数据
        :return: dict
        """
        with open(self.yaml_file, encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data if data is not None else {}  # 如果data为None，则返回空字典

    def get(self, key, default=None):
        """
        获取yaml文件中的数据
        :param key: 数据的键
        :param default: 如果获取失败，则返回该默认值
        :return: dict
        """
        # 读取yaml文件
        data = self.load_yaml()
        # 获取数据
        return data.get(key, default) if data is not None else default

    def get_all(self):
        """
        获取yaml文件中的所有数据
        :return: dict
        """
        # 读取yaml文件
        data = self.load_yaml()
        # 如果data为None，则返回空字典
        return data if data is not None else {} 