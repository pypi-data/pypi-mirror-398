import tkinter as tk
from PIL import ImageGrab, ImageTk
import os
import time

class ScreenSnipper:
    def __init__(self, save_dir):
        self.save_dir = save_dir
        self.root = tk.Tk()
        
        # 1. 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 2. 【核心】瞬间截取全屏，实现“视觉定格”
        # 这一步会让用户感觉屏幕被“冻住”了，方便截取动态视频中的按钮
        self.original_image = ImageGrab.grab(bbox=(0, 0, screen_width, screen_height))
        self.tk_image = ImageTk.PhotoImage(self.original_image)
        
        # 3. 设置全屏窗口
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        
        # 4. 创建画布并把“定格图”铺上去
        self.canvas = tk.Canvas(self.root, cursor="cross", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
        
        # 变量初始化
        self.start_x = None
        self.start_y = None
        self.rect = None

        # 绑定事件
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy()) # 按ESC取消

    def start_capture(self):
        self.root.mainloop()

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        # 画一个红色的框，由于背景是实图，不需要alpha，直接画空心矩形
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, 
            outline='red', width=2
        )

    def on_move_press(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        self.root.destroy()
        
        # 计算坐标
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        # 过滤误触
        if x2 - x1 < 10 or y2 - y1 < 10:
            return

        try:
            # 从刚才缓存的“定格图”中裁剪，而不是重新截图（避免截到红框）
            crop_img = self.original_image.crop((x1, y1, x2, y2))
            
            # 【核心】自动生成唯一文件名：target_时间戳.png
            timestamp = int(time.time() * 1000)
            filename = f"target_{timestamp}.png"
            full_path = os.path.join(self.save_dir, filename)
            
            if not os.path.exists(self.save_dir):
                os.makedirs(self.save_dir)
                
            crop_img.save(full_path)
            print(f"✅ 已添加新目标: {filename}")
        except Exception as e:
            print(f"❌ 保存失败: {e}")

def take_snapshot(save_dir):
    # 每次调用都实例化一个新的，确保截取当前最新屏幕
    snipper = ScreenSnipper(save_dir)
    snipper.start_capture()