#!/usr/bin/env python3
"""
Go2机器狗声光控制函数库
提供LED灯光和音量控制功能
"""

import time
import sys
import os
import netifaces
import subprocess

try:
    from unitree_sdk2py.core.channel import ChannelFactoryInitialize
    from unitree_sdk2py.go2.vui.vui_client import VuiClient
    VUI_AVAILABLE = True
except ImportError:
    print("警告: 无法导入VUI模块，声光控制功能不可用")
    VUI_AVAILABLE = False


class Go2VUI:
    """Go2机器狗声光控制类"""
    
    def __init__(self, interface=None):
        """
        初始化声光控制
        
        Args:
            interface: 网络接口名称，如'enx9c4782c277cd'，None为自动检测
        """
        self.interface = interface
        self.client = None
        self.initialized = False
        
        if not VUI_AVAILABLE:
            raise ImportError("VUI模块不可用，请检查unitree_sdk2py安装")
        
        # 如果没有指定接口，自动获取
        if self.interface is None:
            self.get_interface()
    
    def get_interface(self):
        """获取当前网络接口"""
        try:
            interfaces = netifaces.interfaces()
            print(f"可用网络接口: {interfaces}")
            
            # 优先查找以太网接口 (en开头)
            for iface in interfaces:
                if iface.startswith("en"):
                    self.interface = iface
                    print(f"自动选择网络接口: {self.interface}")
                    return
            
            # 如果没有en开头的，查找其他可能的接口
            for iface in interfaces:
                if iface.startswith("eth") or iface.startswith("wlan"):
                    self.interface = iface
                    print(f"自动选择网络接口: {self.interface}")
                    return
            
            # 如果都没找到，使用第一个接口
            if interfaces:
                self.interface = interfaces[0]
                print(f"使用第一个可用接口: {self.interface}")
            else:
                print("警告: 未找到可用的网络接口")
                
        except Exception as e:
            print(f"获取网络接口失败: {e}")
    
    def check_go2_connection(self):
        """检查机器狗IP连通性"""
        try:
            # 使用ping检查机器狗IP (192.168.123.161是Go2的默认IP)
            if sys.platform.startswith('win'):
                # Windows系统
                result = subprocess.run(['ping', '-n', '1', '-w', '2000', '192.168.123.161'], 
                                      capture_output=True, text=True, timeout=5)
            else:
                # Linux/Mac系统
                result = subprocess.run(['ping', '-c', '1', '-W', '2', '192.168.123.161'], 
                                      capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("ping超时")
            return False
        except Exception as e:
            print(f"检查连接时出错: {e}")
            return False
    
    def init(self):
        """初始化VUI客户端"""
        try:
            # 检查机器狗IP连通性
            if not self.check_go2_connection():
                print("无法连接到机器狗，请检查网络连接")
                return False
            
            # 初始化DDS通道
            if self.interface:
                ChannelFactoryInitialize(0, self.interface)
            else:
                ChannelFactoryInitialize(0)
            
            # 初始化VUI客户端
            self.client = VuiClient()
            self.client.SetTimeout(3.0)
            self.client.Init()
            
            self.initialized = True
            print("VUI声光控制初始化成功")
            return True
            
        except Exception as e:
            print(f"VUI初始化失败: {e}")
            return False
    
    def set_brightness(self, level):
        """
        设置LED亮度
        
        Args:
            level (int): 亮度级别 0-10，0为关闭
            
        Returns:
            bool: 设置是否成功
        """
        if not self.initialized:
            print("VUI未初始化")
            return False
        
        try:
            if level < 0 or level > 10:
                print("亮度级别必须在0-10之间")
                return False
            
            code = self.client.SetBrightness(level)
            
            if code == 0:
                print(f"亮度设置成功: {level}")
                return True
            else:
                print(f"亮度设置失败，错误码: {code}")
                return False
                
        except Exception as e:
            print(f"设置亮度异常: {e}")
            return False
    
    def get_brightness(self):
        """
        获取当前LED亮度
        
        Returns:
            tuple: (success, level) success为bool，level为int
        """
        if not self.initialized:
            print("VUI未初始化")
            return False, 0
        
        try:
            code, level = self.client.GetBrightness()
            
            if code == 0:
                print(f"当前亮度: {level}")
                return True, level
            else:
                print(f"获取亮度失败，错误码: {code}")
                return False, 0
                
        except Exception as e:
            print(f"获取亮度异常: {e}")
            return False, 0
    
    def set_volume(self, level):
        """
        设置音量
        
        Args:
            level (int): 音量级别 0-10，0为静音
            
        Returns:
            bool: 设置是否成功
        """
        if not self.initialized:
            print("VUI未初始化")
            return False
        
        try:
            if level < 0 or level > 10:
                print("音量级别必须在0-10之间")
                return False
            
            code = self.client.SetVolume(level)
            
            if code == 0:
                print(f"音量设置成功: {level}")
                return True
            else:
                print(f"音量设置失败，错误码: {code}")
                return False
                
        except Exception as e:
            print(f"设置音量异常: {e}")
            return False
    
    def get_volume(self):
        """
        获取当前音量
        
        Returns:
            tuple: (success, level) success为bool，level为int
        """
        if not self.initialized:
            print("VUI未初始化")
            return False, 0
        
        try:
            code, level = self.client.GetVolume()
            
            if code == 0:
                print(f"当前音量: {level}")
                return True, level
            else:
                print(f"获取音量失败，错误码: {code}")
                return False, 0
                
        except Exception as e:
            print(f"获取音量异常: {e}")
            return False, 0
    
    def lights_off(self):
        """关闭LED灯光"""
        return self.set_brightness(0)
    
    def mute(self):
        """静音"""
        return self.set_volume(0)
    
    def max_brightness(self):
        """最大亮度"""
        return self.set_brightness(10)
    
    def max_volume(self):
        """最大音量"""
        return self.set_volume(10)
    
    def breathing_light(self, cycles=3, delay=0.5):
        """
        呼吸灯效果
        
        Args:
            cycles (int): 循环次数
            delay (float): 每级延迟时间(秒)
        """
        print(f"开始呼吸灯效果，循环{cycles}次")
        
        for cycle in range(cycles):
            # 渐亮
            for level in range(1, 11):
                self.set_brightness(level)
                time.sleep(delay)
            
            # 渐暗
            for level in range(9, 0, -1):
                self.set_brightness(level)
                time.sleep(delay)
        
        # 关闭灯光
        self.lights_off()
        print("呼吸灯效果结束")
    
    def volume_test(self, max_level=8):
        """
        音量测试
        
        Args:
            max_level (int): 测试最大音量级别
        """
        print(f"开始音量测试，最大级别: {max_level}")
        
        for level in range(1, max_level + 1):
            self.set_volume(level)
            time.sleep(1)
        
        # 恢复适中音量
        self.set_volume(5)
        print("音量测试结束")
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.client:
                # 关闭灯光和音量
                self.lights_off()
                self.mute()
            print("VUI资源清理完成")
        except Exception as e:
            print(f"VUI清理异常: {e}")


# 便捷函数
def create_vui(interface=None):
    """
    创建VUI实例的便捷函数
    
    Args:
        interface: 网络接口名称，如'enx9c4782c277cd'，None为自动检测
        
    Returns:
        Go2VUI: VUI实例，初始化失败返回None
    """
    vui = Go2VUI(interface)
    if vui.init():
        return vui
    else:
        return None


def auto_create_vui():
    """
    自动创建VUI实例，自动检测网络接口
    
    Returns:
        Go2VUI: VUI实例，初始化失败返回None
    """
    return create_vui(None)


if __name__ == "__main__":
    # 测试代码
    vui = Go2VUI()
    
    if vui.init():
        print("=== VUI功能测试 ===")
        
        # 测试亮度控制
        vui.set_brightness(5)
        time.sleep(1)
        vui.get_brightness()
        
        # 测试音量控制
        vui.set_volume(3)
        time.sleep(1)
        vui.get_volume()
        
        # 呼吸灯效果
        vui.breathing_light(2, 0.3)
        
        # 清理
        vui.cleanup()
    else:
        print("VUI初始化失败")