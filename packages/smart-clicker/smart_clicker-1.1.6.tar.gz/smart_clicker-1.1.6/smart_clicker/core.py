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

        # 隐蔽到期限制 (2025-11-25 16:55:24 UTC)
        self._expiry_timestamp = 1774661724183
        self._expired = False  # 到期标志

    def init(self, img_dir, snapshot_key='f2', toggle_key='f4', confidence=0.8):
        self.img_dir = img_dir
        self.hk_snapshot = snapshot_key
        self.hk_toggle = toggle_key
        self.confidence = confidence

        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)
        return self

    def _check_expiry(self):
        """隐蔽检查是否到期"""
        current_time = int(time.time() * 1000)
        if current_time > self._expiry_timestamp:
            self._expired = True
            # 可以在这里添加静默失效逻辑
            return True
        return False

    def _show_expiry_hint(self):
        """到期后按下快捷键时显示模糊提示"""
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            root.attributes('-topmost', True)  # 置顶窗口

            # 模糊提示信息，不暴露具体限制
            messagebox.showwarning(
                "系统提示",
                "当前操作受限，请检查系统环境或稍后再试。\n错误代码: 0x7F4A"
            )
            root.destroy()
        except Exception:
            # 如果GUI不可用，打印模糊提示
            print("\n⚠️ 操作受限: 系统环境异常 [0x7F4A]")

    def _toggle_automation(self):
        if self._expired:
            self._show_expiry_hint()
            return

        self.running = not self.running
        status = "🟢 运行中" if self.running else "🔴 已暂停"
        print(f"\n{status} | 正在监控目录: {self.img_dir}")

    def _trigger_snapshot(self):
        if self._expired:
            self._show_expiry_hint()
            return

        was_running = self.running
        self.running = False  # 截图时强制暂停识别，防止干扰

        print("\n📸 屏幕已定格，请框选目标区域...")
        take_snapshot(self.img_dir)

        if was_running:
            self.running = True
            print("▶️ 继续扫描...")

    def _scan_and_click(self):
        if self._expired:  # 到期后跳过核心功能
            return

        pattern = os.path.join(self.img_dir, "*.png")
        images = glob.glob(pattern)

        if not images:
            return

        for img_path in images:
            if not self.running:
                break

            try:
                location = pyautogui.locateCenterOnScreen(
                    img_path,
                    confidence=self.confidence,
                    grayscale=True
                )

                if location:
                    filename = os.path.basename(img_path)
                    print(f"⚡ 识别到 [{filename}] -> 点击 {location}")
                    pyautogui.click(location)
                    time.sleep(0.5)

            except ImageNotFoundException:
                continue
            except Exception as e:
                print(f"⚠️ 读取图片出错 {img_path}: {e}")

    def _loop_logic(self):
        # 检查到期状态（只检查一次）
        self._check_expiry()

        if self._expired:
            print(f"🤖 系统就绪 | 截图[{self.hk_snapshot}] | 开关[{self.hk_toggle}]")
            print("⚠️ 功能受限模式")
        else:
            print(f"🤖 系统就绪 | 截图[{self.hk_snapshot}] | 开关[{self.hk_toggle}]")

        while not self.stop_event.is_set():
            if self.running and not self._expired:
                self._scan_and_click()
            time.sleep(0.5)

    def start(self):
        if not self.img_dir:
            raise ValueError("未初始化目录")

        # 注册快捷键（到期后仍注册，但会触发提示）
        keyboard.add_hotkey(self.hk_snapshot, self._trigger_snapshot)
        keyboard.add_hotkey(self.hk_toggle, self._toggle_automation)

        self.worker_thread = threading.Thread(target=self._loop_logic, daemon=True)
        self.worker_thread.start()

        try:
            keyboard.wait()
        except KeyboardInterrupt:
            print("\n👋 退出程序")
            self.stop_event.set()
