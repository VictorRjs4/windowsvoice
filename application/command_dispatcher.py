# WINDOWSVOICE/application/command_dispatcher.py
from __future__ import annotations
import re
from difflib import get_close_matches
from typing import Callable, Dict, List, Optional, Tuple
import numpy as np
from nltk.stem import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer     # ← OK
from sklearn.metrics.pairwise import cosine_similarity      
from domain.ports import (
    BrowserGateway, ShortcutGateway, VolumeGateway,
    CommandRepository, VoiceOutputPort,
)
from infrastructure.mysql_metrics_repo import MySQLMetricsRepo


class CommandDispatcher:
    """Ejecuta la frase recibida usando los puertos; el conteo de pasos
    lo hacen los *wrappers* definidos en AssistantService."""

    # ---------------------------------------------------------------
    def __init__(
        self,
        repo: CommandRepository,
        browser: BrowserGateway,
        shortcuts: ShortcutGateway,
        volume: VolumeGateway,
        speaker: VoiceOutputPort,
    ) -> None:

        self.repo       = repo
        self.browser    = browser
        self.shortcuts  = shortcuts
        self.volume     = volume
        self.spk        = speaker

        # Se rellenan desde AssistantService
        self.metrics_repo  : Optional[MySQLMetricsRepo] = None
        self.current_cmd_id: int | None = None

        # --- catálogos de acciones ---------------------------------
        self.websites: Dict[str, str] = {
            "correo": "https://mail.google.com",
            "youtube": "https://www.youtube.com",
            "facebook": "https://www.facebook.com",
            "whatsapp": "https://web.whatsapp.com",
            "drive": "https://drive.google.com",
            "maps": "https://maps.google.com",
            "noticias": "https://news.google.com",
            "traductor": "https://translate.google.com",
        }
        self.direct_actions: Dict[str, Callable[[], None]] = {
            "abrir chrome":          self.browser.open_blank,
            "nueva pestaña":         lambda: self.shortcuts.hotkey(["ctrl", "t"]),
            "cerrar pestaña":        lambda: self.shortcuts.hotkey(["ctrl", "w"]),
            "reabrir pestaña":       lambda: self.shortcuts.hotkey(["ctrl","shift","t"]),
            "volver":                lambda: self.shortcuts.hotkey(["alt","left"]),
            "adelante":              lambda: self.shortcuts.hotkey(["alt","right"]),
            "recargar":              lambda: self.shortcuts.hotkey(["f5"]),
            "pantalla completa":     lambda: self.shortcuts.hotkey(["f11"]),
            "acercar pantalla":      lambda: self.shortcuts.hotkey(["ctrl","+"]),
            "alejar pantalla":       lambda: self.shortcuts.hotkey(["ctrl","-"]),
            "sube un poco":          lambda: self.shortcuts.scroll(300),
            "baja un poco":          lambda: self.shortcuts.scroll(-300),
            "captura de pantalla":   self.shortcuts.screenshot,
            "video pantalla completa": self.shortcuts.fullscreen_video,
            "cerrar pantalla completa": self.shortcuts.exit_fullscreen,
        }

        # --- NLP ----------------------------------------------------
        self._stem = SnowballStemmer("spanish")
        self._vectorizer = TfidfVectorizer(
            tokenizer=self._preprocess,
            token_pattern=None, 
            ngram_range=(1, 2)
        )
        self._pending_suggestion: str | None = None
        self._train_model()

    # ---------- NLP helpers ----------------------------------------
    def _preprocess(self, text: str) -> List[str]:
        return [self._stem.stem(t) for t in re.findall(r"\b\w+\b", text.lower())]

    def _base_corpus(self) -> List[str]:
        return (list(self.direct_actions.keys()) +
                [f"abrir {w}" for w in self.websites] +
                self.repo.list_commands())

    def _train_model(self) -> None:
        base = self._base_corpus() or ["dummy"]
        self._vectorizer.fit(base)
        self._mat      = self._vectorizer.transform(base)
        self._all_cmds = base

    def refresh(self) -> None: self._train_model()

    def _best_match(self, txt: str) -> Tuple[str | None, float]:
        sim = cosine_similarity(self._vectorizer.transform([txt]), self._mat)[0]
        idx = int(np.argmax(sim)); conf = float(max(sim))
        if conf > .5:  return self._all_cmds[idx], conf
        near = get_close_matches(txt, self._all_cmds, n=1, cutoff=.6)
        return (near[0], .6) if near else (None, .0)

    # ---------- API pública ----------------------------------------
    def dispatch(self, text: str) -> bool:
        """
        Ejecuta la frase `text`.
        El `AssistantService` ya cuenta automáticamente cada acción real,
        así que aquí **no** se llama a increment_step().
        """

        # “crear comando” se maneja en AssistantService
        if "crear comando" in text:
            return True

        # confirmación de sugerencia
        if text == "confirmo" and self._pending_suggestion:
            cmd = self._pending_suggestion
            self._pending_suggestion = None
            return self.dispatch(cmd)

        # salida
        if any(k in text for k in ("adiós", "apagar sistema", "cerrar sistema")):
            self.spk.speak("Hasta luego")
            return False

        # abrir sitios
        for name, url in self.websites.items():
            if f"abrir {name}" in text:
                self.browser.open(url)
                self.spk.speak(f"Abriendo {name}")
                return True

        # buscar en Google
        if m := re.search(r"\bbuscar\s+(.+)", text):
            q = m.group(1).strip()
            self.browser.open(f"https://www.google.com/search?q={q}")
            self.spk.speak(f"Buscando {q}")
            return True

        # acciones directas
        for key, fn in self.direct_actions.items():
            if key in text:
                fn()
                if key not in ("sube un poco", "baja un poco"):
                    self.spk.speak(key)
                return True

        # volumen
        if m := re.search(r"(?:sube|aumenta).*volumen a (\d+)", text):
            self.volume.set_level(int(m.group(1))); return True
        if m := re.search(r"(?:baja|disminuye).*volumen a (\d+)", text):
            self.volume.set_level(int(m.group(1))); return True
        if any(k in text for k in ("sube volumen", "más volumen")):
            self.volume.change(+0.05); return True
        if any(k in text for k in ("baja volumen", "menos volumen")):
            self.volume.change(-0.05); return True

        # comandos personalizados
        if url := self.repo.get_url(text):
            self.browser.open(url); self.spk.speak(f"Abriendo {text}")
            return True

        # play / pause video
        if "pausa el video" in text:
            self.shortcuts.hotkey(["space"]); self.spk.speak("Video en pausa"); return True
        if "reproduce el video" in text or "reproducir el video" in text:
            self.shortcuts.hotkey(["space"]); self.spk.speak("Reproduciendo video"); return True

        # sugerencia IA
        best, conf = self._best_match(text)
        if best and conf < .7:
            self.spk.speak(f"¿Quisiste decir {best}? Di confirmo")
            self._pending_suggestion = best
            return True
        if best:
            return self.dispatch(best)

        # sin coincidencias
        self.spk.speak("No entendí tu comando, puedes repetir por favor")
        return True