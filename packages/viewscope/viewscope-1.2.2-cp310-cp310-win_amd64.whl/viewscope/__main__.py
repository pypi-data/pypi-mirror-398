"""
ViewScope命令行入口
"""

import sys
import signal
import threading
import subprocess
import webbrowser
import socket
import time
import uiautomator2 as u2
import uvicorn


def find_available_port(start_port=8060, max_attempts=10):
    """寻找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        try:
            # 尝试连接端口，如果连接失败说明端口可用
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result != 0:  # 连接失败，端口可用
                return port
        except Exception:
            # 异常也表示端口可用
            return port
    return None


def init_uiautomator2():
    """初始化uiautomator2到设备"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        if result.returncode != 0:
            return False

        lines = result.stdout.strip().split('\n')[1:]
        devices = [line.split('\t')[0] for line in lines if line.strip() and '\t' in line]

        if not devices:
            return True  # 继续启动

        for device_id in devices:
            try:
                u2.connect(device_id)
            except Exception:
                pass

        return True

    except Exception:
        return False


def open_browser(port):
    """打开浏览器"""
    def delayed_open():
        time.sleep(3)
        try:
            webbrowser.open(f"http://localhost:{port}")
        except Exception:
            pass

    thread = threading.Thread(target=delayed_open)
    thread.daemon = True
    thread.start()


def signal_handler(signum, frame):
    """信号处理"""
    print("\nShutting down...")
    sys.exit(0)


def main():
    """主入口函数"""
    print("=" * 50)
    print("ViewScope - Android UI Inspector")
    print("=" * 50)

    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)

    # 初始化uiautomator2
    init_uiautomator2()

    # 寻找可用端口
    available_port = find_available_port()
    if not available_port:
        print("Error: No available port found")
        return 1

    # 显示访问信息
    print(f"\nViewScope running at: http://localhost:{available_port}")
    print(f"API docs: http://localhost:{available_port}/docs")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    # 自动打开浏览器
    open_browser(available_port)

    try:
        uvicorn.run(
            "viewscope.main:app",
            host="0.0.0.0",
            port=available_port,
            reload=False,
            access_log=False
        )
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())