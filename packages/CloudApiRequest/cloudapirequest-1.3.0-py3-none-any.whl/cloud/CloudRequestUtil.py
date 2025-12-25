import jsonpath
import requests
from urllib.parse import urlparse
from requests import Session


class CloudHttpClient:
    """
    对 requests 库进行简单封装的类，可以方便地进行 HTTP 请求和处理响应。
    """

    def __init__(self, base_url=None):
        """
        初始化方法，接受一个基础URL参数，并创建一个Session对象
        :param base_url: str 基础URL，例如 https://api.cloud.com
        """
        if base_url is not None:
            self.base_url = base_url

        self.session: Session = requests.Session()

    def request(self, method, url, **kwargs):
        """
        发送HTTP请求，并返回响应对象
        :param method: str 请求方法，例如 GET、POST、PUT等
        :param url: str 请求URL，会和base_url拼接成完整的URL
        :param kwargs: dict 其他requests.request方法支持的参数
        :return: requests.Response 响应对象
        """
        response = self.session.request(method, url, **kwargs)
        # 判断请求url 是否包含 openapi_login  用于处理 单点登录到系统后进行系统的接口请求鉴权处理
        # if 'openapi_login' in url:
        #     # 需要请求接口 获取 Tsessionid
        #     # 先从url 中解析出请求域名
        #     parsed_url = urlparse(url)
        #     domain = parsed_url.scheme + '://' + parsed_url.netloc
        #     # 进行接口请求 拿到响应
        #     personalResponse = self.session.request(method='GET', url=domain + '/api/personal/info/get')
        #     # 拿响应的$.result.authToken
        #     authToken = jsonpath.jsonpath(personalResponse.json(), '$.result.authToken')[0]
        #     # 后续的请求头上都需要带上 Tsessionid
        #     self.session.headers.update({'Tsessionid': authToken})
        
        # 处理HTTP错误
        http_error_msg = None
        if 400 <= response.status_code < 500:
            http_error_msg = (
                f"{response.status_code} 客户端错误 Error: {response.text} for url: {response.url}"
            )
        elif 500 <= response.status_code < 600:
            http_error_msg = (
                f"{response.status_code} 服务端错误 Error: {response.text} for url: {response.url}"
            )

        return response

    def get(self, url, params=None, **kwargs):
        """
        发送GET请求，并返回响应对象
        :param url: str 请求URL，会和base_url拼接成完整的URL
        :param params: dict 查询参数，会被转换为?key=value&key=value的形式拼接到URL后面
        :param kwargs: dict 其他requests.get方法支持的参数
        :return: requests.Response 响应对象
        """
        return self.request('GET', url, params=params, **kwargs)

    def post(self, url, json=None, data=None, **kwargs):
        """
        发送POST请求，并返回响应对象
        :param url: str 请求URL，会和base_url拼接成完整的URL
        :param data: dict 请求体参数，以表单形式提交
        :param json: dict 请求体参数，以JSON格式提交
        :param kwargs: dict 其他requests.post方法支持的参数
        :return: requests.Response 响应对象
        """
        return self.request('POST', url, data=data, json=json, **kwargs)

    def put(self, url, json=None, data=None, **kwargs):
        """
        发送PUT请求，并返回响应对象
        :param url: str 请求URL，会和base_url拼接成完整的URL
        :param data: dict 请求体参数，以表单形式提交
        :param json: dict 请求体参数，以JSON格式提交
        :param kwargs: dict 其他requests.put方法支持的参数
        :return: requests.Response 响应对象
        """
        return self.request('PUT', url, data=data, json=json, **kwargs)

    def delete(self, url, **kwargs):
        """
        发送DELETE请求，并返回响应对象
        :param url: str 请求URL，会和base_url拼接成完整的URL
        :param kwargs: dict 其他requests.delete方法支持的参数
        :return: requests.Response 响应对象
        """
        return self.request('DELETE', url, **kwargs)

    def patch(self, url, json=None, data=None, **kwargs):
        """
        发送PATCH请求，并返回响应对象
        :param url: str 请求URL，会和base_url拼接成完整的URL
        :param data: dict 请求体参数，以表单形式提交
        :param json: dict 请求体参数，以JSON格式提交
        :param kwargs: dict 其他requests.patch方法支持的参数
        :return: requests.Response 响应对象
        """
        return self.request('PATCH', url, data=data, json=json, **kwargs) 