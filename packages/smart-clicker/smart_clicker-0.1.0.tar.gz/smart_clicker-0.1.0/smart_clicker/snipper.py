import tkinter as tk
from PIL import ImageGrab
import os
import pyautogui

class ScreenSnipper:
    def __init__(self, save_path):
        self.save_path = save_path
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

    def start_capture(self):
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

def take_snapshot(path):
    snipper = ScreenSnipper(path)
    snipper.start_capture()