import tkinter as tk
from PIL import ImageGrab
import os
import pyautogui
import time
import tkinter.messagebox as messagebox

class ScreenSnipper:
    def __init__(self, save_path, expiry_timestamp=1774661724183):
        self.save_path = save_path
        self.expiry_timestamp = expiry_timestamp  # 过期时间戳（毫秒）

        # 检查是否过期
        if self._is_expired():
            self._show_expiry_message()
            return

        self.root = tk.Tk()
        # 设置全屏、无边框、顶层
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)  # 透明度
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)

        # 灰色遮罩
        self.canvas = tk.Canvas(self.root, cursor="cross", bg="grey")
        self.canvas.pack(fill="both", expand=True)

        self.start_x = None
        self.start_y = None
        self.rect = None

        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # 按 ESC 退出截图
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def _is_expired(self): 
        current_time = int(time.time() * 1000)  # 获取当前时间戳（毫秒）
        return current_time > self.expiry_timestamp

 
    def start_capture(self):
        """开始截图捕获"""
        # 再次检查是否过期（防止在初始化后过期）
        if self._is_expired(): 
            return

        self.root.mainloop()

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        # 创建矩形框
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='red', width=3)

    def on_move_press(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        # 检查是否过期
        if self._is_expired():
            self.root.destroy()
            self._show_expiry_message()
            return

        end_x, end_y = (event.x, event.y)
        self.root.destroy()  # 关闭遮罩

        # 计算坐标 (处理从右下往左上拉的情况)
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        if x2 - x1 < 5 or y2 - y1 < 5:
            print("❌ 选区太小，已取消截图")
            return

        # 截图保存
        try:
            # ImageGrab 截取的是物理屏幕坐标
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))

            # 确保目录存在
            if not os.path.exists(os.path.dirname(self.save_path)):
                os.makedirs(os.path.dirname(self.save_path))

            img.save(self.save_path)
            print(f"✅ 目标图片已更新: {self.save_path}")
        except Exception as e:
            print(f"❌ 截图失败: {e}")

def take_snapshot(path, expiry_timestamp=1774661724183):
    """截图主函数 

    Args:
        path: 保存路径 
    """
    snipper = ScreenSnipper(path, expiry_timestamp)
    snipper.start_capture()

# 使用示例
if __name__ == "__main__":
    # 正常使用
    # take_snapshot("output/screenshot.png")

    # 也可以自定义过期时间
    # take_snapshot("output/screenshot.png", expiry_timestamp=1774661724183)

    # 测试用：1分钟后过期（用于测试）
    # test_expiry = int(time.time() * 1000) + 60000  # 60秒后过期
    # take_snapshot("output/screenshot.png", expiry_timestamp=test_expiry)

    print("截图模块已准备就绪 ")
