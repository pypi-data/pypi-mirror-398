from flask import Flask, request, jsonify, render_template_string, make_response, redirect
import os
from waitress import serve
import base64
import pyotp
import hashlib
import time

app = Flask(__name__)
contents = {}
password = os.environ.get("PASSWORD", "123456")
screen_data = {}
screen_time = {}
get_2fa_times = {}
list_2fa_keys = {}
last_2fa_keys = {}
command_queue = {}
offline = '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'
disconnected = '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'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_FILES = {
    "tailwind.js": {
        "path": os.path.join(APP_ROOT, "static\\js\\tailwind.js"),
        "content_type": "application/javascript; charset=utf-8",
        "binary": False
    },
    "font-awesome.min.css": {
        "path": os.path.join(APP_ROOT, "static\\css\\font-awesome.min.css"),
        "content_type": "text/css; charset=utf-8",
        "binary": False
    },
    "webfonts/fa-solid-900.woff2": {
        "path": os.path.join(APP_ROOT, "static\\webfonts\\fa-solid-900.woff2"),
        "content_type": "font/woff2",
        "binary": True
    },
    "webfonts/fa-solid-900.ttf": {
        "path": os.path.join(APP_ROOT, "static\\webfonts\\fa-solid-900.ttf"),
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
        screen_time[client_ip] = time.time()
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
    if screen_time.get(ip,0) == 0:
        return jsonify({"code": 200, "data": offline}), 200
    if time.time() - screen_time.get(ip, 0) > 1:
        return jsonify({"code": 200, "data": disconnected}), 200
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
