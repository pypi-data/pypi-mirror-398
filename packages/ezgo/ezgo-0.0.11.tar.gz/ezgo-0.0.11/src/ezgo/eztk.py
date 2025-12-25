import tkinter as tk
import numpy as np
import cv2
from PIL import Image, ImageTk
import platform
import os

class EasyTk:
    def __init__(self, title="APP", size=None):
        """
        初始化EasyTk窗口
        :param title: 窗口标题
        :param size: 窗口大小（格式："宽度x高度"，例如"480x800"）
        """
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(size)

        if platform.system() == "Linux":  # 灵芯派默认设置
            if size is None:
                self.root.geometry("480x800")  # 窗口分辨率480*800
            self.root.resizable(False, False)  # 固定窗口大小
            self.root.attributes('-fullscreen', True)  # 全屏
            self.root.config(cursor="none")  # 隐藏鼠标
        
        # self.root.update_idletasks()  # 强制立即应用全屏，避免闪烁/延迟

        self._image = None


    def add_frame(self, master=None, **kwargs):
        """
        添加一个框架（LabelFrame）到窗口中
    
        :param master: 父容器（默认是root）
        :param kwargs: 组件配置和布局参数
            组件配置常用参数：
            - width: 宽度（像素）,如果为空则根据内容自适应
            - height: 高度（像素），如果为空则根据内容自适应
            - bg: 背景颜色，例如"white"
            组件布局常用参数：
            - side: 组件在父容器中的位置，tk.TOP（上）、tk.BOTTOM（下）、tk.LEFT（左）、tk.RIGHT（右）
            - fill: 组件在父容器中的填充方式，tk.BOTH（填充父容器）、tk.X（填充水平方向）、tk.Y（填充垂直方向）
            - expand: 是否允许组件在父容器中扩展，True（允许）、False（不允许）
            - anchor: 组件在父容器中的对齐方式，tk.N（北）、tk.S（南）、tk.E（东）、tk.W（西）、tk.CENTER（居中）
            - padx: 组件在父容器中的水平间距，单位像素
            - pady: 组件在父容器中的垂直间距，单位像素

        :return: 新添加的框架（LabelFrame）
        :rtype: LabelFrame
        """
        kwargs['master'] = master if master else self.root
        pack_kwargs = {
            'side': kwargs.pop('side', tk.TOP),
            'fill': kwargs.pop('fill', tk.BOTH),
            'expand': kwargs.pop('expand', False if kwargs['master'] == self.root else True),
            'anchor': kwargs.pop('anchor', tk.CENTER),
            'padx': kwargs.pop('padx', 0),
            'pady': kwargs.pop('pady', 0)}

        frame = tk.Frame(**kwargs)
        if kwargs.get('width', None) and kwargs.get('height', None):
            pack_kwargs['fill'] = tk.NONE
        elif kwargs.get('width', None):
            pack_kwargs['fill'] = tk.Y
        elif kwargs.get('height', None):
            pack_kwargs['fill'] = tk.X

        frame.pack_propagate(False if (kwargs.get('width', None) or kwargs.get('height', None)) else True)
        frame.pack(**pack_kwargs)

        return frame

    def add_label(self, master=None, **kwargs):
        """
        添加一个标签（Label）到窗口中, 可以显示文本或图片
    
        :param master: 父容器（默认是root）
        :param kwargs: 组件配置和布局参数
            组件配置常用参数：
            - text: 显示的文本内容
            - image: 显示的图片路径、opencv图像（np.array）、PIL.Image.Image对象
            - font: 字体设置，例如("SimHei", 24)
            - fg: 字体颜色，例如"red"
            - bg: 背景颜色，例如"white"
            - width: 宽度（像素）,如果为空则根据内容自适应
            - height: 高度（像素），如果为空则根据内容自适应
            - wraplength: 文本换行长度，单位像素（默认0，不换行）
            组件布局常用参数：
            - side: 组件在父容器中的位置，tk.TOP（上）、tk.BOTTOM（下）、tk.LEFT（左）、tk.RIGHT（右）
            - fill: 组件在父容器中的填充方式，tk.BOTH（填充父容器）、tk.X（填充水平方向）、tk.Y（填充垂直方向）
            - expand: 是否允许组件在父容器中扩展，True（允许）、False（不允许）
            - anchor: 组件在父容器中的对齐方式，tk.N（北）、tk.S（南）、tk.E（东）、tk.W（西）、tk.CENTER（居中）
            - padx: 组件在父容器中的水平间距，单位像素
            - pady: 组件在父容器中的垂直间距，单位像素
        :return: 新添加的标签（Label）
        :rtype: Label
        """
        # 在Label外部添加一个Frame，用于布局控制
        master = master if master else self.root
        _kwargs = {
            "side" : kwargs.pop('side', tk.TOP),  # 堆叠方向
            "fill" : kwargs.pop('fill', tk.BOTH),  # 填充方向
            "expand" : kwargs.pop('expand', False if master == self.root else True) ,  # 是否展开填充
            "anchor" : kwargs.pop('anchor', tk.CENTER),
            "padx" : kwargs.pop('padx', 0),
            "pady" : kwargs.pop('pady', 0),
            "width" : kwargs.pop('width', None),
            "height" : kwargs.pop('height', None),
            "bg": kwargs.get('bg', None),
        }
        _frame = self.add_frame(master, **_kwargs)
        
        # 在Frame内部创建Label组件
        image = kwargs.pop('image', None)
        label = tk.Label(_frame, **kwargs)
        if image is not None:  # 配置图片
            self.config(label, image=image)
        label.pack(fill=tk.BOTH, expand=True)  # 放置组件
        return label
    

    def add_button(self, master=None, **kwargs):
        """
        添加一个按钮（Button）到窗口中, 可以显示文本或图片

        :param master: 父容器（默认是root）
        :param kwargs: 组件配置和布局参数
            组件配置常用参数：
            - text: 显示的文本内容
            - image: 显示的图片路径、opencv图像（np.array）、PIL.Image.Image对象
            - font: 字体设置，例如("SimHei", 24)
            - fg: 字体颜色，例如"red"
            - bg: 背景颜色，例如"white"
            - width: 宽度（像素）,如果为空则根据内容自适应
            - height: 高度（像素），如果为空则根据内容自适应
            - wraplength: 文本换行长度，单位像素（默认0，不换行）
            组件布局常用参数：
            - side: 组件在父容器中的位置，tk.TOP（上）、tk.BOTTOM（下）、tk.LEFT（左）、tk.RIGHT（右）
            - fill: 组件在父容器中的填充方式，tk.BOTH（填充父容器）、tk.X（填充水平方向）、tk.Y（填充垂直方向）
            - expand: 是否允许组件在父容器中扩展，True（允许）、False（不允许）
            - anchor: 组件在父容器中的对齐方式，tk.N（北）、tk.S（南）、tk.E（东）、tk.W（西）、tk.CENTER（居中）
            - padx: 组件在父容器中的水平间距，单位像素
            - pady: 组件在父容器中的垂直间距，单位像素
        :return: 新添加的按钮（Button）
        :rtype: Button
        """

        kwargs['master'] = master if master else self.root
        pack_kwargs = {
            'side': kwargs.pop('side', tk.TOP),
            'fill': kwargs.pop('fill', tk.NONE),  # 按钮默认不填充父容器
            'expand': kwargs.pop('expand', False if kwargs['master'] == self.root else True),
            'anchor': kwargs.pop('anchor', tk.CENTER),
            'padx': kwargs.pop('padx', 10),  # 按钮默认水平间距10像素
            'pady': kwargs.pop('pady', 10)}  # 按钮默认垂直间距10像素
        kwargs['master'] = master if master else self.root

        # 创建组件
        image = kwargs.pop('image', None)  
        button = tk.Button(**kwargs)
        if image is not None:  # 配置图片
            self.config(button, image=image)
        button.pack(pack_kwargs)  # 放置组件

        return button
    
    def config(self, widget, **kwargs):
        """
        1. 仅当传入image参数时，才处理图片转换和引用
        2. 不传入image时，不修改image参数
        """
        # 处理图片参数（仅当传入image时）
        if 'image' in kwargs:
            img = kwargs['image']
            img_tk = self._convert_image(img)
            widget.img_tk = img_tk  # 关键：保留引用，避免垃圾回收
            kwargs['image'] = img_tk
        
        # 执行组件配置
        widget.config(**kwargs)

    def _convert_image(self, img):
        """
        将不同格式的图片转换为tkinter可用的PhotoImage对象
        支持：字符串路径、OpenCV图像（BGR格式）、PIL Image对象
        """
        if isinstance(img, str) and img:  # 字符串路径
            # 检查文件是否存在
            if not os.path.exists(img):
                raise FileNotFoundError(f"图片文件不存在：{img}")
            img_cv = cv2.imread(img)
            img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(img_pil)
        elif isinstance(img, np.ndarray):  # OpenCV图像（BGR格式）
            if len(img.shape) not in (2, 3):
                raise ValueError("OpenCV图像维度错误，需为2D/3D数组")
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if len(img.shape) == 3 else img
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(img_pil)
        elif isinstance(img, Image.Image):  # PIL Image对象
            img_tk = ImageTk.PhotoImage(img)
        elif isinstance(img, ImageTk.PhotoImage):
            img_tk = img
        else:  # 清空图片
            img_tk = ""  # 用空字符串替代None，避免tkinter报错
        return img_tk

    def after(self, delay, func):
        self.root.after(delay, func)

    def run(self):
        self.root.mainloop()

    def quit(self):
        self.root.quit()
        self.root.destroy()

