"""
QNX连接器核心模块
基于telnet的QNX系统连接和操作封装
"""

import base64
import re
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class QNXConnector:
    """基于telnet的QNX连接器 - 第1-2轮核心实现"""
    
    def __init__(self):
        self.qnx_mirror = None
        self.is_connected = False
        self.logger = logger
        
    def telnet_connect(self, login_config: List[Dict] = None) -> bool:
        """
        建立telnet连接
        
        Args:
            login_config: 登录配置列表，格式如：
                [
                    {"step": "adb shell", "assertword": "#", "input": None},
                    {"step": "/vendor/bin/busybox telnet 192.168.8.1", "assertword": "login:"},
                    {"step": "root", "assertword": "Password:"},
                    {"step": "", "assertword": "#"}
                ]
        
        Returns:
            bool: 连接是否成功
        """
        try:
            from core.qnx_manager import QNXMirror
            
            # 默认登录配置
            if login_config is None:
                login_config = [
                    {
                        "step": "adb shell",
                        "assertword": "#",
                        "input": None
                    },
                    {
                        "step": "/vendor/bin/busybox telnet 192.168.8.1",
                        "assertword": "login:"
                    },
                    {
                        "step": "root",
                        "assertword": "Password:"
                    },
                    {
                        "step": "",
                        "assertword": "#"
                    }
                ]
            
            self.qnx_mirror = QNXMirror(
                login_config=login_config,
                timeout=60,
                encoding='utf-8'
            )
            
            success = self.qnx_mirror.con()
            
            if success:
                self.is_connected = True
                self.logger.info("QNX telnet连接成功")
            else:
                self.is_connected = False
                self.logger.error("QNX telnet连接失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            self.is_connected = False
            return False
    
    def execute_screenshot(self) -> bytes:
        """
        执行截图并返回图像数据
        
        Returns:
            bytes: 截图的二进制数据
        
        Raises:
            Exception: 如果未连接或截图失败
        """
        if not self.qnx_mirror or not self.qnx_mirror.is_connected:
            raise Exception("未连接到QNX系统")
        
        try:
            # 执行QNX截图命令
            screenshot_path = "/tmp/qnx_screenshot.png"
            cmd = f"screenshot {screenshot_path}"
            
            # 发送截图命令，增加等待时间
            success = self.qnx_mirror.send_command(cmd, wait_time=3.0)
            if not success:
                # 尝试其他截图命令格式
                self.logger.warning("标准screenshot命令失败，尝试其他格式")
                cmd = f"screencapture -f {screenshot_path}"
                success = self.qnx_mirror.send_command(cmd, wait_time=3.0)
                if not success:
                    raise Exception("截图命令执行失败")
            
            # 先检查文件是否存在
            check_cmd = f"ls -la {screenshot_path}"
            output, success = self.qnx_mirror.catch_message(check_cmd, timeout=5)
            if not success or "No such file" in output:
                self.logger.error(f"截图文件不存在: {output}")
                raise Exception("截图文件创建失败")
            
            # 使用base64获取截图数据，分块处理避免数据丢失
            # 先获取文件大小
            size_cmd = f"wc -c {screenshot_path} | awk '{{print $1}}'"
            size_output, success = self.qnx_mirror.catch_message(size_cmd, timeout=5)
            if success and size_output:
                file_size = int(size_output.strip())
                self.logger.info(f"截图文件大小: {file_size} 字节")
            
            # 使用base64获取截图数据
            cat_cmd = f"base64 {screenshot_path}"  # 直接使用base64命令，避免管道问题
            output, success = self.qnx_mirror.catch_message(cat_cmd, timeout=30)
            
            if not success or not output:
                # 如果base64命令失败，尝试使用cat和base64组合
                self.logger.warning("直接base64命令失败，尝试cat管道方式")
                cat_cmd = f"cat {screenshot_path} | base64 -w 0"  # -w 0避免换行
                output, success = self.qnx_mirror.catch_message(cat_cmd, timeout=30)
                
                if not success or not output:
                    raise Exception("获取截图数据失败")
            
            # 清理base64数据（去除非base64字符，但保留=填充字符）
            # 先去除可能的命令回显
            if "base64" in output[:100]:
                # 找到第一个换行后的内容
                lines = output.split('\n')
                if len(lines) > 1:
                    output = '\n'.join(lines[1:])
            
            # 清理空白字符和非base64字符
            base64_data = re.sub(r'[\s\r\n]', '', output)  # 先去除所有空白字符
            base64_data = re.sub(r'[^A-Za-z0-9+/=]', '', base64_data)  # 再去除非base64字符
            
            # 验证base64数据长度
            if len(base64_data) < 100:
                self.logger.error(f"Base64数据太短: {len(base64_data)} 字符")
                self.logger.debug(f"原始输出前100字符: {output[:100]}")
                raise Exception(f"Base64数据无效，长度: {len(base64_data)}")
            
            # 解码base64数据
            try:
                # 确保base64字符串长度是4的倍数
                padding = len(base64_data) % 4
                if padding:
                    base64_data += '=' * (4 - padding)
                
                screenshot_bytes = base64.b64decode(base64_data)
            except Exception as e:
                self.logger.error(f"Base64解码失败: {e}")
                self.logger.debug(f"Base64数据前100字符: {base64_data[:100]}")
                raise Exception(f"截图数据解码失败: {e}")
            
            # 验证图像数据
            if len(screenshot_bytes) < 1000:  # PNG文件至少应该有1KB
                self.logger.error(f"解码后数据太小: {len(screenshot_bytes)} 字节")
                raise Exception(f"截图数据无效或太小: {len(screenshot_bytes)} 字节")
            
            # 验证PNG文件头
            if len(screenshot_bytes) >= 8:
                png_header = screenshot_bytes[:8]
                expected_header = b'\x89PNG\r\n\x1a\n'
                if png_header != expected_header:
                    self.logger.warning("警告: 文件可能不是有效的PNG格式")
            
            self.logger.info(f"截图成功，大小: {len(screenshot_bytes)} 字节")
            return screenshot_bytes
            
        except Exception as e:
            self.logger.error(f"执行截图失败: {e}")
            raise e
    
    def execute_click(self, x: int, y: int) -> bool:
        """
        执行点击操作
        
        Args:
            x: X坐标
            y: Y坐标
        
        Returns:
            bool: 点击是否成功
        """
        if not self.qnx_mirror or not self.qnx_mirror.is_connected:
            self.logger.error("未连接到QNX系统")
            return False
        
        try:
            # QNX点击命令
            cmd = f"input mouse {x} {y} click"
            
            # 发送点击命令
            success = self.qnx_mirror.send_command(cmd, wait_time=0.5)
            
            if success:
                self.logger.info(f"点击执行成功: ({x}, {y})")
            else:
                self.logger.warning(f"点击命令可能失败: ({x}, {y})")
            
            return success
            
        except Exception as e:
            self.logger.error(f"执行点击失败: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        下载文件（使用base64传输）
        
        Args:
            remote_path: 远程文件路径
            local_path: 本地保存路径
        
        Returns:
            bool: 下载是否成功
        """
        if not self.qnx_mirror or not self.qnx_mirror.is_connected:
            self.logger.error("未连接到QNX系统")
            return False
        
        try:
            # 使用base64传输文件
            cat_cmd = f"cat {remote_path} | base64"
            output, success = self.qnx_mirror.catch_message(cat_cmd, timeout=30)
            
            if not success or not output:
                raise Exception("获取文件数据失败")
            
            # 清理base64数据
            base64_data = re.sub(r'[^A-Za-z0-9+/=]', '', output)
            
            # 解码并保存文件
            file_bytes = base64.b64decode(base64_data)
            
            with open(local_path, 'wb') as f:
                f.write(file_bytes)
            
            self.logger.info(f"文件下载成功: {remote_path} -> {local_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"文件下载失败: {e}")
            return False
    
    def execute_command(self, command: str, timeout: int = 10) -> str:
        """
        执行自定义命令并获取输出
        
        Args:
            command: 要执行的命令
            timeout: 超时时间（秒）
        
        Returns:
            str: 命令输出
        """
        if not self.qnx_mirror or not self.qnx_mirror.is_connected:
            self.logger.error("未连接到QNX系统")
            return ""
        
        try:
            output, success = self.qnx_mirror.catch_message(command, timeout=timeout)
            
            if success:
                self.logger.info(f"命令执行成功: {command}")
                return output.strip() if output else ""
            else:
                self.logger.warning(f"命令执行可能失败: {command}")
                return ""
                
        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            return ""
    
    def disconnect(self):
        """断开连接"""
        try:
            if self.qnx_mirror:
                self.qnx_mirror._cleanup()
                self.qnx_mirror = None
            
            self.is_connected = False
            self.logger.info("QNX连接已断开")
            
        except Exception as e:
            self.logger.warning(f"断开连接时出错: {e}")
    
    def __del__(self):
        """析构函数，确保资源清理"""
        self.disconnect()