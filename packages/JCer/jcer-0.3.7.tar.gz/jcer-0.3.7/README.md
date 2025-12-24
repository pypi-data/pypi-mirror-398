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

1. 安装依赖：

   ```bash
   pip install JCer[server]
   ```

### 客户端

1. 安装依赖：

   ```bash
   pip install JCer[client]
   ```

## 使用

### 运行服务器

设置环境变量 PASSWORD（可选，默认 123456）：

```bash
export PASSWORD=your_password
jcer-server
```

服务器将在 http://localhost:5000 运行。

### 运行客户端

```bash
jcer-client
```

客户端会扫描网络找到服务器并连接。

## 注意事项

- 确保网络安全，避免在不信任的环境中使用。
- 两因素认证使用 pyotp。

## 许可证

MIT License

Copyright (c) 2025 YANGRENRUIYRR

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
