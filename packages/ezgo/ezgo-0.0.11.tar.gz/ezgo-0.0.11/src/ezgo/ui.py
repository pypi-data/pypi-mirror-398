import tkinter as tk
import platform
import os


if platform.system() == "Linux":
    os.environ["DISPLAY"] = ":0"

class APP(tk.Tk):
    def __init__(self, title="APP", width=480, height=800):
        super().__init__()
        self.title_text = title
        self.title(self.title_text)
        self.geometry(f"{width}x{height}")
        
        if platform.system() == "Linux":
            self.resizable(False, False)  # 固定窗口大小
            self.attributes('-fullscreen', True)  # 全屏
            self.config(cursor="none")  # 隐藏鼠标
            self.update_idletasks()  # 强制立即应用全屏，避免闪烁/延迟
        
        # 显示图像和文字的全局变量
        self.image = None  # 显示的图像
        self.text = ""  # 显示的文字

        self.is_running = True  # 程序运行状态

        # 初始化组件
        self.create_widgets()
        # 绑定窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # 标题
        title_label = tk.Label(self, text=self.title_text, font=("SimHei", 18))
        title_label.pack(pady=5)

        # 图像显示区域
        self.frame1 = tk.LabelFrame(self, text="图像", width=480, height=480, font=("SimHei", 10))
        self.frame1.pack_propagate(False)
        self.frame1.pack(fill=tk.X, pady=5)
        self.image_label = tk.Label(self.frame1)
        self.image_label.pack(pady=5, fill=tk.BOTH, expand=True, anchor=tk.CENTER)

        # 文字显示区域
        self.frame2 = tk.LabelFrame(self, text="结果", width=480, height=200, font=("SimHei", 10))
        self.frame2.pack_propagate(False)
        self.frame2.pack(fill=tk.X, pady=5)
        self.text_label = tk.Label(self.frame2, 
                                   text="文本显示", 
                                   font=("SimHei", 14),
                                   wraplength=450,
                                   justify=tk.CENTER,)
        self.text_label.pack(pady=5, fill=tk.BOTH, expand=True, anchor=tk.CENTER)


        # 退出按钮
        self.exit_btn = tk.Button(self, text="退出", command=self.on_close, font=("SimHei", 16))
        self.exit_btn.pack(pady=10)

    
    def set_image(self, image):
        """设置显示的图像"""
        self.image = image
        self.image_label.config(image=self.image)

    def set_text(self, text):
        """设置显示的文字"""
        self.text = text
        self.text_label.config(text=self.text)

    def on_close(self):
        """窗口关闭/退出按钮回调"""
        self.is_running = False
        self.quit()  # 退出主循环
        self.destroy()  # 销毁窗口

