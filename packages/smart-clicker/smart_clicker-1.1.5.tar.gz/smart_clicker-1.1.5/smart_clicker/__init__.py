from .core import AutoBot

# 为了方便用户直接使用，实例化一个默认对象，或者暴露类
_bot = AutoBot()

def init(img_dir, **kwargs):
    return _bot.init(img_dir, **kwargs)