"""
Definición de interfaces (puertos) que conectan la capa de Aplicación
con capas externas (UI e Infraestructura).  Ninguna implementación
concreta debe vivir aquí: solo contratos.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List


# ---------- puertos de entrada / salida de voz ------------------

class VoiceInputPort(ABC):
    """Micrófono → texto"""

    @abstractmethod
    def listen(self, timeout: int = 5) -> str:
        """Devuelve la frase capturada (en minúsculas) o '' si no detecta nada."""
        ...


class VoiceOutputPort(ABC):
    """Texto → altavoces"""

    @abstractmethod
    def speak(self, text: str) -> None:
        """Pronuncia el texto proporcionado."""
        ...


# ---------- gateways hacia el sistema / internet ----------------

class BrowserGateway(ABC):
    """Abrir URLs en el navegador."""

    @abstractmethod
    def open(self, url: str) -> None: ...
    @abstractmethod
    def open_blank(self) -> None:
        """Abre el navegador (pestaña en blanco) si aún no está abierto."""
        ...
    @abstractmethod
    def get_active_url(self) -> str:
        """Devuelve la URL de la pestaña activa (para crear comandos)."""
        ...

class ShortcutGateway(ABC):
    """Enviar atajos de teclado, scroll y otras acciones de ventana."""

    @abstractmethod
    def hotkey(self, keys: List[str]) -> None: ...

    @abstractmethod
    def scroll(self, amount: int) -> None: ...

    # ── acciones adicionales utilizadas por CommandDispatcher ──
    @abstractmethod
    def screenshot(self) -> None: ...
    @abstractmethod
    def fullscreen_video(self) -> None: ...
    @abstractmethod
    def exit_fullscreen(self) -> None: ...


class VolumeGateway(ABC):
    """Controlar volumen del sistema."""

    @abstractmethod
    def set_level(self, level: int) -> None:
        """Fija el volumen (0-100)."""
        ...

    @abstractmethod
    def change(self, delta: float) -> None:
        """Incrementa o decrementa (-1.0 … 1.0)."""
        ...


# ---------- repositorio de comandos personalizados --------------

class CommandRepository(ABC):
    """CRUD de comandos 'abrir X' guardados por el usuario."""

    @abstractmethod
    def list_commands(self) -> List[str]: ...

    @abstractmethod
    def add(self, name: str, url: str) -> None: ...

    @abstractmethod
    def get_url(self, name: str) -> str | None: ...