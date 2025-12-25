import time
import threading
import numpy as np
import cv2
import netifaces
import subprocess
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient
from unitree_sdk2py.go2.video.video_client import VideoClient
from unitree_sdk2py.idl.unitree_go.msg.dds_ import SportModeState_


error_code = {
    0: "检查设备状态",
    100: "灵动",
    1001: "阻尼",
    1002: "站立锁定",
    1004: "蹲下",
    2006: "蹲下",
    1006: "打招呼/伸懒腰/舞蹈/拜年/比心/开心",
    1007: "坐下",
    1008: "前跳",
    1009: "扑人",
    1013: "平衡站立",
    1015: "常规行走",
    1016: "常规跑步",
    1017: "常规续航",
    1091: "摆姿势",
    2004: "翻身",   # ???
    2007: "闪避",
    2008: "并腿跑",
    2009: "跳跃跑",
    2010: "经典",
    2011: "倒立",
    2012: "前空翻",
    2013: "后空翻",
    2014: "左空翻",
    2016: "交叉步",
    2017: "直立",
    2019: "牵引",
}


class Go2:
    """
    宇树Go2 运动控制封装类
    适用于：Unitree SDK2 Python接口
    """
    def __init__(self, interface=None, timeout=20.0):
        """
        初始化控制器
        :param interface: 网卡接口名称
        :param timeout: 超时时间（秒）
        """
        self.interface = interface
        self.timeout = timeout
        self.sport_client = None
        self.video_client = None
        self.cap = None
        self.error_code = 0  # 状态码
        
        # 移动控制相关变量
        self._moving = False
        self._move_params = (0, 0, 0)
        self._move_thread = None
        
        # 摄像头对象
        self.camera = None
        
        # 声光控制对象
        self._vui = None

        if self.interface is None:
            self.get_interface()
        
        # 清理标志
        self._initialized = False

    def get_interface(self):
        """获取当前接口"""

        interfaces = netifaces.interfaces()
        for iface in interfaces:
            if iface.startswith("en"):
                self.interface = iface
                break

    def check_go2_connection(self):
        """检查机器狗IP连通性"""
        try:
            # 先尝试不使用sudo ping
            result = subprocess.run(['ping', '-c', '1', '-W', '2', '192.168.123.161'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True
            
            # 如果不使用sudo失败，尝试使用sudo
            result = subprocess.run(['sudo', 'ping', '-c', '1', '-W', '2', '192.168.123.161'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("ping超时")
            return False
        except Exception as e:
            print(f"检查连接时出错: {e}")
            return False
        



    def init(self):
        """初始化与Go2的连接"""
        
        # 检查机器狗IP连通性（仅作为警告，不阻止初始化）
        if not self.check_go2_connection():
            print("警告：无法ping通机器狗IP，但继续尝试初始化SDK")
            print("请确保机器狗已开机且网络连接正常")
        
        try:
            ChannelFactoryInitialize(0, self.interface)

            # 启动状态订阅
            self.sub_state(self.callback)

            # 初始化运动控制客户端
            self.sport_client = SportClient()
            self.sport_client.SetTimeout(self.timeout)
            self.sport_client.Init()
            
            # 注意：视频流不再自动初始化，按需开启
            # self.cap = self.open_video()  # 移除自动初始化
            
            self._initialized = True
            print("Go2 SDK初始化成功")
            return True
        except Exception as e:
            print(f"SDK初始化失败: {e}")
            return False
        

    def open_video(self, width: int = 480, height: int = 320):
        """打开视频流"""
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
        cap = cv2.VideoCapture(gstreamer_str, cv2.CAP_GSTREAMER)
        if not cap.isOpened():
            print("视频流打开失败")
            print(f"使用的网络接口: {self.interface}")
            print("GStreamer字符串:", gstreamer_str)
            return None
        print("视频流打开成功")
        return cap

    def read_image(self):
        """从视频流获取一帧图像"""
        if self.cap is None:
            print("视频流未打开，请先调用 open_video()")
            return None
            
        ret, frame = self.cap.read()
        if not ret:
            print("读取图像失败")
            return None
        return frame

    
    def sub_state(self, callback, queue_size: int = 5):
        subscriber = ChannelSubscriber("rt/sportmodestate", SportModeState_)
        subscriber.Init(callback, queue_size)

    def callback(self, msg):
        self.error_code = msg.error_code


    # def read_image(self):
    #     """从视频流获取一帧图像"""
    #     code, data = self.video_client.GetImageSample()
    #     if code != 0 or data is None:
    #         print("获取图像样本失败，错误码:", code)
    #         return None
    #     image_data = np.frombuffer(bytes(data), dtype=np.uint8)
    #     image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    #     return image

    def Damp(self):
        """进入阻尼状态。"""
        self._call(self.sport_client.Damp)

    def BalanceStand(self):
        """解除锁定。"""
        self._call(self.sport_client.BalanceStand)

    def StopMove(self):
        """
        停止机器狗的所有移动动作，并重置相关状态。
        
        该方法会：
        1. 停止任何正在执行的移动线程
        2. 调用底层SDK的停止方法
        3. 重置移动状态标志
        
        注意:
        - 该方法会阻塞等待移动线程结束，最多等待1秒
        - 调用后所有运动指令将被重置为默认状态
        """
        print("停止移动")
        # 停止持续移动线程
        self._moving = False
        if (hasattr(self, '_move_thread') and 
            self._move_thread is not None and 
            self._move_thread.is_alive()):
            self._move_thread.join(timeout=1.0)
            self._move_thread = None
        
        # 调用SDK的停止方法
        self._call(self.sport_client.StopMove)

    def _call(self, func, *args, **kwargs):
        """在线程中调用运动控制函数"""
        def fun_thread():
            ret = func(*args, **kwargs)
            print(f"{func.__name__} 执行结果:", ret)
        
        t = threading.Thread(target=fun_thread)
        t.start()
        t.join()  # 等待线程完成



    def StandUp(self):
        """
        关节锁定，站高。
        执行后状态: 1002:站立锁定
        """
        # 执行前判断状态
        if self.error_code in [1002]:  # 1002 :站立锁定
            print("当前状态:", self.error_code, error_code[self.error_code], "无需执行")
            return
        if self.error_code not in [100, 1001, 1007, 1013]:  # 100 :灵动, 1001 :阻尼, 1013 :平衡站立
            print("繁忙中,当前状态:", self.error_code, error_code[self.error_code])
            return
        self._call(self.sport_client.StandUp)



    def StandDown(self):
        """
        关节锁定，站低。
        执行后状态: 1001:阻尼
        """
        # 执行前判断状态
        if self.error_code in [1001, 1004, 2006]:  # 1001:阻尼 1004 :蹲下 2006 :蹲下
            print("当前状态:", self.error_code, error_code[self.error_code], "无需执行")
            return
        if self.error_code not in [100, 1002, 1013]:  # 100 :灵动, 1001 :阻尼, 1013 :平衡站立
            print("繁忙中,当前状态:", self.error_code, error_code[self.error_code])
            return
        
        # 执行指令
        self._call(self.sport_client.StandDown)

    def RecoveryStand(self):
        """	恢复站立。"""
        self._call(self.sport_client.RecoveryStand)

    def Euler(self, roll, pitch, yaw):
        """站立和行走时的姿态。"""
        pass

    def Move(self, vx, vy, vyaw):
        """移动。"""
        # 检查状态是否允许移动
        if self.error_code not in [100, 1002, 1013]:  # 100:灵动, 1002:站立锁定, 1013:平衡站立
            print(f"当前状态不允许移动: {self.error_code} - {error_code.get(self.error_code, '未知状态')}")
            return False
        
        # 限制速度范围
        vx = max(-1.0, min(1.0, vx))  # 前后速度限制在-1到1之间
        vy = max(-1.0, min(1.0, vy))  # 左右速度限制在-1到1之间
        vyaw = max(-2.0, min(2.0, vyaw))  # 转动速度限制在-2到2之间
        
        def move_thread():
            ret = self.sport_client.Move(vx, vy, vyaw)
            success = ret == 0
            print(f"Move 执行结果: {ret}, 成功: {success}")
            return success
        
        t = threading.Thread(target=move_thread)
        t.start()
        t.join()
        return True

    def MoveForDuration(self, vx, vy, vyaw, duration):
        """
        持续移动指定时间
        
        Args:
            vx (float): 前后速度 (-1.0 到 1.0)
            vy (float): 左右速度 (-1.0 到 1.0)  
            vyaw (float): 转动速度 (-2.0 到 2.0)
            duration (float): 移动时间（秒）
            
        Returns:
            bool: 是否成功执行
        """
        print(f"开始移动: vx={vx}, vy={vy}, vyaw={vyaw}, 持续时间={duration}秒")
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                if not self.Move(vx, vy, vyaw):
                    return False
                time.sleep(0.1)  # 每100ms调用一次
            
            print("移动完成")
            return True
            
        except KeyboardInterrupt:
            print("移动被用户中断")
            return False

    def Forward(self, speed=0.3, duration=2.0):
        """向前移动"""
        return self.MoveForDuration(speed, 0, 0, duration)

    def Backward(self, speed=0.3, duration=2.0):
        """向后移动"""
        return self.MoveForDuration(-speed, 0, 0, duration)

    def Left(self, speed=0.3, duration=2.0):
        """向左移动"""
        return self.MoveForDuration(0, speed, 0, duration)

    def Right(self, speed=0.3, duration=2.0):
        """向右移动"""
        return self.MoveForDuration(0, -speed, 0, duration)

    def TurnLeft(self, speed=0.5, duration=2.0):
        """左转"""
        return self.MoveForDuration(0, 0, speed, duration)

    def TurnRight(self, speed=0.5, duration=2.0):
        """右转"""
        return self.MoveForDuration(0, 0, -speed, duration)

    def StartMove(self, vx, vy, vyaw):
        """
        开始持续移动，需要调用StopMove来停止
        
        Args:
            vx (float): 前后速度 (-1.0 到 1.0)
            vy (float): 左右速度 (-1.0 到 1.0)  
            vyaw (float): 转动速度 (-2.0 到 2.0)
            
        Returns:
            bool: 是否成功开始移动
        """
        print(f"开始持续移动: vx={vx}, vy={vy}, vyaw={vyaw}")
        
        # 先检查是否可以移动
        if not self.Move(vx, vy, vyaw):
            print("无法开始持续移动：当前状态不允许移动")
            return False
            
        self._moving = True
        self._move_params = (vx, vy, vyaw)
        
        def continuous_move():
            while self._moving:
                if not self.Move(vx, vy, vyaw):
                    print("持续移动失败，停止移动")
                    break
                time.sleep(0.1)
        
        self._move_thread = threading.Thread(target=continuous_move)
        self._move_thread.daemon = True  # 设置为守护线程
        self._move_thread.start()
        return True

    def StartForward(self, speed=0.3):
        """开始向前移动"""
        return self.StartMove(speed, 0, 0)

    def StartBackward(self, speed=0.3):
        """开始向后移动"""
        return self.StartMove(-speed, 0, 0)

    def StartLeft(self, speed=0.3):
        """开始向左移动"""
        return self.StartMove(0, speed, 0)

    def StartRight(self, speed=0.3):
        """开始向右移动"""
        return self.StartMove(0, -speed, 0)

    def StartTurnLeft(self, speed=0.5):
        """开始左转"""
        return self.StartMove(0, 0, speed)

    def StartTurnRight(self, speed=0.5):
        """开始右转"""
        return self.StartMove(0, 0, -speed)

    def Sit(self):
        """
        坐下。
        执行后状态: 1007: 坐下
        """
        # 执行前判断状态
        if self.error_code in [1007]:  # 1007 : 坐下
            print("当前状态:", self.error_code, error_code[self.error_code], "无需执行")
            return
        if self.error_code not in [100, 1002, 1013]:  # 100 :灵动, 1001 :阻尼, 1013 :平衡站立
            print("繁忙中,当前状态:", self.error_code, error_code[self.error_code])
            return
        
        # 执行指令
        self._call(self.sport_client.Sit)

    def RiseSit(self):
        """
        站起（相对于坐下）。
        执行后状态: 
        """
        # 执行前判断状态
        if self.error_code in [1007]:  # 1002 :站立锁定
            print("当前状态:", self.error_code, error_code[self.error_code], "无需执行")
            return
        if self.error_code not in [100, 1007, 1013]:  # 100 :灵动, 1007 : 坐下, 1013 :平衡站立
            print("繁忙中,当前状态:", self.error_code, error_code[self.error_code])
            return
        
        # 执行指令
        self._call(self.sport_client.RiseSit)



    def SpeedLevel(self, level: int):
        """设置速度档位。"""
        pass

    def Hello(self):
        """
        打招呼
        执行后状态: 1013:平衡站立
        """
        # 执行前判断状态
        if self.error_code in [1006]:  # 1006 :打招呼/伸懒腰/舞蹈/拜年/比心/开心
            print("当前状态:", self.error_code, error_code[self.error_code], "无需执行")
            return
        if self.error_code not in [100, 1002, 1013]:  # 空闲状态
            print("繁忙中,当前状态:", self.error_code, error_code[self.error_code])
            return

        # 执行指令
        self._call(self.sport_client.Hello)

    def Stretch(self):
        """
        伸懒腰。
        执行后状态: 1013:平衡站立
        """
        # 执行前判断状态
        if self.error_code in [1006]:  # 1006 :打招呼/伸懒腰/舞蹈/拜年/比心/开心
            print("当前状态:", self.error_code, error_code[self.error_code], "无需执行")
            return
        if self.error_code not in [100, 1002, 1013]:  # 站立且空闲状态
            print("繁忙中,当前状态:", self.error_code, error_code[self.error_code])
            return
        
        # 执行指令
        self._call(self.sport_client.Stretch)



    def Content(self):
        """
        开心。
        执行后状态: 1013:平衡站立
        """
        # 执行前判断状态
        if self.error_code in [1006]:  # 1006 :打招呼/伸懒腰/舞蹈/拜年/比心/开心
            print("当前状态:", self.error_code, error_code[self.error_code], "无需执行")
            return
        if self.error_code not in [100, 1002, 1013]:  # 空闲状态
            print("繁忙中,当前状态:", self.error_code, error_code[self.error_code])
            return
        
        # 执行指令
        self._call(self.sport_client.Content)


    def Heart(self):
        """
        比心。
        执行后状态: 1013:平衡站立
        """
        # 执行前判断状态
        if self.error_code in [1006]:  # 1006 :打招呼/伸懒腰/舞蹈/拜年/比心/开心
            print("当前状态:", self.error_code, error_code[self.error_code], "无需执行")
            return
        if self.error_code not in [100, 1002, 1013]:  # 空闲状态
            print("繁忙中,当前状态:", self.error_code, error_code[self.error_code])
            return
        
        # 执行指令
        self._call(self.sport_client.Heart)


    def Pose(self, flag):
        """摆姿势。"""
        pass

    def Scrape(self):
        """ 
        拜年作揖。
        执行后状态: 1013:平衡站立
        """
        # 执行前判断状态
        if self.error_code in [1006]:  # 1006 :打招呼/伸懒腰/舞蹈/拜年/比心/开心
            print("当前状态:", self.error_code, error_code[self.error_code], "无需执行")
            return
        if self.error_code not in [100, 1002, 1013]:  # 空闲状态
            print("繁忙中,当前状态:", self.error_code, error_code[self.error_code])
            return
        
        # 执行指令
        self._call(self.sport_client.Scrape)



    def FrontJump(self):
        """ 
        前跳。
        执行后状态: 1013: 平衡站立
        """
        # 执行前判断状态
        if self.error_code in [1008]:  # 1008 : 前跳
            print("当前状态:", self.error_code, error_code[self.error_code], "无需执行")
            return
        if self.error_code not in [100, 1002, 1013]:  # 空闲状态
            print("繁忙中,当前状态:", self.error_code, error_code[self.error_code])
            return
        
        # 执行指令
        self._call(self.sport_client.FrontJump)



    def FrontPounce(self):
        """ 
        向前扑人。
        执行后状态: 1013: 平衡站立
        """
        # 执行前判断状态
        if self.error_code in [1009]:  # 1009 : 扑人
            print("当前状态:", self.error_code, error_code[self.error_code], "无需执行")
            return
        if self.error_code not in [100, 1002, 1013]:  # 空闲状态
            print("繁忙中,当前状态:", self.error_code, error_code[self.error_code])
            return
        
        # 执行指令
        self._call(self.sport_client.FrontPounce)


    def Dance1(self):
        """
        舞蹈段落1。
        执行后状态: 1013: 平衡站立
        """
        # 执行前判断状态
        if self.error_code in [1006]:  # 1006 :打招呼/伸懒腰/舞蹈/拜年/比心/开心
            print("当前状态:", self.error_code, error_code[self.error_code], "无需执行")
            return
        if self.error_code not in [100, 1002, 1013]:  # 空闲状态
            print("繁忙中,当前状态:", self.error_code, error_code[self.error_code])
            return
        
        # 执行指令
        self._call(self.sport_client.Dance1)
    
    def Dance2(self):
        """
        舞蹈段落2。
        执行后状态: 1013: 平衡站立
        """
        # 执行前判断状态
        if self.error_code in [1006]:  # 1006 :打招呼/伸懒腰/舞蹈/拜年/比心/开心
            print("当前状态:", self.error_code, error_code[self.error_code], "无需执行")
            return
        if self.error_code not in [100, 1002, 1013]:  # 空闲状态
            print("繁忙中,当前状态:", self.error_code, error_code[self.error_code])
            return
        
        # 执行指令
        self._call(self.sport_client.Dance2)
    
    def HandStand(self, flag: int):
        """倒立行走。"""
        # 执行指令
        self._call(lambda: self.sport_client.HandStand(bool(flag)))
        if flag:
            time.sleep(4)
            self._call(lambda: self.sport_client.HandStand(False))

    def LeftFlip(self):
        """左空翻。"""
        # 执行指令
        result = self._call(self.sport_client.LeftFlip)
        return result == 0 if result is not None else False

    def BackFlip(self):
        """后空翻。"""
        # 执行指令
        result = self._call(self.sport_client.BackFlip)
        return result == 0 if result is not None else False

    def FreeWalk(self, flag: int = None):
        """ 灵动模式（默认步态）。"""
        # 执行指令
        if flag is None:
            # 切换模式
            result = self._call(lambda: self.sport_client.FreeWalk())
        else:
            # 根据flag值执行相应操作
            if flag:
                # 开启灵动模式
                result = self._call(lambda: self.sport_client.FreeWalk())
            else:
                # 关闭灵动模式 - 切换到其他模式
                result = self._call(lambda: self.sport_client.StandUp())
        return result == 0 if result is not None else False

    def FreeBound(self, flag: int):
        """ 并腿跑模式。"""
        # 执行指令
        result = self._call(lambda: self.sport_client.FreeBound(bool(flag)))
        success = result == 0 if result is not None else False
        
        if flag and success:
            # 如果成功开启，等待2秒后自动关闭（这是为了演示效果）
            time.sleep(2)
            self._call(lambda: self.sport_client.FreeBound(False))
        
        return success

    def FreeJump(self, flag: int):
        """ 跳跃模式。"""
        # 执行指令
        result = self._call(lambda: self.sport_client.FreeJump(bool(flag)))
        success = result == 0 if result is not None else False
        
        if flag and success:
            # 如果成功开启，等待4秒后自动关闭（这是为了演示效果）
            time.sleep(4)
            self._call(lambda: self.sport_client.FreeJump(False))
        
        return success

    def FreeAvoid(self, flag: int):
        """ 闪避模式。"""
        # 执行指令
        result = self._call(lambda: self.sport_client.FreeAvoid(bool(flag)))
        success = result == 0 if result is not None else False
        
        if flag and success:
            # 如果成功开启，等待2秒后自动关闭（这是为了演示效果）
            time.sleep(2)
            self._call(lambda: self.sport_client.FreeAvoid(False))
        
        return success

    def WalkUpright(self, flag: int):
        """ 后腿直立模式。"""
        # 执行指令
        result = self._call(lambda: self.sport_client.WalkUpright(bool(flag)))
        success = result == 0 if result is not None else False
        
        if flag and success:
            # 如果成功开启，等待4秒后自动关闭（这是为了演示效果）
            time.sleep(4)
            self._call(lambda: self.sport_client.WalkUpright(False))
        
        return success

    def CrossStep(self, flag: int):
        """ 交叉步模式。"""
        # 执行指令
        result = self._call(lambda: self.sport_client.CrossStep(bool(flag)))
        success = result == 0 if result is not None else False
        
        if flag and success:
            # 如果成功开启，等待4秒后自动关闭（这是为了演示效果）
            time.sleep(4)
            self._call(lambda: self.sport_client.CrossStep(False))
        
        return success

    def AutoRecoverSet(self, flag: int):
        """ 设置自动翻身是否生效。"""
        try:
            # 执行指令
            result = self._call(lambda: self.sport_client.AutoRecoverSet(bool(flag)))
            return result == 0 if result is not None else False
        except AttributeError:
            print("警告: AutoRecoverSet 方法在当前SDK版本中不可用")
            return False

    def AutoRecoverGet(self):
        """ 查询自动翻身是否生效。"""
        try:
            # 执行指令
            result = self._call(self.sport_client.AutoRecoverGet)
            return result if result is not None else False
        except AttributeError:
            print("警告: AutoRecoverGet 方法在当前SDK版本中不可用")
            return False

    def ClassicWalk(self, flag: int):
        """ 经典步态。"""
        try:
            # 执行指令
            result = self._call(lambda: self.sport_client.ClassicWalk(bool(flag)))
            return result == 0 if result is not None else False
        except AttributeError:
            print("警告: ClassicWalk 方法在当前SDK版本中不可用")
            return False

    def TrotRun(self):
        """ 进入常规跑步模式 """
        try:
            # 执行指令
            result = self._call(self.sport_client.TrotRun)
            return result == 0 if result is not None else False
        except AttributeError:
            print("警告: TrotRun 方法在当前SDK版本中不可用")
            return False

    def StaticWalk(self):
        """ 进入常规行走模式"""
        try:
            # 执行指令
            result = self._call(self.sport_client.StaticWalk)
            return result == 0 if result is not None else False
        except AttributeError:
            print("警告: StaticWalk 方法在当前SDK版本中不可用")
            return False

    def EconomicGait(self):
        """ 进入常规续航模式 """
        try:
            # 执行指令
            result = self._call(self.sport_client.EconomicGait)
            return result == 0 if result is not None else False
        except AttributeError:
            print("警告: EconomicGait 方法在当前SDK版本中不可用")
            return False

    def SwitchAvoidMode(self):
        """ 闪避模式下，关闭摇杆未推时前方障碍物的闪避以及后方的障碍物躲避"""
        try:
            # 执行指令
            result = self._call(self.sport_client.SwitchAvoidMode)
            return result == 0 if result is not None else False
        except AttributeError:
            print("警告: SwitchAvoidMode 方法在当前SDK版本中不可用")
            return False
    
    def get_camera(self):
        """
        获取摄像头对象（按需初始化）
        
        Returns:
            Go2Camera: 摄像头控制对象
        """
        if self.camera is None:
            # 直接导入go2_camera模块
            from .go2_camera import Go2Camera
            self.camera = Go2Camera(self.interface, self.timeout)
            # 注意：这里不自动初始化，让用户按需调用
        return self.camera
    
    def get_vui(self):
        """
        获取声光控制对象（按需初始化）
        
        Returns:  
            Go2VUI: 声光控制对象
        """
        if not hasattr(self, '_vui') or self._vui is None:
            # 直接导入go2_vui模块
            from .go2_vui import Go2VUI
            self._vui = Go2VUI(self.interface)
            # 注意：这里不自动初始化，让用户按需调用
        return self._vui
    
    def capture_image(self, save_path=None):
        """
        便利方法：获取一张图片（按需初始化摄像头）
        
        Args:
            save_path (str): 保存路径
            
        Returns:
            numpy.ndarray: 图像数据
        """
        camera = self.get_camera()
        if not camera.init(self.interface):
            print("摄像头初始化失败")
            return None
        return camera.capture_image(save_path)
    
    def start_video_stream(self, width=480, height=320):
        """
        便利方法：开始视频流（按需初始化摄像头）
        
        Args:
            width (int): 视频宽度
            height (int): 视频高度
            
        Returns:
            bool: 是否成功
        """
        camera = self.get_camera()
        if not camera.init(self.interface):
            print("摄像头初始化失败")
            return False
        return camera.start_stream(width, height)
    
    def get_video_frame(self):
        """
        便利方法：获取最新视频帧
        
        Returns:
            numpy.ndarray: 图像数据
        """
        if self.camera is None:
            print("视频流未启动，请先调用 start_video_stream()")
            return None
        return self.camera.get_latest_frame()
    
    def stop_video_stream(self):
        """便利方法：停止视频流"""
        if self.camera:
            self.camera.stop_stream()
    
    def cleanup(self):
        """清理资源，停止所有连接和线程"""
        if not self._initialized:
            return
            
        print("正在清理Go2资源...")
        
        # 停止移动线程
        self._moving = False
        if (hasattr(self, '_move_thread') and 
            self._move_thread is not None and 
            self._move_thread.is_alive()):
            self._move_thread.join(timeout=1.0)
            self._move_thread = None
        
        # 清理摄像头资源
        if self.camera is not None:
            try:
                self.camera.cleanup()
                self.camera = None
            except:
                pass
        
        # 释放视频流
        if self.cap is not None:
            try:
                self.cap.release()
                self.cap = None
            except:
                pass
        
        # 清理DDS连接
        try:
            from unitree_sdk2py.core.channel import ChannelFactoryRelease
            ChannelFactoryRelease()
        except:
            pass
        
        self._initialized = False
        print("Go2资源清理完成")
    
    def __del__(self):
        """析构函数，自动清理资源"""
        try:
            self.cleanup()
        except:
            pass




# -------------------- 测试 --------------------
if __name__ == "__main__":
    interface = "enx00e0986113a6"  # 替换为你的Go2网卡接口名称
    
    go2 = Go2(interface=interface)

    go2.stand_down()
    go2.stand_up()
