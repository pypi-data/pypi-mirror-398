import cv2
from PIL import Image, ImageTk
import platform
import time
import queue
import threading


class Camera:
    def __init__(self, index=0, width=640, height=480, fps=30,):
        """
        初始化摄像头对象。

        参数:
        - index: 摄像头索引，默认值为 0。
        - width: 视频宽度，默认值为 640。
        - height: 视频高度，默认值为 480。
        - fps: 视频帧率，默认值为 30。
        """
        # 基础参数
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps

        # 状态控制
        self.is_opened = False  # 摄像头是否成功打开
        self.is_running = False  # 线程退出标志
        self.first_frame_ready = threading.Event()  # 第一帧就绪事件

        # 资源管理
        self.cap = None
        self.capture_thread = None  # 读帧线程对象


        # 双缓冲：两个缓冲区
        self.buffer_write = None  # 写入缓冲区
        self.buffer_read = None   # 读取缓冲区
        self.buffer_lock = threading.Lock()  # 用于交换缓冲区的锁

        # 线程锁
        # self.lock = threading.Lock()
        
        

    def open(self, timeout=5):
        """
        打开摄像头。
        若在 Linux 系统下，启用 V4L2 硬件加速和 MJPG 压缩格式。

        参数:
        - timeout: 等待第一帧图像的超时时间，默认值为 5 秒。
        """
        
        if self.is_opened:
            print(f"摄像头 {self.index} 已打开")
            return True

        if platform.system() == "Linux":
            self.cap = cv2.VideoCapture(self.index, cv2.CAP_V4L2)
            # 尝试设置MJPG格式（硬件加速）
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 减少摄像头缓冲区，降低延迟
        elif platform.system() == "Windows":
            self.cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)  # 替代默认的CAP_MSMF，降低延迟
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        else:  # macOS
            self.cap = cv2.VideoCapture(self.index)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

        if not self.cap.isOpened():
            raise Exception("无法打开摄像头")

        # 仅当实际分辨率不一致时才设置分辨率
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if actual_width != self.width or actual_height != self.height:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        # 重置状态
        self.first_frame_ready.clear()
        self.buffer_write = None
        self.buffer_read = None

        # 启动读帧线程
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_thread, daemon=True)
        self.capture_thread.start()

        # 等待第一帧就绪（带超时）
        if not self.first_frame_ready.wait(timeout=timeout):
            self.close()
            raise TimeoutError(f"等待第一帧超时（{timeout}秒）")

        self.is_opened = True

        return self

    def _capture_thread(self):
        """读取图像帧线程"""
        frame_interval = 1.0 / self.fps  # 理论帧间隔
        first_frame = True
        next_frame_time = time.time()  # 初始化
        while self.is_running and self.cap.isOpened():
            start_time = time.time()
            # 读取帧
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.001)
                continue

            # 写入缓冲区
            with self.buffer_lock:
                # 先交换缓冲区：把已写好的交给读缓冲区
                self.buffer_write, self.buffer_read = self.buffer_read, self.buffer_write
                # 再写入新帧到空的写缓冲区
                self.buffer_write = frame

            # 标记第一帧就绪
            if first_frame  and self.buffer_read is not None:
                self.first_frame_ready.set()
                first_frame = False
                
            # 基于绝对时间的帧率控制，避免累积误差
            next_frame_time += frame_interval
            sleep_time = max(0, next_frame_time - time.time())
            # 短睡眠用time.sleep，长睡眠用cv2.waitKey（更低CPU占用）
            if sleep_time > 0.01:
                cv2.waitKey(int(sleep_time * 1000))  # 毫秒级，释放GIL
            else:
                time.sleep(sleep_time)

    def read(self):
        """读取最新帧"""
        frame = None
        with self.buffer_lock:
            if self.buffer_read is not None:
                frame = self.buffer_read  # 先引用，不拷贝
        return frame.copy() if frame is not None else None  # 仅当有数据时拷贝
    
    def save_image(self, frame, filename="frame.jpg"):
        """保存当前帧到文件"""
        if frame is None:
            raise ValueError("无法保存空帧")
        cv2.imwrite(filename, frame)
        
    def resize(self, frame, size=(224, 224)):
        """将图像调整为指定尺寸"""
        if frame is None:
            return None
        return cv2.resize(frame, size, interpolation=cv2.INTER_LINEAR)
    
    def crop_to_square(self, frame):
        """将图像裁剪为正方形"""
        if frame is None:
            return None
        h, w = frame.shape[:2]
        min_dim = min(h, w)
        y = (h - min_dim) // 2
        x = (w - min_dim) // 2
        return frame[y:y+min_dim, x:x+min_dim]
    
    def close(self):
        """手动释放资源"""
        self.is_running = False  # 停止读帧线程
        self.is_opened = False

        if self.capture_thread is not None:
            self.capture_thread.join(timeout=1.0)  # 等待线程退出
            self.capture_thread = None
            
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def __del__(self):
        """释放资源"""
        self.close()