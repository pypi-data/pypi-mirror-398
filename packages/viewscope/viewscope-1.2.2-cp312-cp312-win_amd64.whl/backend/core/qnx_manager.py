import subprocess
import json
import os
import time
import re
import sys
import warnings
import wexpect
import logging

# 设置日志
logger = logging.getLogger(__name__)



class QNXMirror(object):
    """传入的登录格式：login_config = [
    {
      "step": "adb shell",
      "assertword": "#",
      "input": None  # 特殊标记，使用step作为命令但不等待assertword回显
    },
    {
      "step": "/vendor/bin/busybox telnet 192.168.8.1",
      "assertword": "login:"
    },
    # 其他步骤...
]"""

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        return instance

    def __init__(self, login_config=None, timeout=60, encoding='utf-8', log_file=None):
        self.login_config = login_config or []
        self.timeout = timeout  # 默认超时增加到60秒
        self.encoding = encoding
        self.child = None
        self.logger = logger
        self.is_connected = False
        self.prompt_pattern = None  # 存储检测到的命令提示符模式
        self._file_verification_cache = {}  # 文件验证缓存

    def con(self):
        """连接qnx保持长连接，后续可以发送命令"""
        try:
            # 执行adb root和remount
            subprocess.run(['adb', 'root'], check=False)
            subprocess.run(['adb', 'remount'], check=False)
            
            if not self.login_config:
                raise ValueError("Login configuration is missing")

            # 在连接前清理可能挂起的telnet和busybox进程
            self.logger.info("开始清理可能挂起的telnet和busybox进程...")
            try:
                subprocess.run(['adb', 'shell', 'pkill', 'telnet'], check=False, capture_output=True)
                subprocess.run(['adb', 'shell', 'pkill', 'busybox'], check=False, capture_output=True)
                self.logger.info("清理挂起进程完成")
            except:
                pass

            # 首先验证连接的有效性
            if not self._test_adb_connection():
                raise Exception("ADB连接测试失败")

            # 启动第一个命令进程
            first_step = self.login_config[0]
            self.child = wexpect.spawn(first_step["step"], timeout=self.timeout, encoding=self.encoding)
            self.logger.info(f"启动进程: {first_step['step']}")

            # 处理从第一个步骤开始的所有登录步骤
            for i, step in enumerate(self.login_config):
                step_cmd = step.get("qnx_login_token", step["step"])
                step_assert = step["assertword"]
                self.logger.info(f"处理步骤 {i}: 命令='{step_cmd}', 预期='{step_assert}'")

                # 特殊处理第一步：当"input"为None时，只等待预期输出而不发送命令
                if i == 0 and "input" in step and step["input"] is None:
                    self.logger.info(f"第一步特殊处理: 等待预期输出 '{step_assert}' 而不发送命令")
                    result = self.child.expect([step_assert, wexpect.TIMEOUT, wexpect.EOF])

                    if result == 0:  # 匹配到预期字符串
                        self.logger.info(f"成功匹配预期输出: '{step_assert}'")
                        continue
                    elif result == 1:  # 超时
                        current_output = self.child.before if hasattr(self.child, 'before') else "无输出"
                        error_msg = f"第一步超时: 等待 '{step_assert}' 超时。当前输出: {current_output}"
                        self.logger.error(error_msg)
                        raise Exception(error_msg)
                    else:  # EOF
                        error_msg = f"第一步连接意外关闭 while waiting for '{step_assert}'"
                        self.logger.error(error_msg)
                        raise Exception(error_msg)
                elif i == 0:
                    # 第一步已经通过spawn执行了，只需要等待输出
                    self.logger.info(f"第一步等待预期输出: '{step_assert}'")
                    result = self.child.expect([step_assert, wexpect.TIMEOUT, wexpect.EOF])
                    
                    if result == 0:
                        self.logger.info(f"成功匹配预期输出: '{step_assert}'")
                        continue
                    elif result == 1:
                        current_output = self.child.before if hasattr(self.child, 'before') else "无输出"
                        error_msg = f"第一步超时: 预期 '{step_assert}' 但超时。当前输出: {current_output}"
                        self.logger.error(error_msg)
                        raise Exception(error_msg)
                    else:
                        error_msg = f"第一步连接意外关闭"
                        self.logger.error(error_msg)
                        raise Exception(error_msg)
                else:
                    # 后续步骤：先发送命令，然后等待预期输出
                    self.logger.info(f"发送命令: '{step_cmd}'")
                    self.child.sendline(step_cmd)

                    self.logger.info(f"等待预期输出: '{step_assert}'")
                    result = self.child.expect([step_assert, wexpect.TIMEOUT, wexpect.EOF])

                    if result == 0:  # 匹配到预期字符串
                        self.logger.info(f"成功匹配预期输出: '{step_assert}'")
                    elif result == 1:  # 超时
                        current_output = self.child.before if hasattr(self.child, 'before') else "无输出"
                        error_msg = f"执行步骤超时: 命令 '{step_cmd}' 预期 '{step_assert}' 但超时。当前输出: {current_output}"
                        self.logger.error(error_msg)
                        raise Exception(error_msg)
                    else:  # EOF
                        error_msg = f"连接意外关闭在步骤: '{step_cmd}'"
                        self.logger.error(error_msg)
                        raise Exception(error_msg)

            # 设置连接状态为True，这样后续方法才能正常工作
            self.is_connected = True

            # 验证连接是否真的建立成功
            if not self._test_qnx_connection():
                self.is_connected = False
                raise Exception("QNX连接验证失败")

            # 检测命令提示符模式
            self._detect_prompt()

            self.logger.info("QNX连接成功建立")
            return True

        except Exception as e:
            self.logger.error(f"连接失败: {str(e)}")
            self._cleanup()
            return False

    def _test_adb_connection(self):
        """测试ADB连接是否有效"""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and 'device' in result.stdout:
                self.logger.info("ADB连接测试成功")
                return True
            else:
                self.logger.error(f"ADB连接测试失败: {result.stdout}")
                return False
        except Exception as e:
            self.logger.error(f"ADB连接测试异常: {str(e)}")
            return False

    def _test_qnx_connection(self):
        """测试QNX连接是否真的建立成功"""
        try:
            # 简单测试：检查child对象是否存在且alive
            if self.child and hasattr(self.child, 'isalive') and self.child.isalive():
                self.logger.info("QNX连接测试成功：child进程存活")
                return True
            else:
                self.logger.error("QNX连接测试失败：child进程不存在或已死亡")
                return False
                
        except Exception as e:
            self.logger.error(f"QNX连接测试异常: {str(e)}")
            return False

    def _detect_prompt(self):
        """检测并设置命令提示符模式"""
        try:
            # 简化提示符检测，避免阻塞
            self.prompt_pattern = r'(\$|#)\s*$'
            self.logger.info("使用默认命令提示符模式")
            
        except Exception as e:
            self.prompt_pattern = r'(\$|#)\s*$'
            self.logger.warning(f"提示符检测失败: {str(e)}，使用默认模式")

    def send_command(self, command, wait_time=0.5, verify_file_path=None, enable_verification=False):
        """发送命令不获取命令回复信息

        Args:
            command: 要发送的命令
            wait_time: 等待时间（秒），默认0.5秒
            verify_file_path: 如果命令涉及文件写入，提供文件路径用于验证
            enable_verification: 是否启用文件验证，默认False（性能优化）
        """
        if not self.is_connected or not self.child:
            self.logger.error("未建立连接，无法发送命令")
            return False

        try:
            # 清空缓冲区以避免旧输出干扰 - 限制次数避免无限循环
            try:
                for _ in range(3):  # 最多尝试3次
                    result = self.child.expect([r'.+', wexpect.TIMEOUT], timeout=0.1)
                    if result == 1:  # TIMEOUT表示缓冲区已清空
                        break
            except Exception:
                pass  # 忽略异常

            self.child.sendline(command)
            time.sleep(wait_time)
            
            # 尝试读取输出以验证命令执行情况
            try:
                # 设置较短超时以快速检测错误
                self.child.expect([r'.+', wexpect.TIMEOUT], timeout=1.0)
                output = self.child.before

                # 检查常见错误模式
                error_patterns = [
                    "command not found",
                    "Permission denied", 
                    "No such file or directory",
                    "cannot execute",
                    "error:",
                    "failed",
                    "bash:"
                ]

                for pattern in error_patterns:
                    if pattern in output.lower():
                        self.logger.error(f"命令执行失败 - {pattern}: {output}")
                        return False

            except wexpect.TIMEOUT:
                # 超时是正常的，说明命令可能在后台运行无输出
                self.logger.debug("命令执行超时（正常现象，命令可能在后台运行）")
            except Exception as e:
                self.logger.warning(f"读取命令输出时发生错误: {str(e)}")

            # 如果提供了文件路径且启用验证，验证文件是否成功创建/更新
            if verify_file_path and enable_verification:
                return self._verify_file_operation(verify_file_path, command)
            
            self.logger.info(f"命令发送成功: {command}")
            return True
                
        except Exception as e:
            self.logger.error(f"发送命令失败: {str(e)}")
            return False


    def catch_message(self, command, expect_pattern=None, timeout=None):
        """发送命令需要提取命令回复信息"""
        if not self.is_connected or not self.child:
            self.logger.error("未建立连接，无法发送命令")
            return None, False

        timeout = timeout or self.timeout

        try:
            # 清空缓冲区 - 限制次数避免无限循环
            try:
                for _ in range(3):  # 最多尝试3次
                    result = self.child.expect([r'.+', wexpect.TIMEOUT], timeout=0.1)
                    if result == 1:  # TIMEOUT表示缓冲区已清空
                        break
            except Exception:
                pass

            self.child.sendline(command)
            self.logger.info(f"发送命令: {command}")

            patterns = []
            if expect_pattern:
                patterns.append(expect_pattern)

            # 添加命令提示符模式
            patterns.append(self.prompt_pattern)

            # 添加超时和EOF处理
            patterns.extend([wexpect.TIMEOUT, wexpect.EOF])

            index = self.child.expect(patterns, timeout=timeout)

            if index == 0 and expect_pattern:  # 匹配到预期模式
                output = self.child.before + self.child.after
                self.logger.info(f"成功匹配预期模式，输出长度: {len(output)}")
                return output, True
            elif index in [0, 1] and not expect_pattern:  # 匹配到命令提示符
                # 提取命令输出，去除命令本身和提示符
                output = self.child.before
                # 移除命令回显
                output = output.replace(command + '\r\n', '', 1)
                # 移除提示符
                output = re.sub(self.prompt_pattern, '', output).strip()
                self.logger.info(f"获取命令输出，长度: {len(output)}")
                return output, True
            elif index == len(patterns) - 2:  # 超时
                self.logger.error(f"等待命令回复超时，预期模式: {expect_pattern or 'prompt'}")
                return self.child.before, False
            else:  # EOF
                self.logger.error("连接关闭，无法获取完整输出")
                return self.child.before, False

        except Exception as e:
            self.logger.error(f"执行命令时发生错误: {str(e)}")
            return None, False

    def stop(self, command="^C"):
        """停止当前命令，默认发送Ctrl+C"""
        if not self.is_connected or not self.child:
            self.logger.error("未建立连接，无法发送停止信号")
            return False

        try:
            if command == "^C":
                # 发送Ctrl+C中断信号
                self.child.send('\x03')
                self.logger.info("已发送Ctrl+C中断信号")
            else:
                self.child.sendline(command)

            time.sleep(0.5)  # 给系统时间处理
            self.logger.info(f"已发送停止信号: {command}")
            return True
        except Exception as e:
            self.logger.error(f"发送停止信号失败: {str(e)}")
            return False


    def Exception_step(self, error_msg, recovery_steps=None):
        """报异常的处理手段"""
        self.logger.error(f"异常处理触发: {error_msg}")

        try:
            if self.child:
                self.child.send('\x03')  # 发送 Ctrl+C (ASCII 3) 尝试中断当前操作
                time.sleep(1)

            if recovery_steps:
                self.logger.info("尝试恢复操作")
                for step in recovery_steps:
                    self.child.sendline(step)
                    time.sleep(0.5)

                # 检查是否恢复
                result = self.child.expect([self.prompt_pattern, wexpect.TIMEOUT], timeout=5)
                if result == 0:
                    self.logger.info("恢复成功")
                    return True

            self.logger.warning("恢复失败，重新连接")
            self._cleanup()
            return self.con()  # 尝试重新连接

        except Exception as e:
            self.logger.error(f"异常处理过程中发生错误: {str(e)}")
            self._cleanup()
            return False

    def _cleanup(self):
        """清理资源"""
        try:
            if self.child:
                self.child.close()
        except Exception:
            pass

        self.child = None
        self.is_connected = False
        self.logger.info("资源已清理")

    def __del__(self):
        self._cleanup()