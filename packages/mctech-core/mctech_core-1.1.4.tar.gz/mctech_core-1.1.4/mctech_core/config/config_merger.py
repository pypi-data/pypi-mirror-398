from __future__ import absolute_import
import os
import re
import functools
from . import config_value as vals

from typing import Dict, Mapping, Any, List, Optional
from log4py import logging

from .config_value import SecurityObject

log = logging.getLogger('python.lib.configure.merge')


ARRAY_INDEX_PATTERN = re.compile("\\[\\d+\\]$")
INTERNAL_PARAM_PATTERN = re.compile("\\$\\(([.\\w-]+)(#(\\w+))??\\)")


def config_merge(target: Dict[str, Any], source: Dict[str, Any], type: str):
    '''
    添加配置项，每一个同名的配置项都对应着一个数组，每一个数组成员的type都不同，来自不同的配置源
    :param key 配置项的key
    :param value 配置项的值
    :param type 配置项的类型，表示来自哪一种数据源
    '''
    for name, src_value in source.items():
        if src_value is None:
            continue

        index = None
        if ARRAY_INDEX_PATTERN.search(name):
            # 形如下面格式的数组
            # a.b.c[0]: 123
            # a.b.c[1]: 456
            start = name.rindex('[')
            index = name[start + 1:-1]
            index = int(index)
            name = name[0:start]

        target_value: Optional[Any] = target.get(name)

        if isinstance(index, int):
            # 合并数组中的一项
            # 处理形如下面的配置格式
            #    a.b.c[0]: 'value'
            # 此时取到的name = 'c', index = 0, value = 'value'
            # 找到targe中数组配置的值的对象
            if target_value is None:
                target_value = TypedList()
                target_value.item_type = 'array'
                target[name] = target_value

            _merge_plain_array(target_value, src_value, type, index)
        else:
            if isinstance(src_value, Dict):
                # 最终生成的json对象中非叶子节点都是object类型，不用数组表示
                # 叶子节点每个值都是数组，表示从各个配置源得到的值，最终使用的是索引为0的值
                # 非叶子节点
                if target_value is None:
                    target_value = {}
                    target[name] = target_value
                elif not isinstance(target_value, Dict):
                    error_msg = "配置段类型不匹配. source:%s, target:%s" % (
                        src_value, target_value)
                    raise RuntimeError(error_msg)
                config_merge(target_value, src_value, type)
            else:
                # 叶子节点或json格式的数组对象
                src_type = 'array' if isinstance(src_value, List) else 'simple'
                if target_value is None:
                    target_value = TypedList()
                    target[name] = target_value
                    target_value.item_type = src_type
                try:
                    target_type = target_value.item_type
                    if target_type != src_type:
                        error_msg = "合并的类型不一致, name: %s, sourceType: %s, sourceType: %s" % (  # noqa
                            name, target_type, src_type)
                        raise RuntimeError(error_msg)

                    # 插入到最前面
                    target_value.insert(0, {
                        'type': type,
                        'value': src_value
                    })
                except Exception:
                    log.error(
                        "合并配置时发生错误：targetValue: %s, source=%s, target=%s" % (
                            target_value, source, target)
                    )
                    raise


def _merge_plain_array(target_value, source_value, type: str, index: int):
    '''
    :param targetValue
    :param sourceValue
    :param type 配置所属的类型
    :param index
    '''
    array_value = None
    # 找到type 相同的项
    for config_item in target_value:
        if config_item["type"] == type:
            array_value = config_item.get("value")

    if array_value is None:
        array_value = TypedList()
        target_value.insert(0, {
            'type': type,
            'value': array_value
        })

    if len(array_value) != index:
        raise RuntimeError('合并数组配置必须按下标顺序合并，当前数组长度为%d，要合并的下标为%d' %
                           (len(array_value), index))
    if isinstance(source_value, Dict):
        val: Dict[str, Any] = {}
        # 如果数组中每一项都是对象，递归处理，避免最终结果中出现带[0]这样的属性
        config_merge(val, source_value, type)
        array_value.append(val)
    else:
        array_value.append(source_value)


def process_source(source: Dict[str, Any], params: Mapping[str, Any]):
    return process_object(source, params)


def process_object(obj: Dict[str, Any], params: Mapping[str, Any]):
    for key, value in obj.items():
        obj[key] = process_value(value, params)
    return obj


def process_array(arr: List[Any], params: Mapping[str, Any]):
    for i in range(0, len(arr)):
        arr[i] = process_value(arr[i], params)
    return arr


def process_value(value: Any, params: Mapping[str, Any]):
    if isinstance(value, list):
        value = process_array(value, params)
    elif isinstance(value, dict):
        value = process_object(value, params)
    elif isinstance(value, str):
        value = _resolve_internal_variable(value, params)
    return value


__DEFAULT_RDB_PATTERN = re.compile('rdb.(default|yearrow).')


def _resolve_internal_variable(content: Optional[str], params: Mapping[str, str]):
    if not content:
        return content

    replacements: List[Dict[str, Any]] = []
    security = False
    product_line = os.environ.get('PRODUCT_LINE')
    matcher = INTERNAL_PARAM_PATTERN.search(content)
    while matcher:
        expr: str = matcher.group(0)
        key: str = matcher.group(1)
        param_type: str = matcher.group(3)
        if param_type is None:
            param_type = 'string'
        value: Any = None

        # 根据产品线替换rdb.default的数据库配置
        if product_line and __DEFAULT_RDB_PATTERN.match(key):
            ns_key = __DEFAULT_RDB_PATTERN.sub(f'rdb.product-line.{product_line}.', key)
            value = params.get(ns_key)

        if value is None:
            value = params[key]
        if value is None:
            raise RuntimeError("未指定变量'%s'的值" % key)

        val_type = 'string'
        if isinstance(value, bool):
            val_type = 'boolean'
        elif isinstance(value, int):
            val_type = 'number'

        if val_type != param_type and (param_type != 'password' or val_type != 'string'):
            raise RuntimeError(
                "%s类型参数的传入值不正确. key: %s, type: %s" % (
                    param_type, key, val_type)
            )
        wrap = value
        if (val_type == 'string' and isinstance(value, str)):
            if (value.startswith(vals.CRYPTO_CONST)):
                input = value[len(vals.CRYPTO_CONST):]
                wrap = vals.as_crypto_value(input)
            wrap = vals.as_password_value(str(wrap)) if param_type == 'password' else wrap  # noqa

        if not security and isinstance(wrap, SecurityObject):
            security = True

        replacements.append({'expr': expr, 'key': key, 'value': wrap})
        matcher = INTERNAL_PARAM_PATTERN.search(content, matcher.end())

    if len(replacements) == 0:
        # 不存在参数
        return content

    if len(replacements) == 1:
        # 等于于一个参数
        r = replacements[0]
        if r['expr'] == content:
            # 整个字符串完全匹配一个参数，直接返回参数的原始值
            return r['value']

    # 含有敏感数据，封装成对象
    return vals.as_value(content, replacements, security)


class TypedList(List):
    def __init__(self, *args):
        super().__init__(args)
        self.item_type: Optional[str] = None


def resolve_params(target: Dict[str, Any], params: Dict[str, str]):
    param_refs = list()
    keys = list(params.keys())
    for key in keys:
        value = params.get(key)
        if not isinstance(value, str):
            # 只有字符串类型才检查参数的级联引用，其它类型直接保存下来
            target[key] = value
            continue
        matcher = INTERNAL_PARAM_PATTERN.search(value)
        if matcher is None:
            target[key] = value
            continue

        # 找出参数引用关系
        item = {'key': key, 'refs': list()}
        param_refs.append(item)
        while matcher is not None:
            item['refs'].append(matcher.group(1))
            matcher = INTERNAL_PARAM_PATTERN.search(value, matcher.end())

    def cmp(a, b):
        if b['key'] in a['refs']:
            return 1
        if a['key'] in b['refs']:
            return -1
        return 0

    param_refs.sort(key=functools.cmp_to_key(cmp))

    for param_ref in param_refs:
        key = param_ref['key']
        expr = params.get(key)
        value = _resolve_internal_variable(expr, target)
        target[key] = value
