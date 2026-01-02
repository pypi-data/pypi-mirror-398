"""
QNX设备管理器 - ADB + busybox telnet版本
通过ADB shell执行busybox telnet连接QNX系统
"""

import wexpect
import subprocess
import cv2
import numpy as np
import imagehash
from PIL import Image
import io
import base64
import tempfile
import os
import re
from typing import Dict, List, Optional


class QNXADBTelnetManager:
    """QNX系统设备管理器 - 通过ADB shell + busybox telnet连接"""
    
    def __init__(self, adb_device_id: str = None, qnx_host: str = "192.168.8.1", 
                 busybox_path: str = "/vendor/bin/busybox",
                 username: str = None, password: str = None):
        """
        初始化QNX ADB+Telnet管理器
        
        Args:
            adb_device_id: ADB设备ID（如果有多个设备连接）
            qnx_host: QNX系统的IP地址（默认192.168.8.1）
            busybox_path: busybox的路径（默认/vendor/bin/busybox）
            username: QNX登录用户名
            password: QNX登录密码
        """
        self.adb_device_id = adb_device_id
        self.qnx_host = qnx_host
        self.busybox_path = busybox_path
        self.username = username
        self.password = password
        self.child_process = None
        self.is_connected = False
        self.device_id = f"qnx_adb_{qnx_host}"
        self.last_screenshot = None
        self.last_screenshot_hash = None
        # QNX shell提示符模式 - 考虑ADB shell和QNX shell的不同提示符
        self.qnx_prompt_pattern = r'[#$>]\s*$'
        self.adb_prompt_pattern = r'[$#]\s*$'
    
    def _check_adb_connection(self) -> bool:
        """检查ADB连接状态"""
        try:
            # 构建adb命令
            adb_cmd = ['adb']
            if self.adb_device_id:
                adb_cmd.extend(['-s', self.adb_device_id])
            adb_cmd.append('devices')
            
            result = subprocess.run(adb_cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # 检查设备是否在列表中
                if self.adb_device_id:
                    return self.adb_device_id in result.stdout
                else:
                    # 检查是否有任何设备连接
                    lines = result.stdout.strip().split('\n')
                    return len(lines) > 1 and 'device' in result.stdout
            return False
            
        except Exception as e:
            print(f"[ERROR] 检查ADB连接失败: {e}")
            return False
    
    def connect(self):
        """建立ADB shell + busybox telnet连接"""
        try:
            # 1. 首先检查ADB连接
            if not self._check_adb_connection():
                raise Exception("ADB设备未连接或未找到")
            
            # 2. 构建adb shell命令
            adb_cmd = "adb"
            if self.adb_device_id:
                adb_cmd = f"adb -s {self.adb_device_id}"
            
            # 3. 启动adb shell进程
            shell_cmd = f"{adb_cmd} shell"
            print(f"[ADB] 启动ADB shell: {shell_cmd}")
            self.child_process = wexpect.spawn(shell_cmd)
            
            # 4. 等待ADB shell提示符
            try:
                self.child_process.expect(self.adb_prompt_pattern, timeout=5)
                print("[ADB] ADB shell连接成功")
            except wexpect.TIMEOUT:
                # 尝试发送回车获取提示符
                self.child_process.sendline("")
                self.child_process.expect(self.adb_prompt_pattern, timeout=3)
                print("[ADB] ADB shell连接成功（二次尝试）")
            
            # 5. 在ADB shell中执行busybox telnet命令（不指定端口，使用默认端口）
            telnet_cmd = f"{self.busybox_path} telnet {self.qnx_host}"
            print(f"[QNX] 执行telnet连接: {telnet_cmd}")
            self.child_process.sendline(telnet_cmd)
            
            # 6. 等待telnet连接建立
            # 可能会看到连接消息如 "Connected to" 或 "Entering character mode"
            try:
                index = self.child_process.expect([r'Connected to', r'Entering character mode', r'login:'], timeout=10)
                if index == 0:
                    print(f"[QNX] Telnet连接到 {self.qnx_host} 成功")
                elif index == 1:
                    print("[QNX] 进入字符模式")
                elif index == 2:
                    print("[QNX] 检测到登录提示")
            except wexpect.TIMEOUT:
                print("[QNX] 未检测到连接确认，继续尝试...")
            
            # 7. 处理QNX登录
            if self.username:
                try:
                    # 等待login提示
                    self.child_process.expect(r'login:', timeout=10)
                    print(f"[QNX] 发送用户名: {self.username}")
                    self.child_process.sendline(self.username)
                    
                    # 等待密码提示
                    if self.password:
                        self.child_process.expect(r'[Pp]assword:', timeout=10)
                        print("[QNX] 发送密码")
                        self.child_process.sendline(self.password)
                    
                    # 等待登录后的提示符
                    self.child_process.expect(self.qnx_prompt_pattern, timeout=10)
                    self.is_connected = True
                    print(f"[QNX] 登录成功: {self.device_id}")
                    
                except wexpect.TIMEOUT as e:
                    print("[ERROR] 登录超时")
                    if self.child_process and hasattr(self.child_process, 'before'):
                        print(f"[DEBUG] 最后输出: {self.child_process.before}")
                    raise Exception(f"QNX登录失败: {e}")
            else:
                # 无需登录，尝试直接获取提示符
                try:
                    self.child_process.expect(self.qnx_prompt_pattern, timeout=10)
                    self.is_connected = True
                    print(f"[QNX] 连接成功（无需登录）: {self.device_id}")
                except wexpect.TIMEOUT:
                    # 尝试发送回车获取提示符
                    self.child_process.sendline("")
                    self.child_process.expect(self.qnx_prompt_pattern, timeout=5)
                    self.is_connected = True
                    print(f"[QNX] 连接成功（二次尝试）: {self.device_id}")
            
        except Exception as e:
            self.is_connected = False
            print(f"[ERROR] QNX ADB+Telnet连接失败: {e}")
            if self.child_process and hasattr(self.child_process, 'before'):
                print(f"[DEBUG] 输出: {self.child_process.before}")
            raise e
    
    def disconnect(self):
        """断开连接"""
        try:
            if self.child_process:
                # 尝试优雅退出telnet
                try:
                    self.child_process.sendline("exit")
                    self.child_process.expect(self.adb_prompt_pattern, timeout=2)
                    print("[QNX] Telnet连接已退出")
                except:
                    pass
                
                # 退出ADB shell
                try:
                    self.child_process.sendline("exit")
                except:
                    pass
                
                # 关闭进程
                self.child_process.close()
                self.child_process = None
            
            self.is_connected = False
            print(f"[QNX] ADB+Telnet连接已断开: {self.device_id}")
            
        except Exception as e:
            print(f"[WARN] 断开连接时出错: {e}")
    
    def execute_screenshot(self) -> bytes:
        """执行QNX截图命令"""
        if not self.is_connected:
            raise Exception("ADB+Telnet连接未建立")
        
        try:
            # 执行QNX Screen截图命令
            screenshot_path = "/tmp/qnx_screenshot.png"
            cmd = f"screenshot {screenshot_path}"
            
            print(f"[QNX] 执行截图命令: {cmd}")
            
            # 发送截图命令
            self.child_process.sendline(cmd)
            self.child_process.expect(self.qnx_prompt_pattern, timeout=10)
            
            # 使用base64传输文件
            transfer_cmd = f"cat {screenshot_path} | base64"
            
            print(f"[QNX] 传输截图文件: {transfer_cmd}")
            
            self.child_process.sendline(transfer_cmd)
            self.child_process.expect(self.qnx_prompt_pattern, timeout=15)
            
            # 获取base64编码的图像数据
            base64_output = self.child_process.before
            if isinstance(base64_output, bytes):
                base64_output = base64_output.decode('utf-8')
            
            # 清理输出 - 移除命令回显和提示符
            lines = base64_output.split('\n')
            # 跳过第一行（命令回显）和最后的空行
            base64_lines = [line for line in lines[1:] if line.strip() and not line.startswith('cat')]
            base64_data = ''.join(base64_lines)
            
            # 进一步清理非base64字符
            base64_data = re.sub(r'[^A-Za-z0-9+/=]', '', base64_data)
            
            try:
                screenshot_bytes = base64.b64decode(base64_data)
            except Exception as decode_error:
                print(f"[WARN] Base64解码失败: {decode_error}")
                print(f"[DEBUG] Base64数据前100字符: {base64_data[:100]}")
                raise Exception("截图文件传输失败")
            
            # 验证图像数据有效性
            if len(screenshot_bytes) > 100:  # 基本大小检查
                # 缓存截图和计算哈希
                self.last_screenshot = screenshot_bytes
                pil_image = Image.open(io.BytesIO(screenshot_bytes))
                self.last_screenshot_hash = str(imagehash.average_hash(pil_image))
                
                print(f"[QNX] 截图成功，大小: {len(screenshot_bytes)} 字节")
                return screenshot_bytes
            else:
                raise Exception("截图数据无效或太小")
            
        except Exception as e:
            print(f"[ERROR] QNX截图失败: {e}")
            raise e
    
    def execute_click(self, x: int, y: int) -> bool:
        """执行QNX点击命令"""
        if not self.is_connected:
            raise Exception("ADB+Telnet连接未建立")
        
        try:
            # QNX Screen点击命令
            cmd = f"input mouse {x} {y} click"
            
            print(f"[QNX] 执行点击命令: {cmd}")
            
            self.child_process.sendline(cmd)
            self.child_process.expect(self.qnx_prompt_pattern, timeout=5)
            
            # 检查命令执行结果
            output = self.child_process.before
            if isinstance(output, bytes):
                output = output.decode('utf-8')
            
            # 简单的错误检查
            if "error" in output.lower() or "failed" in output.lower():
                print(f"[WARN] 点击命令可能失败: {output}")
                return False
            
            print(f"[QNX] 点击执行成功: ({x}, {y})")
            return True
            
        except Exception as e:
            print(f"[ERROR] QNX点击失败: {e}")
            return False
    
    def execute_command(self, command: str, timeout: int = 10) -> str:
        """执行自定义QNX命令"""
        if not self.is_connected:
            raise Exception("ADB+Telnet连接未建立")
        
        try:
            self.child_process.sendline(command)
            self.child_process.expect(self.qnx_prompt_pattern, timeout=timeout)
            
            output = self.child_process.before
            if isinstance(output, bytes):
                output = output.decode('utf-8')
            
            # 清理输出 - 移除命令回显
            lines = output.split('\n')
            if lines and lines[0].strip() == command:
                lines = lines[1:]
            
            return '\n'.join(lines).strip()
            
        except Exception as e:
            print(f"[ERROR] 执行QNX命令失败: {e}")
            return ""
    
    def get_device_info(self):
        """获取QNX设备信息"""
        if not self.is_connected:
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
                    result = self.execute_command(cmd, timeout=5)
                    device_info[key] = result if result else "Unknown"
                except Exception:
                    device_info[key] = "Unknown"
            
            return {
                "model": device_info.get("hostname", "QNX Device"),
                "brand": "QNX",
                "version": device_info.get("version", "Unknown"),
                "cpu": device_info.get("cpu", "Unknown"),
                "memory": device_info.get("memory", "Unknown"),
                "connection_type": "adb_telnet",
                "adb_device": self.adb_device_id or "default",
                "qnx_host": self.qnx_host,
                "resolution": "Unknown"  # 需要通过截图分析获取
            }
            
        except Exception as e:
            print(f"[ERROR] 获取QNX设备信息失败: {e}")
            return {}
    
    def get_current_app(self):
        """获取当前应用信息（QNX特定实现）"""
        if not self.is_connected:
            return None
        
        try:
            # QNX获取当前应用的命令
            result = self.execute_command("ps aux 2>/dev/null | head -10 || ps | head -10", timeout=5)
            
            if result:
                return {
                    "package": "qnx.system",
                    "activity": "screen",
                    "connection_type": "adb_telnet",
                    "processes": result.split('\n')[:5]  # 前5个进程
                }
            
            return None
            
        except Exception:
            return None
    
    def test_connection(self) -> bool:
        """测试连接是否正常"""
        if not self.is_connected:
            return False
        
        try:
            # 发送简单命令测试连接
            result = self.execute_command("echo 'connection_test'", timeout=5)
            return "connection_test" in result
        except Exception:
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """从QNX系统下载文件"""
        if not self.is_connected:
            raise Exception("ADB+Telnet连接未建立")
        
        try:
            # 使用cat + base64的方式传输文件
            cmd = f"cat {remote_path} | base64"
            
            print(f"[QNX] 下载文件: {cmd}")
            
            self.child_process.sendline(cmd)
            self.child_process.expect(self.qnx_prompt_pattern, timeout=30)
            
            # 获取base64输出
            base64_output = self.child_process.before
            if isinstance(base64_output, bytes):
                base64_output = base64_output.decode('utf-8')
            
            # 清理输出
            lines = base64_output.split('\n')
            base64_lines = [line for line in lines[1:] if line.strip() and not line.startswith('cat')]
            base64_data = ''.join(base64_lines)
            base64_data = re.sub(r'[^A-Za-z0-9+/=]', '', base64_data)
            
            file_bytes = base64.b64decode(base64_data)
            
            # 写入本地文件
            with open(local_path, 'wb') as f:
                f.write(file_bytes)
            
            print(f"[QNX] 文件下载成功: {remote_path} -> {local_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] QNX文件下载失败: {e}")
            return False
    
    @staticmethod
    def list_adb_devices() -> List[str]:
        """列出所有ADB设备"""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                devices = []
                lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                for line in lines:
                    if '\t' in line and 'device' in line:
                        device_id = line.split('\t')[0]
                        devices.append(device_id)
                return devices
            return []
        except Exception as e:
            print(f"[ERROR] 获取ADB设备列表失败: {e}")
            return []