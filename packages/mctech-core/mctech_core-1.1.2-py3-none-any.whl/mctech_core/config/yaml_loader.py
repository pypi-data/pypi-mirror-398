from __future__ import absolute_import
import re
import yaml
import os
from typing import Mapping

from log4py import logging
log = logging.getLogger('python.lib.configure.yamlLoader')

pattern = re.compile(r"\${([^{}]+)}")


def get_yaml_objects(file: str, params: Mapping[str, str]):
    if not os.path.exists(file):
        return []

    try:
        yaml_text = _prapare_variable(file, params)
        yaml_iter = yaml.safe_load_all(yaml_text)
        return list(yaml_iter)
    except Exception:
        log.error("Error loading YAML configuration file: %s" % file)
        raise


def _prapare_variable(file_name: str, params: Mapping[str, str]):
    with open(file_name, "r+", encoding="utf-8") as file:
        cfg = file.read()

    def _replacement(matched, params: Mapping[str, str]):
        text = str(matched.group(1))
        index = text.find(":")
        default_value = None
        if index > 0:
            var_name = text[0:index]
            default_value = text[index + 1:]
        else:
            var_name = text
        # 获取传入参数
        value = params.get(var_name)
        if value is None and default_value:
            # 设置默认值
            value = default_value

        if (value is None):
            error_msg = "未指定变量'%s'的默认值" % var_name
            raise RuntimeError(error_msg)
        return value

    text = pattern.sub(
        lambda matched: _replacement(matched, params), cfg)
    return text
