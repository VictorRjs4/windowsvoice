"""
Gateway para abrir URLs.  Se apoya en el módulo estándar `webbrowser`,
de modo que la decisión del navegador recae en el sistema operativo.
"""

# infrastructure/browser_gateway.py

from __future__ import annotations
import os
import subprocess
import logging
import webbrowser
import pyautogui
import time
import pyperclip
from typing import Final

from domain.ports import BrowserGateway

class Browser(BrowserGateway):
    _CHROME_PATHS: Final[list[str]] = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    def open(self, url: str) -> None:
        try:
            webbrowser.open(url)
        except Exception as e:
            logging.error(f"Browser.open: {e}")

    def open_blank(self) -> None:
        # Si Chrome ya corre, solo enfoca
        if self._is_running("chrome.exe"):
            self._focus_chrome()
            return

        # Si no, intenta arrancarlo
        for exe in self._CHROME_PATHS:
            if os.path.exists(exe):
                try:
                    subprocess.Popen([exe, "--start-maximized"])
                    return
                except Exception as e:
                    logging.error(f"Browser.open_blank: {e}")
        # Fallback
        try:
            webbrowser.open("about:blank")
        except Exception as e:
            logging.error(f"Browser.open_blank fallback: {e}")

    def get_active_url(self) -> str:
        try:
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.1)
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.1)
            return pyperclip.paste().strip()
        except Exception as e:
            logging.error(f"Browser.get_active_url: {e}")
            return ""

    def _is_running(self, proc_name: str) -> bool:
        try:
            out = subprocess.check_output("tasklist", shell=True).decode("cp1252", errors="ignore")
            return proc_name.lower() in out.lower()
        except Exception as e:
            logging.error(f"Browser._is_running: {e}")
            return False

    def _focus_chrome(self) -> None:
        try:
            subprocess.Popen([
                "powershell", "-Command",
                "(New-Object -ComObject Shell.Application).Windows()"
                " | Where-Object { $_.Name -like '*Chrome*' }"
                " | ForEach-Object { $_.Visible = $True }"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logging.error(f"Browser._focus_chrome: {e}")
