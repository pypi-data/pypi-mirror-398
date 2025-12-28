from setuptools import setup
import os
from os import path as os_path

this_directory = os_path.abspath(os_path.dirname(__file__))


# 读取文件内容
def read_file(filename):
    desc = ""
    with open(os_path.join(this_directory, filename), encoding="utf-8") as f:
        desc = f.read()
    return desc


# 获取依赖
def read_requirements(filename):
    return [line.strip() for line in read_file(filename).splitlines() if not line.startswith("#")]


# 删除无用文件
path = f"./py_ctp/lib64"
for f in os.listdir(path):
    if os.path.isdir(f):
        continue
    if os.path.splitext(f)[1] not in [".dll", ".so"]:
        os.remove(f"./py_ctp/lib64/{f}")

long_description = read_file("setup.md")

# 虚拟环境
#   python -m venv tutorial-env
# source tutorial-env/bin/activate
# 安装信赖
#   pip install --upgrade setuptools wheel keyring twine pipreqs
# 生成 requirements.txt
#   pipreqs --encoding=utf8 --force py_ctp
# 安装 .tar.gz
#   rm dist -rf && python setup.py sdist && twine upload dist/*
# 安装 .whl
#   rm dist -rf && python setup.py bdist_wheel && twine upload dist/*.whl
#
# 注意: 从 2025年10月开始，PyPI 不再支持用户名/密码认证，必须使用 API Token 认证
# 方法1: 使用 ~/.pypirc 配置文件
#   在 ~/.pypirc 文件中添加如下配置:
#   [pypi]
#   username = __token__
#   password = pypi-*** (你的API Token)
# 方法2: 使用命令行参数
#   twine upload -u __token__ -p pypi-*** dist/*
# 方法3: 使用 keyring 存储凭证
#   keyring set https://upload.pypi.org/legacy/ __token__
#
setup(
    name="py_ctp",  # 包名
    python_requires=">=3.6.0",  # python环境
    version="6.7.10.20250424",
    description="Python CTP futures api",  # 包简介，显示在PyPI上
    long_description=long_description,  # 读取的Readme文档内容
    long_description_content_type="text/markdown",  # 指定包文档格式为markdown
    author="HaiFengAT",  # 作者相关信息
    author_email="haifengat@vip.qq.com",
    url="https://github.com/haifengat/pyctp",
    # library_dirs = ['/usr/lib'],
    # extra_link_args.append（'-Wl，-rpath，'+ lib_path）
    # 指定包信息，还可以用find_packages()函数
    # packages=find_packages(),
    packages=["py_ctp"],
    install_requires=read_requirements("requirements.txt"),  # 指定需要安装的依赖
    include_package_data=True,
    license="MIT License",
    platforms="any",
    # 只在Linux系统下安装动态库文件
    data_files=["README.md", ("/usr/lib/py_ctp", ["py_ctp/lib64/thostmduserapi_se.so", "py_ctp/lib64/thosttraderapi_se.so"])] if os.name == "posix" else [],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
