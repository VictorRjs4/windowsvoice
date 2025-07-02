import logging
import pygame
import edge_tts
import asyncio
import os
import tempfile
from domain.ports import VoiceOutputPort

class VoiceOutput(VoiceOutputPort):
    def __init__(self):
        self.voice = "es-PY-TaniaNeural"

    def speak(self, text: str) -> None:
        if not text or not text.strip():
            logging.warning("Texto vacío, no se generará voz.")
            return

        logging.info(f"Leya dice: {text}")

        try:
            asyncio.run(self._generar_y_reproducir(text))
        except Exception as e:
            logging.error(f"[ERROR al sintetizar voz]: {e}")

    async def _generar_y_reproducir(self, text: str):
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            ruta_mp3 = tmp.name

        # Generar voz
        communicate = edge_tts.Communicate(text=text, voice=self.voice)
        await communicate.save(ruta_mp3)

        # Reproducir voz
        pygame.mixer.init()
        pygame.mixer.music.load(ruta_mp3)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        # ✅ Esperar y cerrar antes de eliminar
        pygame.mixer.music.unload()
        pygame.mixer.quit()
        os.remove(ruta_mp3)