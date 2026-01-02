import time
import os
import threading
import keyboard
import pyautogui
from pyautogui import ImageNotFoundException
from .snipper import take_snapshot

class AutoBot:
    def __init__(self):
        self.img_dir = None
        self.target_name = "target.png"  # 默认图片名
        self.target_path = None
        self.running = False
        self.stop_event = threading.Event()
        self.worker_thread = None
        
        # 配置参数
        self.confidence = 0.8
        self.grayscale = True
        
        # 快捷键
        self.hk_snapshot = 'f2'    # 截图快捷键
        self.hk_toggle = 'f4'      # 开关快捷键

    def init(self, img_dir, target_filename="target.png", snapshot_key='f2', toggle_key='f4'):
        """初始化配置"""
        self.img_dir = img_dir
        self.target_name = target_filename
        self.target_path = os.path.join(self.img_dir, self.target_name)
        self.hk_snapshot = snapshot_key
        self.hk_toggle = toggle_key
        
        # 确保目录存在
        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)
            
        return self # 支持链式调用

    def _toggle_automation(self):
        """切换运行状态"""
        self.running = not self.running
        if self.running:
            print(f"\n🚀 自动化已启动! (目标: {self.target_name})")
            # 检查图片是否存在
            if not os.path.exists(self.target_path):
                print(f"⚠️ 警告: 未找到 {self.target_path}，请先按 {self.hk_snapshot} 截图！")
                self.running = False
        else:
            print("\n⏸️ 自动化已暂停")

    def _trigger_snapshot(self):
        """触发截图流程（需要暂停自动化以防冲突）"""
        was_running = self.running
        if was_running:
            self.running = False
            print("📸 暂停任务以进行截图...")
            
        print(">>> 请框选要识别的区域...")
        # 这里的截图需要在主线程或者完全独立的进程中调用，因为 tkinter 在子线程运行会有问题
        # 但 keyboard 的回调通常在一个独立的线程。
        # 这里为了简单，直接调用，若有 GUI 冲突需使用队列通信，但在纯脚本环境下通常可行。
        take_snapshot(self.target_path)
        
        if was_running:
            self.running = True
            print("▶️ 恢复任务")

    def _loop_logic(self):
        """后台循环查找线程"""
        print(f"🤖 服务已就绪 | 截图: [{self.hk_snapshot}] | 开关: [{self.hk_toggle}]")
        print("按 Ctrl+C 强制退出程序")
        
        while not self.stop_event.is_set():
            if self.running and os.path.exists(self.target_path):
                try:
                    location = pyautogui.locateCenterOnScreen(
                        self.target_path,
                        confidence=self.confidence,
                        grayscale=self.grayscale
                    )
                    
                    if location:
                        print(f"✨ 点击坐标: {location}")
                        pyautogui.click(location)
                        time.sleep(1) # 点击冷却
                        
                except ImageNotFoundException:
                    pass # 没找到是正常的，继续找
                except Exception as e:
                    print(f"❌ 错误: {e}")
            
            time.sleep(0.1) # 避免CPU占用过高

    def start(self):
        """启动监听和循环"""
        if not self.img_dir:
            raise ValueError("请先调用 init('path') 设置目录")

        # 注册热键
        keyboard.add_hotkey(self.hk_snapshot, self._trigger_snapshot)
        keyboard.add_hotkey(self.hk_toggle, self._toggle_automation)

        # 启动后台工作线程
        self.worker_thread = threading.Thread(target=self._loop_logic)
        self.worker_thread.daemon = True # 设置为守护线程，主程序退出时自动销毁
        self.worker_thread.start()

        # 阻塞主线程，保持程序运行，直到用户按 Ctrl+C
        try:
            keyboard.wait() 
        except KeyboardInterrupt:
            print("\n👋 程序退出")
            self.stop_event.set()