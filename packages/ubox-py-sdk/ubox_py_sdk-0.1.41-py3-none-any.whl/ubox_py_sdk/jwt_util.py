"""
JWT工具类

用于生成和验证JWT token，支持优测API的鉴权。
"""

import base64
import time
from typing import Optional

import jwt


class JWTUtil:
    """JWT工具类，用于生成优测API的鉴权token"""
    
    @staticmethod
    def generate_utest_token(sid: str, skey: str, expiration_hours: int = 24) -> str:
        """
        生成优测API鉴权token
        
        Args:
            sid: Secret ID
            skey: Secret Key
            expiration_hours: token过期时间（小时），默认24小时
            
        Returns:
            str: JWT token字符串
        """
        # 按照Java代码的逻辑：先base64编码，再base64解码得到字节数组
        # 1. 将secret key转为UTF-8字节数组
        skey_bytes = skey.encode('utf-8')
        # 2. 将字节数组进行base64编码得到字符串
        skey_base64_str = base64.b64encode(skey_bytes).decode('utf-8')
        # 3. 将base64字符串解码为字节数组（模拟Java的DatatypeConverter.parseBase64Binary）
        api_key_secret_bytes = base64.b64decode(skey_base64_str)
        
        # 计算过期时间
        now = int(time.time())
        expiration = now + (expiration_hours * 3600)
        
        # 构建payload
        payload = {
            'iss': sid,  # issuer
            'iat': now,  # issued at
            'exp': expiration,  # expiration
        }
        
        # 生成JWT token
        token = jwt.encode(
            payload,
            api_key_secret_bytes,
            algorithm='HS256',
            headers={'typ': 'JWT'}
        )
        
        return token
    
    @staticmethod
    def is_token_expired(token: str, skey: str, buffer_seconds: int = 300) -> bool:
        """
        检查token是否即将过期
        
        Args:
            token: JWT token字符串
            skey: Secret Key用于解码
            buffer_seconds: 提前多少秒认为过期，默认5分钟
            
        Returns:
            bool: True表示即将过期或已过期，False表示未过期
        """
        try:
            # 解码token获取过期时间
            # 按照Java代码的逻辑：先base64编码，再base64解码得到字节数组
            skey_bytes = skey.encode('utf-8')
            skey_base64_str = base64.b64encode(skey_bytes).decode('utf-8')
            api_key_secret_bytes = base64.b64decode(skey_base64_str)
            payload = jwt.decode(token, api_key_secret_bytes, algorithms=['HS256'])
            
            # 检查是否即将过期
            current_time = int(time.time())
            expiration_time = payload.get('exp', 0)
            
            return current_time >= (expiration_time - buffer_seconds)
            
        except jwt.InvalidTokenError:
            # 如果token无效，认为已过期
            return True
        except Exception:
            # 其他错误，认为已过期
            return True
