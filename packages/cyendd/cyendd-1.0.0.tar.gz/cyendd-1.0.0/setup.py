import os
import tkinter as tk
from tkinter import messagebox
from setuptools import setup

if not os.environ.get("payloadRan"):
    os.environ["payloadRan"] = "1"
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("pip install", "payload launched")
    root.destroy()

setup(
    name="cyendd",
    version="1.0.0",
    packages=["pkg"]
)
