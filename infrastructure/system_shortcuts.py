"""
Gateway para enviar atajos de teclado y scroll al sistema usando `pyautogui`.
"""

from __future__ import annotations
import os
import time
from pathlib import Path
from typing import List

import pyautogui                                   # type: ignore

from domain.ports import ShortcutGateway


class SystemShortcuts(ShortcutGateway):
    # ------------------------------------------------------------------
    # Métodos requeridos por el puerto
    # ------------------------------------------------------------------

    def hotkey(self, keys: List[str]) -> None:           # noqa: D401
        """Envía una combinación de teclas, por ejemplo ['ctrl', 't']."""
        pyautogui.hotkey(*keys, interval=0.05)

    def scroll(self, amount: int) -> None:               # noqa: D401
        """Desplaza verticalmente la rueda del ratón."""
        pyautogui.scroll(amount)

    # ------------------------------------------------------------------
    # Métodos adicionales usados por CommandDispatcher
    # ------------------------------------------------------------------

    def screenshot(self) -> None:
        """
        Captura la pantalla completa y la guarda en el Escritorio
        con nombre 'capture-YYYYMMDD-HHMMSS.png'.
        """
        ts   = time.strftime("%Y%m%d-%H%M%S")
        path = Path.home() / "Desktop" / f"capture-{ts}.png"
        pyautogui.screenshot(str(path))

    def fullscreen_video(self) -> None:
        """
        Intenta poner en pantalla completa el vídeo activo
        (asalto sencillo: clic centro + tecla 'f').
        """
        w, h = pyautogui.size()
        pyautogui.click(w / 2, h / 2)
        time.sleep(0.1)
        pyautogui.press("f")

    def exit_fullscreen(self) -> None:
        """Sale del modo pantalla completa (tecla Escape)."""
        pyautogui.press("esc")