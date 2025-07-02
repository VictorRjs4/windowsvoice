"""
Micrófono → texto (implementa VoiceInputPort)
Depende únicamente de SpeechRecognition.
"""

from __future__ import annotations
import logging
import speech_recognition as sr
from domain.ports import VoiceInputPort


class VoiceInput(VoiceInputPort):
    def __init__(self) -> None:
        self._rec = sr.Recognizer()
        self._rec.pause_threshold = 1.0
        self._rec.energy_threshold = 300
        self._rec.dynamic_energy_threshold = True

    def listen(self, timeout: int = 5) -> str:  # noqa: D401
        """Devuelve la frase capturada o '' si no hay audio."""
        try:
            with sr.Microphone() as src:
                self._rec.adjust_for_ambient_noise(src, duration=0.5)
                audio = self._rec.listen(src, timeout=timeout, phrase_time_limit=5)
            return self._rec.recognize_google(audio, language="es-ES").lower()
        except sr.WaitTimeoutError:
            return ""
        except Exception as exc:  # pragma: no cover
            logging.error("VoiceInput error: %s", exc)
            return ""