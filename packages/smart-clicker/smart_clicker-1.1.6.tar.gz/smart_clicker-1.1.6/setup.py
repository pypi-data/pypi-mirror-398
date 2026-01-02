from setuptools import setup, find_packages

setup(
    name="smart_clicker",
    version="1.1.6", 
    author_email="183732521@qq.com",
    packages=find_packages(),
    install_requires=[
        "pyautogui",
        "opencv-python",
        "keyboard",
        "pillow"
    ],
    author="jiaobenxiaozi",
    description="A simple screen automation tool with hotkey snapshot capability.淘宝:阳阳软件市场",
)