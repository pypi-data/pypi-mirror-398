from __future__ import absolute_import
import json
import os
import base64
import pyDes

from abc import ABC, abstractmethod
from typing import Dict, List, Any

work_dir = os.getcwd()
# 加载密钥信息
crypto_file = os.path.join(work_dir, 'crypto.json')
__crypto_params: Dict[str, Any] = {}

if os.path.exists(crypto_file):
    with open(crypto_file, "r+") as fn:
        __crypto_params = json.load(fn)

CRYPTO_CONST = '{crypto}'


def as_password_value(input: str):
    return _PasswordObject(input)


def as_crypto_value(input: str):
    if __crypto_params is None:
        raise RuntimeError('未找到配置文件解密密钥')
    return _CryptoObject(input, lambda x: __crypto_params)


def as_value(content: str, replacements: List[Any], security: bool):
    '''
    :param content 原生字符串
    :param replacements 找到的替换参数和参数值
    :param security 参数中是否包含敏感数据
    '''
    if security:
        return _CompositeObject(content, replacements)
    return _CompositeObject.format(content, replacements)


class SecurityObject(ABC):
    def __init__(self, data: str):
        super().__init__()
        self._data = data

    @abstractmethod
    def __str__(self) -> str:
        pass

    def __json__(self) -> str:
        return '***************'


class _CryptoObject (SecurityObject):
    def __init__(self, data: str, cb):
        super().__init__(data)
        self._cb = cb

    def __str__(self) -> str:
        o = self._cb()
        hex_key = base64.b64decode(o['key'])
        hex_iv = base64.b64decode(o['iv'])
        cipher_data = base64.b64decode(self._data)
        algo = pyDes.triple_des(
            hex_key, pyDes.CBC, IV=hex_iv, pad=None, padmode=pyDes.PAD_PKCS5)
        plain_text = str(algo.decrypt(cipher_data), 'utf-8')
        return plain_text

    # __repr__ = __str__


class _PasswordObject(SecurityObject):
    def __init__(self, data: str):
        super().__init__(data)

    def __str__(self):
        return str(self._data)

    # __repr__ = __str__


class _CompositeObject(SecurityObject):
    def __init__(self, content: str, replacements: List[Dict[str, Any]]):
        '''
        :param content 原生字符串
        :param replacements 找到的替换参数和参数值
        '''
        super().__init__(content)
        self.replacements = replacements

    def __str__(self) -> str:
        template = self._data
        return _CompositeObject.format(template, self.replacements, False)

    def __json__(self) -> str:
        template = self._data
        return _CompositeObject.format(template, self.replacements, True)

    @staticmethod
    def format(content: str, replacements: List[Any], json: bool = False):
        '''
        :param content 原生字符串
        :param replacements 找到的替换参数和参数值
        :param json
        '''
        result = content
        for item in replacements:
            expr: str = item['expr']
            value = item['value']
            text = value.__json__() if json and isinstance(value, SecurityObject) else str(value)
            result = result.replace(expr, text)
        return result
