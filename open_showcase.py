"""
open_showcase.py
Launches showcase.html directly in Google Chrome or Microsoft Edge,
bypassing Windows legacy file associations (such as disabled Internet Explorer).
"""

import os
import sys
import subprocess

workspace = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(workspace, "showcase.html")

if not os.path.exists(html_path):
    print(f"Error: {html_path} does not exist. Run 'python build_showcase.py' first.")
    sys.exit(1)

# Preferred modern browser executables
browsers = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

opened = False
for b in browsers:
    if os.path.exists(b):
        b_name = "Chrome" if "chrome" in b.lower() else "Edge"
        print(f"Launching showcase.html in Google {b_name}...")
        subprocess.Popen([b, html_path])
        print(f"SUCCESS: Opened {html_path}")
        opened = True
        break

if not opened:
    print("Launching via default Windows file handler...")
    os.startfile(html_path)
