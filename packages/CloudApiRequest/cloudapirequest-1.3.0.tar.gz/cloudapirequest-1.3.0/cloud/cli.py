#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud API SDK 命令行工具
"""

import argparse
import sys
import os
from cloud_api_sdk import config, CloudAPIRequest


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='Cloud API SDK 测试工具')
    parser.add_argument('testcase', help='测试用例文件路径')
    parser.add_argument('--base-url', help='基础URL')
    parser.add_argument('--access-key-id', help='访问密钥ID')
    parser.add_argument('--access-key-secret', help='访问密钥Secret')
    parser.add_argument('--cloud-password', help='云服务密码')
    parser.add_argument('--env', default='test', help='运行环境')
    parser.add_argument('--common-path', help='公共用例路径')
    parser.add_argument('--assert-fail', default='stop', choices=['stop', 'continue'], help='断言失败处理模式')
    
    args = parser.parse_args()
    
    # 配置环境
    if args.base_url:
        config.baseUrl = args.base_url
    if args.access_key_id:
        config.accessKeyId = args.access_key_id
    if args.access_key_secret:
        config.accessKeySecret = args.access_key_secret
    if args.cloud_password:
        config.CloudPassword = args.cloud_password
    if args.common_path:
        config.commonTestCasePath = args.common_path
    config.assertFail = args.assert_fail
    config.tEnv = args.env
    
    # 检查测试用例文件是否存在
    if not os.path.exists(args.testcase):
        print(f"错误: 测试用例文件 {args.testcase} 不存在")
        sys.exit(1)
    
    # 执行测试
    try:
        class TestRunner:
            pass
        
        test_runner = TestRunner()
        CloudAPIRequest().doRequest(args.testcase, test_runner)
        print("测试执行完成")
    except Exception as e:
        print(f"测试执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 