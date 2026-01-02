"""
QNX设备管理器 - wexpect版本
基于wexpect的QNX系统连接和控制
"""

import wexpect
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


class QNXWexpectManager:
    """QNX系统设备管理器 - 通过wexpect/telnet连接"""
    
    def __init__(self, host: str, username: str = None, password: str = None, 
                 port: int = 23, connection_type: str = "telnet"):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.connection_type = connection_type  # "telnet" or "serial"
        self.child_process = None
        self.is_connected = False
        self.device_id = f"qnx_{host}:{port}_{connection_type}"
        self.last_screenshot = None
        self.last_screenshot_hash = None
        self.prompt_pattern = r'[#$>]\s*$'  # QNX shell prompt pattern
    
    def connect(self):
        """建立wexpect连接"""
        try:
            if self.connection_type == "telnet":
                # 使用telnet连接
                cmd = f"telnet {self.host} {self.port}"
                print(f"[QNX] 执行连接命令: {cmd}")
                self.child_process = wexpect.spawn(cmd)
                
                # 等待登录提示并进行认证
                if self.username:
                    try:
                        self.child_process.expect(r'login:', timeout=10)
                        self.child_process.sendline(self.username)
                        print(f"[QNX] 发送用户名: {self.username}")
                        
                        if self.password:
                            self.child_process.expect(r'Password:', timeout=5)
                            self.child_process.sendline(self.password)
                            print(f"[QNX] 发送密码")
                    except wexpect.TIMEOUT:
                        print("[QNX] 可能无需认证或认证超时，尝试直接连接")
                
                # 等待shell提示符
                try:
                    self.child_process.expect(self.prompt_pattern, timeout=10)
                    self.is_connected = True
                    print(f"[QNX] Telnet连接成功: {self.device_id}")
                except wexpect.TIMEOUT:
                    # 尝试发送回车获取提示符
                    self.child_process.sendline("")
                    self.child_process.expect(self.prompt_pattern, timeout=5)
                    self.is_connected = True
                    print(f"[QNX] Telnet连接成功(二次尝试): {self.device_id}")
                
            elif self.connection_type == "serial":
                # 串口连接 (假设通过串口工具)
                cmd = f"putty -serial {self.host} -sercfg {self.port},8,n,1,N"
                print(f"[QNX] 执行串口连接: {cmd}")
                self.child_process = wexpect.spawn(cmd)
                self.child_process.expect(self.prompt_pattern, timeout=15)
                self.is_connected = True
                print(f"[QNX] 串口连接成功: {self.device_id}")
            
        except Exception as e:
            self.is_connected = False
            print(f"[ERROR] QNX wexpect连接失败: {e}")
            if hasattr(e, 'before'):
                print(f"[DEBUG] 连接前输出: {e.before}")
            if hasattr(e, 'after'):
                print(f"[DEBUG] 连接后输出: {e.after}")
            raise e
    
    def disconnect(self):
        """断开wexpect连接"""
        try:
            if self.child_process:
                self.child_process.close()
                self.child_process = None
            
            self.is_connected = False
            print(f"[QNX] Wexpect连接已断开: {self.device_id}")
            
        except Exception as e:
            print(f"[WARN] 断开QNX连接时出错: {e}")
    
    def execute_screenshot(self) -> bytes:
        """执行QNX截图命令"""
        if not self.is_connected:
            raise Exception("wexpect连接未建立")
        
        try:
            # 执行QNX Screen截图命令
            screenshot_path = "/tmp/qnx_screenshot.png"
            cmd = f"screenshot {screenshot_path}"
            
            print(f"[QNX] 执行截图命令: {cmd}")
            
            # 发送截图命令
            self.child_process.sendline(cmd)
            self.child_process.expect(self.prompt_pattern, timeout=10)
            
            # 传输文件到本地临时目录
            local_temp_file = tempfile.mktemp(suffix='.png')
            transfer_cmd = f"cat {screenshot_path} | base64"
            
            print(f"[QNX] 传输截图文件: {transfer_cmd}")
            
            self.child_process.sendline(transfer_cmd)
            self.child_process.expect(self.prompt_pattern, timeout=15)
            
            # 获取base64编码的图像数据
            base64_output = self.child_process.before
            if isinstance(base64_output, bytes):\n                base64_output = base64_output.decode('utf-8')
            
            # 清理输出并解码
            base64_data = re.sub(r'[^A-Za-z0-9+/=]', '', base64_output)
            
            try:
                screenshot_bytes = base64.b64decode(base64_data)
            except Exception as decode_error:
                # 备用方案：使用scp或其他文件传输方法
                print(f"[WARN] Base64解码失败，尝试备用方案: {decode_error}")
                # 这里可以添加其他文件传输逻辑
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
            raise Exception("wexpect连接未建立")
        
        try:
            # QNX Screen点击命令
            cmd = f"input mouse {x} {y} click"
            
            print(f"[QNX] 执行点击命令: {cmd}")
            
            self.child_process.sendline(cmd)
            self.child_process.expect(self.prompt_pattern, timeout=5)
            
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
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """从QNX系统下载文件"""
        if not self.is_connected:
            raise Exception("wexpect连接未建立")
        
        try:
            # 使用cat + base64的方式传输文件
            cmd = f"cat {remote_path} | base64"
            
            print(f"[QNX] 下载文件: {cmd}")
            
            self.child_process.sendline(cmd)
            self.child_process.expect(self.prompt_pattern, timeout=30)
            
            # 获取base64输出
            base64_output = self.child_process.before
            if isinstance(base64_output, bytes):
                base64_output = base64_output.decode('utf-8')
            
            # 清理和解码
            base64_data = re.sub(r'[^A-Za-z0-9+/=]', '', base64_output)
            file_bytes = base64.b64decode(base64_data)
            
            # 写入本地文件
            with open(local_path, 'wb') as f:
                f.write(file_bytes)
            
            print(f"[QNX] 文件下载成功: {remote_path} -> {local_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] QNX文件下载失败: {e}")
            return False
    
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
                "memory": "free -m | head -2"
            }
            
            device_info = {}
            for key, cmd in info_commands.items():
                try:
                    self.child_process.sendline(cmd)
                    self.child_process.expect(self.prompt_pattern, timeout=5)
                    
                    output = self.child_process.before
                    if isinstance(output, bytes):
                        output = output.decode('utf-8')
                    
                    # 清理输出
                    result = output.strip()
                    device_info[key] = result if result else "Unknown"
                except Exception:
                    device_info[key] = "Unknown"
            
            return {
                "model": device_info.get("hostname", "QNX Device"),
                "brand": "QNX",
                "version": device_info.get("version", "Unknown"),
                "cpu": device_info.get("cpu", "Unknown"),
                "memory": device_info.get("memory", "Unknown"),
                "connection_type": self.connection_type,
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
            # QNX获取当前应用的命令（根据实际QNX系统调整）
            cmd = "ps aux | head -10"  # 简单的进程列表
            
            self.child_process.sendline(cmd)
            self.child_process.expect(self.prompt_pattern, timeout=5)
            
            output = self.child_process.before
            if isinstance(output, bytes):
                output = output.decode('utf-8')
            
            result = output.strip()
            
            return {
                "package": "qnx.system",
                "activity": "screen",
                "connection_type": self.connection_type,
                "processes": result.split('\n')[:5]  # 前5个进程
            }
            
        except Exception:
            return None
    
    def execute_command(self, command: str, timeout: int = 10) -> str:
        """执行自定义QNX命令"""
        if not self.is_connected:
            raise Exception("wexpect连接未建立")
        
        try:
            self.child_process.sendline(command)
            self.child_process.expect(self.prompt_pattern, timeout=timeout)
            
            output = self.child_process.before
            if isinstance(output, bytes):
                output = output.decode('utf-8')
            
            return output.strip()
            
        except Exception as e:
            print(f"[ERROR] 执行QNX命令失败: {e}")
            return ""
    
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