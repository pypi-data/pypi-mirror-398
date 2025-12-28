# py_ctp

上期技术期货交易 api 之 python 封装，实现接口调用。支持 windows(x86/x64) linux(x64).

## 更新

v6.7.10.20250422 全函数封装

ctp 接口封装由 [ctp_generate](https://gitee.com/haifengat/ctp_generate) 生成

## 安装

```sh
pip install py-ctp==6.7.10.20250422
```

#### 示例

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
__title__ = 'test py ctp of se'
__author__ = 'HaiFeng'
__mtime__ = '20190506'

from py_ctp.trade import CtpTrade
from py_ctp.quote import CtpQuote
from py_ctp.enums import *
import time


class TestTrade(object):
    def __init__(self, addr: str, broker: str, investor: str, pwd: str, appid: str, auth_code: str, proc: str):
        self.front = addr
        self.broker = broker
        self.investor = investor
        self.pwd = pwd
        self.appid = appid
        self.authcode = auth_code
        self.proc = proc

        self.t = CtpTrade()
        self.t.OnConnected = self.on_connect
        self.t.OnUserLogin = lambda o, x: print('Trade logon:', x)
        self.t.OnDisConnected = lambda o, x: print(x)
        self.t.OnRtnNotice = lambda obj, time, msg: print(f'OnNotice: {time}:{msg}')
        self.t.OnErrRtnQuote = lambda obj, quote, info: None
        self.t.OnErrRtnQuoteInsert = lambda obj, o: None
        self.t.OnOrder = lambda obj, o: None
        self.t.OnErrOrder = lambda obj, f, info: None
        self.t.OnTrade = lambda obj, o: None
        self.t.OnInstrumentStatus = lambda obj, inst, stat: None

    def on_connect(self, obj):
        self.t.ReqUserLogin(self.investor, self.pwd, self.broker, self.proc, self.appid, self.authcode)

    def run(self):
        self.t.ReqConnect(self.front)
        # self.t.ReqConnect('tcp://192.168.52.4:41205')

    def release(self):
        self.t.ReqUserLogout()


class TestQuote(object):
    """TestQuote"""

    def __init__(self, addr: str, broker: str, investor: str, pwd: str):
        """"""
        self.front = addr
        self.broker = broker
        self.investor = investor
        self.pwd = pwd

        self.q = CtpQuote()
        self.q.OnConnected = lambda x: self.q.ReqUserLogin(self.investor, self.pwd, self.broker)
        self.q.OnUserLogin = lambda o, i: self.q.ReqSubscribeMarketData('rb2409')

    def run(self):
        self.q.ReqConnect(self.front)

    def release(self):
        self.q.ReqUserLogout()


if __name__ == "__main__":
    front_trade = 'tcp://180.168.146.187:10202'
    front_quote = 'tcp://180.168.146.187:10212'
    broker = '9999'
    investor = ''
    pwd = ''
    appid = ''
    auth_code = ''
    proc = ''
    if investor == '':
        investor = input('invesotr:')
        pwd = input('password:')
        appid = input('appid:')
        auth_code = input('auth code:')
        proc = input('product info:')
    tt = TestTrade(front_trade, broker, investor, pwd, appid, auth_code, proc)
```

## 发布到 PyPI

从 2023 年起，PyPI 不再支持用户名/密码认证，必须使用 API Token 或 Trusted Publishers。

### 方法一：使用 API Token（推荐）

1. 访问 [PyPI](https://pypi.org/manage/account/) 并登录
2. 进入 Account Settings 页面
3. 找到 "API tokens" 部分并点击 "Add API token"
4. 为 Token 添加描述（例如：py_ctp release）
5. 选择作用域（Scope），通常选择 "Upload packages"
6. 点击 "Add token" 并复制生成的 Token

有了 API Token 后，有两种使用方式：

#### 选项 1：使用 `.pypirc` 配置文件

创建或编辑 `~/.pypirc` 文件：

```ini
[pypi]
username = __token__
password = pypi-*******************************
```

将 `pypi-*******************************` 替换为你刚刚生成的实际 API Token。

然后正常执行发布命令：

```bash
rm dist -rf && python setup.py sdist && twine upload dist/*
```

#### 选项 2：使用命令行参数

```bash
rm dist -rf && python setup.py sdist && twine upload -u __token__ -p pypi-******************************* dist/*
```

### 方法二：使用 Trusted Publishers（适用于 GitHub Actions 等 CI/CD）

如果你使用 GitHub Actions 或其他 CI/CD 系统，可以配置 Trusted Publishers 实现自动发布。

详细信息请参考官方文档：

- [API Token 使用说明](https://pypi.org/help/#apitoken)
- [Trusted Publishers 使用说明](https://pypi.org/help/#trusted-publishers)
