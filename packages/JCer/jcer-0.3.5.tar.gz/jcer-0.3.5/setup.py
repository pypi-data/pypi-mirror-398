import setuptools
import sys

DistutilsError=RuntimeError

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()
def check_install_extras():
    # 获取pip安装的命令行参数
    install_cmd = None
    for idx, arg in enumerate(sys.argv):
        if arg in ["install", "develop", "editable"]:
            install_cmd = arg
            # 检查后续参数是否包含extras（如[client]、[server]、[all]）
            if idx + 1 < len(sys.argv):
                next_arg = sys.argv[idx + 1]
                if "[" in next_arg and any(x in next_arg for x in ["client", "server", "all"]):
                    return  # 已指定分组，正常执行
            # 未检测到extras分组，抛出错误
            raise DistutilsError(
                "\n❌ 必须指定安装类型！请使用以下命令之一：\n"
                "  pip install JCer[client]   # 仅安装客户端\n"
                "  pip install JCer[server]   # 仅安装服务器端\n"
                "  pip install JCer[all]      # 全量安装（客户端+服务器端）"
            )

# 执行校验（仅在install/develop/editable命令时触发）
if any(cmd in sys.argv for cmd in ["install", "develop", "editable"]):
    try:
        check_install_extras()
    except DistutilsError as e:
        print(e)
        sys.exit(1)  # 退出并返回错误码

setuptools.setup(
    name="JCer",
    version="0.3.5",
    author="YANGRENRUIYRR",
    author_email="yangrenruiyrr@yeah.net",
    description="A package for remote control with screen capture and input handling",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YANGRENRUIYRR/JCer",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires='>=3.6',
    install_requires=[
        
    ],
    extras_require={
        "[client]":[
            "certifi>=2025.4.26",
            "charset-normalizer>=2.0.0",
            "idna>=3.10",
            "ipaddress>=1.0.23",
            "mss>=7.0.1",
            "pillow>=8.4.0",
            "pynput>=1.8.1",
            "requests>=2.27.1",
            "six>=1.17.0",
            "urllib3>=1.26.20",
        ],
        "[server]":[
            "blinker>=1.5",
            "click>=7.1.2",
            "colorama>=0.4.5",
            "Flask>=1.1.4",
            "itsdangerous>=1.1.0",
            "Jinja2>=2.11.3",
            "MarkupSafe>=2.0.1",
            "pyotp>=2.7.0",
            "waitress>=2.0.0",
            "Werkzeug>=1.0.1",
        ],
        "[all]":[
            "blinker>=1.5",
            "click>=7.1.2",
            "colorama>=0.4.5",
            "Flask>=1.1.4",
            "itsdangerous>=1.1.0",
            "Jinja2>=2.11.3",
            "MarkupSafe>=2.0.1",
            "pyotp>=2.7.0",
            "waitress>=2.0.0",
            "Werkzeug>=1.0.1",
            "certifi>=2025.4.26",
            "charset-normalizer>=2.0.0",
            "idna>=3.10",
            "ipaddress>=1.0.23",
            "mss>=7.0.1",
            "pillow>=8.4.0",
            "pynput>=1.8.1",
            "requests>=2.27.1",
            "six>=1.17.0",
            "urllib3>=1.26.20",
        ],
        ":python_version == '3.6'": [
            "blinker==1.5",
            "click==7.1.2",
            "colorama==0.4.5",
            "dataclasses==0.8",
            "Flask==1.1.4",
            "importlib-metadata==4.8.3",
            "itsdangerous==1.1.0",
            "Jinja2==2.11.3",
            "MarkupSafe==2.0.1",
            "pyotp==2.7.0",
            "typing-extensions==4.1.1",
            "waitress==2.0.0",
            "Werkzeug==1.0.1",
            "zipp==3.6.0",
            "certifi==2025.4.26",
            "charset-normalizer==2.0.0",
            "idna==3.10",
            "ipaddress==1.0.23",
            "mss==7.0.1",
            "Pillow==8.4.0",
            "pynput==1.8.1",
            "requests==2.27.1",
            "six==1.17.0",
            "urllib3==1.26.20",
        ],
        ":python_version == '3.7'": [
            "blinker==1.5",
            "click==7.1.2",
            "colorama==0.4.5",
            "Flask==1.1.4",
            "importlib-metadata==4.8.3",
            "itsdangerous==1.1.0",
            "Jinja2==2.11.3",
            "MarkupSafe==2.0.1",
            "pyotp==2.7.0",
            "typing-extensions==4.1.1",
            "waitress==2.0.0",
            "Werkzeug==1.0.1",
            "zipp==3.6.0",
            "certifi==2025.4.26",
            "charset-normalizer==2.0.0",
            "idna==3.10",
            "ipaddress==1.0.23",
            "mss==7.0.1",
            "Pillow==8.4.0",
            "pynput==1.8.1",
            "requests==2.27.1",
            "six==1.17.0",
            "urllib3==1.26.20",
        ],
        ":python_version == '3.8'": [
            "blinker==1.5",
            "click==7.1.2",
            "colorama==0.4.5",
            "Flask==1.1.4",
            "importlib-metadata==4.8.3",
            "itsdangerous==1.1.0",
            "Jinja2==2.11.3",
            "MarkupSafe==2.0.1",
            "pyotp==2.7.0",
            "typing-extensions==4.1.1",
            "waitress==2.0.0",
            "Werkzeug==1.0.1",
            "zipp==3.6.0",
            "certifi==2025.4.26",
            "charset-normalizer==2.0.0",
            "idna==3.10",
            "ipaddress==1.0.23",
            "mss==7.0.1",
            "Pillow==8.4.0",
            "pynput==1.8.1",
            "requests==2.27.1",
            "six==1.17.0",
            "urllib3==1.26.20",
        ],
    },
    include_package_data=True,
    package_data={
        'JCer': ['static/**/*'],
    },
    entry_points={
        "gui_scripts": [
            "jcer-server = JCer.server:main",
            "jcer-client = JCer.client:main"
        ],
    },
)