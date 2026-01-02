from setuptools import setup, find_packages

setup(
    name="smart_clicker",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyautogui",
        "opencv-python",
        "keyboard",
        "pillow"
    ],
    author="Your Name",
    description="A simple screen automation tool with hotkey snapshot capability.",
)