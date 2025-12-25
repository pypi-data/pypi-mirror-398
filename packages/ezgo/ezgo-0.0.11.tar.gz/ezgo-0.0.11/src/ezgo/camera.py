import cv2
from PIL import Image, ImageTk
import platform

class Camera:
    def __init__(self, index=0, width=640, height=480, fps=30,):
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps

        self.cap = None
        # self.open_camera()

    def open_camera(self):

        if platform.system() == "Linux":
            self.cap = cv2.VideoCapture(self.index, cv2.CAP_V4L2)  # 启用 V4L2 硬件加速
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')  # 强制硬件压缩的 MJPG 格式（利用 FFMPEG 加速）
            self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        else:
            self.cap = cv2.VideoCapture(self.index)
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 清空缓存
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)

        if not self.cap.isOpened():
            raise Exception("无法打开摄像头")
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"打开摄像头 {self.index}，分辨率 {actual_width}x{actual_height}，帧率 {self.fps}")
        

    def read_cv2_image(self):
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("无法读取摄像头帧")
        return frame
    
    def read_pil_image(self):
        """将BGR帧转换为PIL"""
        frame = self.read_cv2_image()
        return self.cv2_to_pil(frame)
    
    def cv2_to_tk(self, frame):
        """将BGR帧转换为Tkinter PhotoImage"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb)
        frame_tk = ImageTk.PhotoImage(image=frame_pil)
        return frame_tk
    
    def resize(self, frame, size=(224, 224)):
        """将图像调整为指定尺寸"""
        return cv2.resize(frame, size, interpolation=cv2.INTER_LINEAR)
    
    def crop_to_square(self, frame):
        """将图像裁剪为正方形"""
        h, w = frame.shape[:2]
        min_dim = min(h, w)
        y = (h - min_dim) // 2
        x = (w - min_dim) // 2
        return frame[y:y+min_dim, x:x+min_dim]
    
    def __del__(self):
        """释放摄像头资源"""
        if self.cap is not None:
            self.cap.release()

