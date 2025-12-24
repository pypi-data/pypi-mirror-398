# JCer

## 项目描述

JCer 是一个基于 Python 和 Flask 的远程控制系统。它包括一个服务器端和一个客户端。服务器提供 Web 界面，用于管理连接的客户端。客户端可以捕获屏幕、记录键盘输入，并将数据发送到服务器。

## 功能特性

- 远程屏幕监控
- 远程命令执行
- 键盘输入记录
- 2FA 认证 (用户无法重新连接)
- Web 界面控制

## 安装

### 服务器端

1. 克隆或下载项目。
2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

   对于特定 Python 版本，使用相应的 requirements 文件（requirements_3.6.txt, requirements_3.7.txt, requirements_3.8.txt）。

### 客户端

客户端依赖在 `static/client/requirements.txt`。

1. 安装依赖：

   ```bash
   pip install -r static/client/requirements.txt
   ```

## 使用

### 运行服务器

设置环境变量 PASSWORD（可选，默认 123456）：

```bash
export PASSWORD=your_password
python server.py
```

服务器将在 http://localhost:5000 运行。

### 运行客户端

```bash
python static/client/client.py
```

客户端会扫描网络找到服务器并连接。

## 项目结构

- `server.py`: Flask 服务器应用
- `static/client/client.py`: 客户端脚本
- `static/`: 静态文件（CSS, JS 等）
- `requirements.txt`: 服务器依赖
- `static/client/requirements.txt`: 客户端依赖

## 注意事项

- 这是一个实验性项目，请谨慎使用。
- 确保网络安全，避免在不信任的环境中使用。
- 两因素认证使用 pyotp。

## 许可证

（请根据实际情况添加许可证信息）