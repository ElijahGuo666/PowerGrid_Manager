import requests
import time
import uuid
from urllib.parse import urlencode
from typing import Dict, Optional, Any
from gmssl import sm3, func

import logging
logger = logging.getLogger(__name__)

class Sm3Utils:
    """
    SM3加密工具类
    提供SM3哈希加密功能
    """
    @staticmethod
    def encrypt(param_str: str) -> str:
        """
        SM3加密（结果大写）
        Args:
            param_str: 需要加密的字符串
        Returns:
            str: 大写格式的SM3哈希值
        """
        try:
            data_list = func.bytes_to_list(param_str.encode('utf-8'))
            return sm3.sm3_hash(data_list).upper()
        except Exception as e:
            raise ValueError(f"SM3加密失败: {str(e)}")

class ServiceClientV2:
    """
    服务客户端V2版本
    提供统一的API调用接口，支持签名验证、请求头构建等功能
    """
    def __init__(self, config: Dict[str, Any]):
        """
        初始化服务客户端
        Args:
            config: 配置字典，包含基础URL、应用密钥、服务代码等信息
        """
        # 基础配置
        self.base_url = config['base_url']
        self.app_key = config['app_key']
        self.app_secret = config['app_secret']
        self.service_code = config['service_code']
        self.version = config['version']
        
        # 请求参数
        self.path_params = config.get('path_params', {})
        self.query_params = config.get('query_params', {})
        self.form_data = config.get('form_data', {})
        self.raw_data = config.get('raw_data')
        self.headers = config.get('headers', {})
        
        # 客户端配置
        self.timeout = config.get('timeout', (30, 30))
        self.client_id = self.headers.get('X-Base-ClientId', '')
        self.client_code = self.headers.get('X-Base-ClientCode', '')

    def _generate_signature(self, timestamp: str, nonce: str) -> str:
        """
        生成请求签名
        Args:
            timestamp: 时间戳
            nonce: 随机数
        Returns:
            str: SM3签名值
        """
        sign_str = f"{timestamp}{self.app_secret}{nonce}{timestamp}"
        return Sm3Utils.encrypt(sign_str)

    def _build_headers(self, timestamp: str, nonce: str) -> Dict[str, str]:
        """
        构造请求头
        Args:
            timestamp: 时间戳
            nonce: 随机数
        Returns:
            dict: 请求头字典
        """
        return {
            'x-tif-signature': self._generate_signature(timestamp, nonce),
            'x-tif-timestamp': timestamp,
            'x-tif-nonce': nonce,
            'x-tif-paasid': self.app_key,
            'X-Base-ClientId': self.client_id,
            'X-Base-ClientCode': self.client_code,
            'X-Service-Code': self.service_code,
            'X-Version': self.version,
            **self.headers
        }

    def _build_url(self) -> str:
        """
        构造完整请求URL
        Returns:
            str: 完整的请求URL
        """
        # 处理路径参数
        service_path = self.service_code
        for key, value in self.path_params.items():
            service_path = service_path.replace(f'{{{key}}}', value)
        
        # 转换为路径格式
        service_path = service_path.replace('.', '/')
        
        # 构造基础URL
        full_url = f"{self.base_url.rstrip('/')}/{service_path}"
        
        # 添加查询参数
        if self.query_params:
            query_str = urlencode(self.query_params, doseq=True)
            full_url += f"?{query_str}"
        
        return full_url

    def execute(self) -> requests.Response:
        """
        执行请求
        Returns:
            requests.Response: HTTP响应对象
        """
        timestamp = str(int(time.time()))
        nonce = uuid.uuid4().hex
        
        try:
            # 构造请求要素
            url = self._build_url()
            headers = self._build_headers(timestamp, nonce)
            
            # 发送请求
            if self.raw_data is not None:
                response = requests.post(
                    url,
                    json=self.raw_data,
                    headers=headers,
                    timeout=self.timeout
                )
            elif self.form_data:
                response = requests.post(
                    url,
                    data=self.form_data,
                    headers=headers,
                    timeout=self.timeout
                )
            else:
                response = requests.post(
                    url,
                    headers=headers,
                    timeout=self.timeout
                )
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API请求失败: {str(e)}") from e

def invoker_test():
    """
    测试调用示例
    演示如何使用ServiceClientV2发送短信
    """
    config = {
        "base_url": "http://10.10.21.65/ebus/tsfehh6eaxxzxgateway/xxzx/xxzx/message-center-service-application/",
        "app_key": "e4a2237489d34ab0bed9f4c7aa7a50ff",
        "app_secret": "6Miz2kt3VhnO879fkEYJnnLdToUOAqAA",
        "service_code": "bs.mc.msb.service.send.sendElink",
        "version": "T.2023.12.30",
        "headers": {
            "X-Base-ClientId": "6c98bfd9c7ad811f591aa03eb1032ecf",
            "X-Base-ClientCode": "gxdw_nnj_rgzntyznt"
        },
        "raw_data": {"businessSysId": "gxdw_nnj_rgzntyznt",
            "messageId":"111111",
            "messageSendBatch":"000001",
            "content":"中台发送消息测试-zzt",
            "phone":"13800138000",
            "type":"text"
        }
    }
    
    try:
        client = ServiceClientV2(config)
        response = client.execute()
        
        print("调用成功")
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text[:500]}...")  # 限制输出长度
        
    except Exception as e:
        print(f"调用失败: {str(e)}")

def elink_push(phone,message):
    """
    发送短信消息
    Args:
        phone: 手机号码
        message: 短信内容
    Returns:
        tuple: (是否成功, 结果信息)
    """
    config = {
        "base_url": "http://10.10.21.65/ebus/tsfehh6eaxxzxgateway/xxzx/xxzx/message-center-service-application/",
        "app_key": "e4a2237489d34ab0bed9f4c7aa7a50ff",
        "app_secret": "6Miz2kt3VhnO879fkEYJnnLdToUOAqAA",
        "service_code": "bs.mc.msb.service.send.sendElink",
        "version": "T.2023.12.30",
        "headers": {
            "X-Base-ClientId": "6c98bfd9c7ad811f591aa03eb1032ecf",
            "X-Base-ClientCode": "gxdw_nnj_rgzntyznt"
        },
        "raw_data": {"businessSysId": "gxdw_nnj_rgzntyznt",
            "messageId":"11111133",
            "messageSendBatch":"000001",
            "content":message,
            "phone":phone,
            "type":"text"
        }
    }
    
    try:
        client = ServiceClientV2(config)
        response = client.execute()
        respdata = response.json()
        logger.debug(respdata)
        if "code" in respdata.keys() and respdata["code"] != "200":
            logger.error(f"调用失败: {str(respdata)}")
            if "当前手机号不存在对应用户" in respdata["msg"]:
                return (False,"phone")
            return (False,str(respdata))
        else:
            revokeid = respdata["jobId"]
            return (True,revokeid)

    except Exception as e:
        logger.error(f"调用失败: {str(e)}")
        return (False,str(e))

def elink_revoke(msgid):
    """
    撤销短信消息
    Args:
        msgid: 消息ID
    Returns:
        tuple: (是否成功, 结果信息)
    """
    config = {
        "base_url": "http://10.10.21.65/ebus/tsfehh6eaxxzxgateway/xxzx/xxzx/message-center-service-application/",
        "app_key": "e4a2237489d34ab0bed9f4c7aa7a50ff",
        "app_secret": "6Miz2kt3VhnO879fkEYJnnLdToUOAqAA",
        "service_code": "bs.mc.msb.service.send.revokeElink",
        "version": "T.2023.12.30",
        "headers": {
            "X-Base-ClientId": "6c98bfd9c7ad811f591aa03eb1032ecf",
            "X-Base-ClientCode": "gxdw_nnj_rgzntyznt"
        },
        "raw_data": {
            "jobId":msgid
        }
    }

    try:
        client = ServiceClientV2(config)
        response = client.execute()
        respdata = response.json()
        logger.debug(respdata)
        if "code" in respdata.keys() and respdata["code"] != "200":
            logger.error(f"调用失败: {str(respdata)}")
            return (False,str(respdata))
        else:
            return (True,"")

    except Exception as e:
        logger.error(f"调用失败: {str(e)}")
        return (False,str(e))

if __name__ == '__main__':
    # 测试发送短信
    print(elink_push("15240652309","111111"))
    # 测试撤销短信
    # print(elink_revoke("4_1745122855_679962"))


