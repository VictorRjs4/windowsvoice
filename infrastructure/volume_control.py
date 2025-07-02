"""
Gateway de volumen del sistema usando la librería PyCAW.
Si PyCAW o COM no están disponibles, los métodos quedan en `noop`.
"""

from __future__ import annotations
from domain.ports import VolumeGateway

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    _ENDPOINT = cast(
        AudioUtilities.GetSpeakers().Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None),
        POINTER(IAudioEndpointVolume)
    )
    _AUDIO_OK = True
except Exception:  # pragma: no cover
    _ENDPOINT = None
    _AUDIO_OK = False


class VolumeControl(VolumeGateway):
    def set_level(self, level: int) -> None:  # noqa: D401
        """Establece el volumen absoluto (0–100)."""
        if _AUDIO_OK:
            _ENDPOINT.SetMasterVolumeLevelScalar(max(0, min(level, 100)) / 100, None)

    def change(self, delta: float) -> None:  # noqa: D401
        """Variación relativa (-1.0 … 1.0)."""
        if _AUDIO_OK:
            cur = _ENDPOINT.GetMasterVolumeLevelScalar()
            _ENDPOINT.SetMasterVolumeLevelScalar(max(0, min(cur + delta, 1.0)), None)