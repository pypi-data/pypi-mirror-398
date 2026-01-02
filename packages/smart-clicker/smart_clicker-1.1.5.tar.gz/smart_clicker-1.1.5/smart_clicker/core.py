import time
import os
import threading
import glob
import keyboard
import pyautogui
from pyautogui import ImageNotFoundException
from .snipper import take_snapshot

class AutoBot:
    def __init__(self):
        self.img_dir = None
        self.running = False
        self.stop_event = threading.Event()
        self.confidence = 0.8
        
        # 快捷键配置
        self.hk_snapshot = 'f2'
        self.hk_toggle = 'f4'

    def init(self, img_dir, snapshot_key='f2', toggle_key='f4', confidence=0.8):
        self.img_dir = img_dir
        self.hk_snapshot = snapshot_key
        self.hk_toggle = toggle_key
        self.confidence = confidence
        
        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)
        return self

    def _toggle_automation(self):
        self.running = not self.running
        status = "🟢 运行中" if self.running else "🔴 已暂停"
        print(f"\n{status} | 正在监控目录: {self.img_dir}")

    def _trigger_snapshot(self):
        was_running = self.running
        self.running = False # 截图时强制暂停识别，防止干扰
        
        print("\n📸 屏幕已定格，请框选目标区域...")
        # 这里的 take_snapshot 现在会冻结屏幕
        take_snapshot(self.img_dir)
        
        if was_running:
            self.running = True
            print("▶️ 继续扫描...")

    def _scan_and_click(self):
        # 获取目录下所有png图片
        # 使用 glob 匹配路径下所有 png
        pattern = os.path.join(self.img_dir, "*.png")
        images = glob.glob(pattern)
        
        if not images:
            return

        # 遍历每张图片
        for img_path in images:
            if not self.running: break # 如果中途停止
            
            try:
                # 尝试寻找
                location = pyautogui.locateCenterOnScreen(
                    img_path,
                    confidence=self.confidence,
                    grayscale=True
                )
                
                if location:
                    filename = os.path.basename(img_path)
                    print(f"⚡ 识别到 [{filename}] -> 点击 {location}")
                    pyautogui.click(location)
                    
                    # 找到一个后，是继续找下一个，还是休息一下？
                    # 建议休息一下，防止鼠标抢夺太快
                    time.sleep(0.5) 
                    
            except ImageNotFoundException:
                continue # 当前图片没找到，找下一张
            except Exception as e:
                print(f"⚠️ 读取图片出错 {img_path}: {e}")

    def _loop_logic(self):
        print(f"🤖 系统就绪 | 截图[{self.hk_snapshot}] | 开关[{self.hk_toggle}]")
        
        while not self.stop_event.is_set():
            if self.running:
                self._scan_and_click()
            
            # 每一轮扫描后的间隔，防止CPU占用过高
            time.sleep(0.5)

    def start(self):
        if not self.img_dir:
            raise ValueError("未初始化目录")

        keyboard.add_hotkey(self.hk_snapshot, self._trigger_snapshot)
        keyboard.add_hotkey(self.hk_toggle, self._toggle_automation)

        self.worker_thread = threading.Thread(target=self._loop_logic, daemon=True)
        self.worker_thread.start()

        try:
            keyboard.wait()
        except KeyboardInterrupt:
            print("\n👋 退出程序")
            self.stop_event.set()