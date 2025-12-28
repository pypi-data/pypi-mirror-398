# 部署包说明

注意以下pip，python均表示的是3.x以上的python

## 本地源码安装部署包

```bash
pip install log4py
python {pack}_setup.py install
```

## 生成部署包并上传pypi

```bash
pip install wheel twine
# 构建源码包和二进制wheel包
python mctech_actuator_setup.py clean --all sdist bdist_wheel
python mctech_cloud_setup.py clean --all sdist bdist_wheel
python mctech_core_setup.py clean --all sdist bdist_wheel
python mctech_discovery_setup.py clean --all sdist bdist_wheel
# 上传pypi
twine upload dist/*
```
