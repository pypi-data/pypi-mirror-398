"""
Go2机器狗摄像头控制类
提供图片获取和视频流功能
"""

import cv2
import numpy as np
import threading
import time
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.video.video_client import VideoClient


class Go2Camera:
    """
    Go2机器狗摄像头控制类
    支持单张图片获取和视频流获取
    """
    
    def __init__(self, interface=None, timeout=3.0):
        """
        初始化摄像头控制器
        
        Args:
            interface (str): 网卡接口名称
            timeout (float): 超时时间（秒）
        """
        self.interface = interface
        self.timeout = timeout
        self.video_client = None
        self.cap = None
        self._streaming = False
        self._stream_thread = None
        self._latest_frame = None
        self._frame_lock = threading.Lock()
        
    def init(self, interface=None):
        """
        初始化摄像头连接
        
        Args:
            interface (str): 网卡接口名称，如果为None则使用初始化时的接口
            
        Returns:
            bool: 是否初始化成功
        """
        if interface:
            self.interface = interface
            
        if not self.interface:
            print("错误：未指定网络接口")
            return False
            
        try:
            # 初始化DDS通道（与go2.py保持一致）
            ChannelFactoryInitialize(0, self.interface)
            
            # 初始化视频客户端
            self.video_client = VideoClient()
            self.video_client.SetTimeout(self.timeout)
            self.video_client.Init()
            
            print(f"摄像头初始化成功，使用接口: {self.interface}")
            return True
            
        except Exception as e:
            print(f"摄像头初始化失败: {e}")
            return False
    
    def capture_image(self, save_path=None):
        """
        获取一张图片
        
        Args:
            save_path (str): 保存路径，如果为None则不保存
            
        Returns:
            numpy.ndarray: 图像数据，失败时返回None
        """
        if not self.video_client:
            print("错误：摄像头未初始化，请先调用 init()")
            return None
            
        try:
            # 获取图像样本
            code, data = self.video_client.GetImageSample()
            
            if code != 0 or data is None:
                print(f"获取图像失败，错误码: {code}")
                return None
                
            # 转换图像数据
            image_data = np.frombuffer(bytes(data), dtype=np.uint8)
            image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
            
            if image is None:
                print("图像解码失败")
                return None
                
            print(f"成功获取图像，尺寸: {image.shape}")
            
            # 保存图像
            if save_path:
                cv2.imwrite(save_path, image)
                print(f"图像已保存到: {save_path}")
                
            return image
            
        except Exception as e:
            print(f"获取图像时出错: {e}")
            return None
    
    def open_video_stream(self, width=480, height=320):
        """
        打开视频流
        
        Args:
            width (int): 视频宽度
            height (int): 视频高度
            
        Returns:
            bool: 是否成功打开视频流
        """
        if not self.interface:
            print("错误：未指定网络接口")
            return False
            
        # 构建GStreamer字符串
        gstreamer_str = (
            f"udpsrc address=230.1.1.1 port=1720 multicast-iface={self.interface} "
            "! application/x-rtp, media=video, encoding-name=H264 "
            "! rtph264depay ! h264parse "
            "! avdec_h264 "  # 解码H.264
            "! videoscale "  # 添加缩放元素，用于调整分辨率
            f"! video/x-raw,width={width},height={height} "  # 目标分辨率
            "! videoconvert ! video/x-raw, format=BGR "  # 转换为OpenCV支持的BGR格式
            "! appsink drop=1"
        )
        
        try:
            self.cap = cv2.VideoCapture(gstreamer_str, cv2.CAP_GSTREAMER)
            
            if not self.cap.isOpened():
                print("视频流打开失败")
                print(f"使用的网络接口: {self.interface}")
                print("GStreamer字符串:", gstreamer_str)
                return False
                
            print("视频流打开成功")
            return True
            
        except Exception as e:
            print(f"打开视频流时出错: {e}")
            return False
    
    def read_frame(self):
        """
        从视频流读取一帧
        
        Returns:
            numpy.ndarray: 图像数据，失败时返回None
        """
        if self.cap is None or not self.cap.isOpened():
            print("错误：视频流未打开")
            return None
            
        try:
            ret, frame = self.cap.read()
            if not ret:
                print("读取视频帧失败")
                return None
                
            return frame
            
        except Exception as e:
            print(f"读取视频帧时出错: {e}")
            return None
    
    def start_stream(self, width=480, height=320):
        """
        开始后台视频流（持续获取最新帧）
        
        Args:
            width (int): 视频宽度
            height (int): 视频高度
            
        Returns:
            bool: 是否成功开始流
        """
        if self._streaming:
            print("视频流已在运行中")
            return True
            
        if not self.open_video_stream(width, height):
            return False
            
        self._streaming = True
        
        def stream_loop():
            while self._streaming:
                frame = self.read_frame()
                if frame is not None:
                    with self._frame_lock:
                        self._latest_frame = frame.copy()
                time.sleep(0.01)  # 避免过度占用CPU
                
        self._stream_thread = threading.Thread(target=stream_loop)
        self._stream_thread.daemon = True
        self._stream_thread.start()
        
        print("后台视频流已启动")
        return True
    
    def get_latest_frame(self):
        """
        获取最新的视频帧（非阻塞）
        
        Returns:
            numpy.ndarray: 最新图像数据，无数据时返回None
        """
        with self._frame_lock:
            if self._latest_frame is not None:
                return self._latest_frame.copy()
            return None
    
    def stop_stream(self):
        """停止后台视频流"""
        self._streaming = False
        if self._stream_thread and self._stream_thread.is_alive():
            self._stream_thread.join(timeout=1.0)
        print("后台视频流已停止")
    
    def close_video_stream(self):
        """关闭视频流"""
        self.stop_stream()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            print("视频流已关闭")
    
    def cleanup(self):
        """清理所有资源"""
        self.stop_stream()
        self.close_video_stream()
        self.video_client = None
        print("摄像头资源清理完成")
    
    def __del__(self):
        """析构函数"""
        try:
            self.cleanup()
        except:
            pass


# 便利函数
def capture_single_image(interface=None, save_path=None):
    """
    便利函数：获取单张图片
    
    Args:
        interface (str): 网卡接口
        save_path (str): 保存路径
        
    Returns:
        numpy.ndarray: 图像数据
    """
    camera = Go2Camera()
    if camera.init(interface):
        return camera.capture_image(save_path)
    return None


def create_video_stream(interface=None, width=480, height=320):
    """
    便利函数：创建视频流对象
    
    Args:
        interface (str): 网卡接口
        width (int): 视频宽度
        height (int): 视频高度
        
    Returns:
        Go2Camera: 摄像头对象
    """
    camera = Go2Camera(interface)
    if camera.init(interface):
        if camera.open_video_stream(width, height):
            return camera
    return None