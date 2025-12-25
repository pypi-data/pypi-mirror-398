#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ezgo - 宇树Go2机器狗Python控制库

这是一个用于控制宇树Go2机器狗的Python库，提供了简单易用的API接口。
支持运动控制、视频流获取、UI界面等功能。
"""

__version__ = "0.0.11"
__author__ = "ezgo"
__email__ = ""
__license__ = "MIT"

# 懒加载模块 - 只在实际使用时才导入
def _lazy_import(module_name, class_name):
    """懒加载模块，避免导入时的依赖检查"""
    def _import():
        try:
            # 使用importlib代替__import__，更可靠
            import importlib
            module = importlib.import_module(f'.{module_name}', package=__name__)
            return getattr(module, class_name)
        except ImportError as e:
            # 只在使用时才提示依赖缺失
            raise ImportError(f"使用 {class_name} 需要安装额外依赖: {e}")
    return _import

# 定义懒加载函数
_Go2 = _lazy_import('go2', 'Go2')
_Camera = _lazy_import('camera', 'Camera')
_APP = _lazy_import('ui', 'APP')
_Go2Camera = _lazy_import('go2_camera', 'Go2Camera')
_Go2VUI = _lazy_import('go2_vui', 'Go2VUI')

# 直接导入不需要额外依赖的模块
try:
    from .eztk import EasyTk
    from .ezcamera import Camera as EzCamera
except ImportError as e:
    # 这些模块应该能正常导入，如果失败则显示错误
    print(f"错误: 无法导入核心模块: {e}")
    EasyTk = None
    EzCamera = None

# 定义公开的API
__all__ = [
    "Go2",
    "Camera", 
    "APP",
    "Go2Camera",
    "Go2VUI",
    "EasyTk",
    "EzCamera",
    "__version__"
]

# 懒加载属性访问器
class _LazyModule:
    def __init__(self, import_func):
        self._import_func = import_func
        self._module = None
    
    def __call__(self, *args, **kwargs):
        if self._module is None:
            self._module = self._import_func()
        return self._module(*args, **kwargs)
    
    def __getattr__(self, name):
        if self._module is None:
            self._module = self._import_func()
        return getattr(self._module, name)

# 创建懒加载对象
Go2 = _LazyModule(_Go2)
Camera = _LazyModule(_Camera)
APP = _LazyModule(_APP)
Go2Camera = _LazyModule(_Go2Camera)
Go2VUI = _LazyModule(_Go2VUI)

