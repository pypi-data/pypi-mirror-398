"""
设备管理核心模块
基于已有的DeviceManager进行扩展，专门用于View Scope
"""

import asyncio
import time
import socket
import ipaddress
from typing import Dict, List, Optional
from datetime import datetime
import uiautomator2 as u2
import subprocess
import concurrent.futures
import imagehash
from PIL import Image
import io
import base64
import logging
import re

# 设置日志
logger = logging.getLogger(__name__)

# QNX设备管理器
class QNXDeviceManager:
    """QNX系统设备管理器 - 使用QNXMirror通过ADB+Telnet连接"""
    
    def __init__(self, login_config: List[Dict] = None):
        """
        初始化QNX设备管理器
        
        Args:
            login_config: 登录配置列表，格式如：
                [
                    {"step": "adb shell", "assertword": "#", "input": None},
                    {"step": "/vendor/bin/busybox telnet 192.168.8.1", "assertword": "login:"},
                    {"step": "root", "assertword": "#"}
                ]
        """
        # 默认登录配置
        if login_config is None:
            login_config = [
                {
                    "step": "adb shell",
                    "assertword": "#",
                    "input": None  # 特殊标记，不发送命令只等待提示符
                },
                {
                    "step": "/vendor/bin/busybox telnet 192.168.8.1",
                    "assertword": "login:"
                },
                {
                    "step": "root",  # 用户名
                    "assertword": "Password:"  # 等待密码提示
                },
                {
                    "step": "",  # 密码（空密码，直接回车）
                    "assertword": "#"  # 登录后的提示符
                }
            ]
        
        self.login_config = login_config
        self.qnx_mirror = None
        self.is_connected = False
        self.device_id = "qnx_adb_telnet"
        self.last_screenshot = None
        self.last_screenshot_hash = None
        self.logger = logger
    
    def connect(self):
        """建立QNX连接（通过ADB+Telnet）"""
        try:
            # 导入QNXMirror类
            from core.qnx_manager import QNXMirror
            
            # 创建QNXMirror实例
            self.qnx_mirror = QNXMirror(
                login_config=self.login_config,
                timeout=60,
                encoding='utf-8'
            )
            
            # 建立连接
            success = self.qnx_mirror.con()
            
            if success:
                self.is_connected = True
                self.logger.info(f"QNX connected: {self.device_id}")
            else:
                self.is_connected = False
                raise Exception("QNX connection failed")

        except Exception as e:
            self.is_connected = False
            self.logger.error(f"QNX connection error: {e}")
            raise e
    
    def disconnect(self):
        """断开QNX连接"""
        try:
            if self.qnx_mirror:
                self.qnx_mirror._cleanup()
                self.qnx_mirror = None
            
            self.is_connected = False
            self.logger.info(f"QNX disconnected: {self.device_id}")

        except Exception as e:
            self.logger.warning(f"QNX disconnect warning: {e}")
    
    def execute_screenshot(self) -> bytes:
        """执行QNX截图命令"""
        if not self.is_connected or not self.qnx_mirror:
            raise Exception("QNX连接未建立")
        
        try:
            # 执行QNX Screen截图命令
            screenshot_path = "/tmp/qnx_screenshot.png"
            cmd = f"screenshot {screenshot_path}"
            
            # 发送截图命令
            success = self.qnx_mirror.send_command(cmd, wait_time=2.0)
            if not success:
                raise Exception("截图命令执行失败")
            
            # 通过base64获取截图数据
            cat_cmd = f"cat {screenshot_path} | base64"
            base64_output, success = self.qnx_mirror.catch_message(cat_cmd, timeout=15)
            
            if not success or not base64_output:
                raise Exception("获取截图数据失败")
            
            # 清理base64数据
            base64_data = re.sub(r'[^A-Za-z0-9+/=]', '', base64_output)
            
            # 解码base64数据
            try:
                screenshot_bytes = base64.b64decode(base64_data)
            except Exception as e:
                self.logger.error(f"Base64解码失败: {e}")
                raise Exception("截图数据解码失败")
            
            # 验证图像数据
            if len(screenshot_bytes) < 100:
                raise Exception("截图数据无效或太小")
            
            # 缓存截图和计算哈希
            self.last_screenshot = screenshot_bytes
            pil_image = Image.open(io.BytesIO(screenshot_bytes))
            self.last_screenshot_hash = str(imagehash.average_hash(pil_image))

            return screenshot_bytes

        except Exception as e:
            self.logger.error(f"QNX screenshot error: {e}")
            raise e
    
    def execute_click(self, x: int, y: int) -> bool:
        """执行QNX点击命令"""
        if not self.is_connected or not self.qnx_mirror:
            raise Exception("QNX连接未建立")
        
        try:
            # QNX Screen点击命令
            cmd = f"input mouse {x} {y} click"
            
            # 发送点击命令
            success = self.qnx_mirror.send_command(cmd, wait_time=0.5)
            
            if success:
                return True
            else:
                return False

        except Exception:
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """从QNX系统下载文件"""
        if not self.is_connected or not self.qnx_mirror:
            raise Exception("QNX连接未建立")
        
        try:
            # 使用base64传输文件
            cat_cmd = f"cat {remote_path} | base64"
            base64_output, success = self.qnx_mirror.catch_message(cat_cmd, timeout=30)
            
            if not success or not base64_output:
                raise Exception("获取文件数据失败")
            
            # 清理base64数据
            base64_data = re.sub(r'[^A-Za-z0-9+/=]', '', base64_output)
            
            # 解码并保存文件
            file_bytes = base64.b64decode(base64_data)
            
            with open(local_path, 'wb') as f:
                f.write(file_bytes)

            return True

        except Exception:
            return False
    
    def get_device_info(self):
        """获取QNX设备信息"""
        if not self.is_connected or not self.qnx_mirror:
            return {}
        
        try:
            # 获取系统信息
            info_commands = {
                "hostname": "hostname",
                "version": "uname -a",
                "cpu": "uname -m",
                "memory": "free -m 2>/dev/null || echo 'Unknown'"
            }
            
            device_info = {}
            for key, cmd in info_commands.items():
                try:
                    result, success = self.qnx_mirror.catch_message(cmd, timeout=5)
                    if success and result:
                        device_info[key] = result.strip()
                    else:
                        device_info[key] = "Unknown"
                except Exception:
                    device_info[key] = "Unknown"
            
            return {
                "model": device_info.get("hostname", "QNX Device"),
                "brand": "QNX",
                "version": device_info.get("version", "Unknown"),
                "cpu": device_info.get("cpu", "Unknown"),
                "memory": device_info.get("memory", "Unknown"),
                "connection_type": "adb_telnet",
                "resolution": "Unknown"  # 需要通过截图分析获取
            }
            
        except Exception as e:
            self.logger.error(f"QNX device info error: {e}")
            return {}
    
    def get_current_app(self):
        """获取当前应用信息（QNX特定实现）"""
        if not self.is_connected or not self.qnx_mirror:
            return None
        
        try:
            # QNX获取当前应用的命令
            cmd = "ps aux 2>/dev/null | head -10 || ps | head -10"
            
            result, success = self.qnx_mirror.catch_message(cmd, timeout=5)
            
            if success and result:
                return {
                    "package": "qnx.system",
                    "activity": "screen",
                    "connection_type": "adb_telnet",
                    "processes": result.strip().split('\n')[:5]  # 前5个进程
                }
            
            return None
            
        except Exception:
            return None
    
    def execute_command(self, command: str, timeout: int = 10) -> str:
        """执行自定义QNX命令"""
        if not self.is_connected or not self.qnx_mirror:
            raise Exception("QNX连接未建立")
        
        try:
            result, success = self.qnx_mirror.catch_message(command, timeout=timeout)
            
            if success:
                return result.strip() if result else ""
            else:
                return ""

        except Exception:
            return ""
    
    def test_connection(self) -> bool:
        """测试连接是否正常"""
        if not self.is_connected or not self.qnx_mirror:
            return False
        
        try:
            # 发送简单命令测试连接
            result, success = self.qnx_mirror.catch_message("echo 'connection_test'", timeout=5)
            return success and "connection_test" in str(result)
        except Exception:
            return False

# 简单的设备管理基类
class BaseDeviceManager:
    """基础设备管理器"""
    def __init__(self, device_id):
        self.device_id = device_id
        self.device = None
        self.is_connected = False
    
    def connect(self):
        try:
            self.device = u2.connect(self.device_id)
            self.is_connected = True
        except Exception as e:
            self.is_connected = False
            raise e
    
    def disconnect(self):
        self.is_connected = False
        self.device = None
    
    def get_device_info(self):
        if not self.device:
            return {}
        try:
            info = self.device.info
            return {
                "model": info.get("model", "Unknown"),
                "brand": info.get("brand", "Unknown"), 
                "version": info.get("version", "Unknown"),
                "sdk": info.get("sdkInt", "Unknown"),
                "resolution": f"{info.get('displayWidth', 0)}x{info.get('displayHeight', 0)}"
            }
        except:
            return {}
    
    def get_current_app(self):
        if not self.device:
            return None
        try:
            return self.device.app_current()
        except:
            return None

def list_devices():
    """获取设备列表"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return []
        
        devices = []
        lines = result.stdout.strip().split('\n')[1:]  # 跳过第一行标题
        for line in lines:
            if line.strip() and '\t' in line:
                device_id = line.split('\t')[0]
                if device_id:
                    devices.append(device_id)
        return devices
    except Exception as e:
        print(f"[ERROR] 获取设备列表失败: {e}")
        return []


class DeviceManager:
    """View Scope专用设备管理器"""
    
    def __init__(self):
        self._devices: Dict[str, BaseDeviceManager] = {}
        self._device_info_cache: Dict[str, dict] = {}
        self._last_scan_time: Optional[datetime] = None
        self._scan_interval = 5.0  # 设备扫描间隔（秒）
        
    async def initialize(self):
        """初始化设备管理器"""
        await self.scan_devices()
    
    async def cleanup(self):
        """清理资源"""
        for device_id, device_manager in self._devices.items():
            try:
                device_manager.disconnect()
            except Exception:
                pass
        
        self._devices.clear()
        self._device_info_cache.clear()
    
    async def scan_devices(self) -> List[dict]:
        """扫描可用设备"""
        try:
            # 获取设备列表
            device_ids = list_devices()
            current_devices = {}
            device_list = []
            
            for device_id in device_ids:
                try:
                    # 创建或获取设备管理器
                    if device_id not in self._devices:
                        self._devices[device_id] = BaseDeviceManager(device_id)
                    
                    device_manager = self._devices[device_id]
                    current_devices[device_id] = device_manager
                    
                    # 获取设备信息
                    device_info = await self._get_device_info(device_id, device_manager)
                    device_list.append(device_info)
                    
                except Exception as e:
                    device_list.append({
                        "id": device_id,
                        "model": "Unknown",
                        "brand": "Unknown",
                        "status": "error",
                        "error": str(e)
                    })
            
            # 移除不存在的设备
            removed_devices = set(self._devices.keys()) - set(device_ids)
            for device_id in removed_devices:
                if device_id in self._devices:
                    try:
                        self._devices[device_id].disconnect()
                    except Exception:
                        pass
                    del self._devices[device_id]
                
                if device_id in self._device_info_cache:
                    del self._device_info_cache[device_id]
            
            # 更新设备列表
            self._devices = current_devices
            self._last_scan_time = datetime.now()

            return device_list

        except Exception:
            return []
    
    async def _get_device_info(self, device_id: str, device_manager: BaseDeviceManager) -> dict:
        """获取设备详细信息"""
        # 检查缓存
        if device_id in self._device_info_cache:
            cache_time = self._device_info_cache[device_id].get('_cache_time')
            if cache_time and (time.time() - cache_time) < 30:  # 30秒缓存
                return self._device_info_cache[device_id]
        
        try:
            # 尝试连接获取信息
            device_manager.connect()
            device_info = device_manager.get_device_info()
            
            # 添加额外信息
            extended_info = {
                "id": device_id,
                "model": device_info.get("model", "Unknown"),
                "brand": device_info.get("brand", "Unknown"),
                "version": device_info.get("version", "Unknown"),
                "sdk": device_info.get("sdk", "Unknown"),
                "resolution": device_info.get("resolution", "Unknown"),
                "status": "connected" if device_manager.is_connected else "disconnected",
                "connected": device_manager.is_connected,
                "_cache_time": time.time()
            }
            
            # 获取当前应用信息
            try:
                current_app = device_manager.get_current_app()
                if current_app:
                    extended_info["current_app"] = current_app
            except Exception:
                pass
            
            # 缓存信息
            self._device_info_cache[device_id] = extended_info
            return extended_info
            
        except Exception as e:
            return {
                "id": device_id,
                "model": "Unknown",
                "brand": "Unknown",
                "status": "error",
                "error": str(e),
                "connected": False,
                "_cache_time": time.time()
            }
    
    def get_all_devices(self) -> List[dict]:
        """获取所有设备（从缓存）"""
        return list(self._device_info_cache.values())
    
    def get_device(self, device_id: str) -> Optional[BaseDeviceManager]:
        """获取指定设备的管理器"""
        return self._devices.get(device_id)
    
    async def connect_device(self, device_id: str, auto_screenshot: bool = True) -> dict:
        """连接指定设备"""
        if device_id not in self._devices:
            # 重新扫描设备
            await self.scan_devices()
            
        if device_id not in self._devices:
            raise ValueError(f"设备 {device_id} 不存在")
        
        device_manager = self._devices[device_id]
        
        try:
            device_manager.connect()
            
            if device_manager.is_connected:
                # 更新缓存
                device_info = device_manager.get_device_info()
                device_info["status"] = "connected"
                device_info["connected"] = True
                device_info["_cache_time"] = time.time()
                device_info["auto_screenshot"] = auto_screenshot
                self._device_info_cache[device_id] = device_info
                
                return device_info
            else:
                raise Exception("连接失败")
                
        except Exception as e:
            raise Exception(f"连接设备失败: {str(e)}")
    
    async def disconnect_device(self, device_id: str):
        """断开指定设备"""
        if device_id in self._devices:
            try:
                self._devices[device_id].disconnect()
                
                # 更新缓存状态
                if device_id in self._device_info_cache:
                    self._device_info_cache[device_id]["status"] = "disconnected"
                    self._device_info_cache[device_id]["connected"] = False
                    
            except Exception as e:
                raise Exception(f"断开设备失败: {str(e)}")
    
    async def get_device_status(self, device_id: str) -> dict:
        """获取设备状态"""
        if device_id not in self._devices:
            raise ValueError(f"设备 {device_id} 不存在")
        
        device_manager = self._devices[device_id]
        
        return {
            "device_id": device_id,
            "connected": device_manager.is_connected,
            "status": "connected" if device_manager.is_connected else "disconnected",
            "last_check": datetime.now().isoformat()
        }
    
    def get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().isoformat()
    
    def should_refresh_devices(self) -> bool:
        """判断是否需要刷新设备列表"""
        if not self._last_scan_time:
            return True
        
        elapsed = (datetime.now() - self._last_scan_time).total_seconds()
        return elapsed > self._scan_interval
    
    async def discover_wifi_devices(self, ip_range: str, port: int = 5555) -> List[dict]:
        """扫描WiFi设备"""
        # 解析IP范围
        ip_list = self._parse_ip_range(ip_range)
        
        # 并发扫描
        discovered_devices = []
        max_workers = min(50, len(ip_list))  # 限制并发数
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交扫描任务
            future_to_ip = {
                executor.submit(self._scan_single_ip, ip, port): ip 
                for ip in ip_list
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_ip, timeout=30):
                ip = future_to_ip[future]
                try:
                    device_info = future.result()
                    if device_info:
                        discovered_devices.append(device_info)
                except Exception:
                    pass

        return discovered_devices
    
    def _parse_ip_range(self, ip_range: str) -> List[str]:
        """解析IP范围"""
        try:
            if '-' in ip_range:
                # 范围格式：192.168.1.1-192.168.1.255
                start_ip, end_ip = ip_range.split('-')
                start = ipaddress.IPv4Address(start_ip.strip())
                end = ipaddress.IPv4Address(end_ip.strip())
                
                ip_list = []
                current = start
                while current <= end:
                    ip_list.append(str(current))
                    current += 1
                    if len(ip_list) > 254:  # 安全限制
                        break
                return ip_list
            
            elif '/' in ip_range:
                # CIDR格式：192.168.1.0/24
                network = ipaddress.IPv4Network(ip_range, strict=False)
                return [str(ip) for ip in network.hosts()]
            
            else:
                # 单个IP
                return [ip_range.strip()]
                
        except Exception:
            return []
    
    def _scan_single_ip(self, ip: str, port: int, timeout: float = 2.0) -> Optional[dict]:
        """扫描单个IP地址"""
        try:
            # 1. 首先检查端口是否开放
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result != 0:
                return None
            
            # 2. 尝试通过ADB连接
            device_id = f"{ip}:{port}"
            
            # 先尝试连接ADB
            try:
                subprocess.run(
                    ['adb', 'connect', device_id], 
                    capture_output=True, 
                    timeout=timeout, 
                    check=True
                )
            except:
                pass  # 连接失败不一定意味着设备不存在
            
            # 3. 尝试获取设备信息
            try:
                device = u2.connect(device_id)
                device_info = device.info
                
                return {
                    "id": device_id,
                    "model": device_info.get("productName", "Unknown"),
                    "brand": device_info.get("brand", "Unknown"),
                    "version": device_info.get("version", "Unknown"),
                    "sdk": device_info.get("sdkInt", "Unknown"),
                    "resolution": f"{device_info.get('displayWidth', 0)}x{device_info.get('displayHeight', 0)}",
                    "status": "wifi_available",
                    "connected": False,
                    "connection_type": "wifi",
                    "ip_address": ip,
                    "_cache_time": time.time()
                }
            except:
                # 如果能连接端口但无法获取设备信息，可能是其他设备
                return {
                    "id": device_id,
                    "model": "Unknown Device",
                    "brand": "Unknown",
                    "status": "wifi_detected",
                    "connected": False,
                    "connection_type": "wifi",
                    "ip_address": ip,
                    "error": "Unable to retrieve device info",
                    "_cache_time": time.time()
                }
                
        except Exception:
            return None
    
    async def connect_wifi_device(self, ip_address: str, port: int = 5555) -> dict:
        """连接WiFi设备"""
        device_id = f"{ip_address}:{port}"

        try:
            # 1. 首先通过ADB连接
            result = subprocess.run(
                ['adb', 'connect', device_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise Exception(f"ADB连接失败: {result.stderr}")
            
            # 2. 验证连接
            time.sleep(1)  # 等待连接稳定
            
            # 3. 创建设备管理器
            if device_id not in self._devices:
                self._devices[device_id] = BaseDeviceManager(device_id)
            
            device_manager = self._devices[device_id]
            device_manager.connect()
            
            if device_manager.is_connected:
                # 获取设备信息
                device_info = device_manager.get_device_info()
                device_info.update({
                    "id": device_id,
                    "status": "connected",
                    "connected": True,
                    "connection_type": "wifi",
                    "ip_address": ip_address,
                    "_cache_time": time.time()
                })
                
                # 缓存设备信息
                self._device_info_cache[device_id] = device_info

                return device_info
            else:
                raise Exception("设备管理器连接失败")

        except Exception as e:
            raise Exception(f"连接WiFi设备失败: {str(e)}")
    
    async def disconnect_wifi_device(self, device_id: str):
        """断开WiFi设备连接"""
        try:
            # 断开设备管理器连接
            if device_id in self._devices:
                self._devices[device_id].disconnect()
                del self._devices[device_id]
            
            # 断开ADB连接
            subprocess.run(
                ['adb', 'disconnect', device_id],
                capture_output=True,
                timeout=5
            )
            
            # 更新缓存
            if device_id in self._device_info_cache:
                self._device_info_cache[device_id]["status"] = "disconnected"
                self._device_info_cache[device_id]["connected"] = False

        except Exception as e:
            raise Exception(f"断开WiFi设备失败: {str(e)}")