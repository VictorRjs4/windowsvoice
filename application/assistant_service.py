# WINDOWSVOICE/application/assistant_service.py
"""
Loop principal: escucha, envía al dispatcher y registra métricas
(start_time, end_time, step_count).  El flujo “crear comando” se
mantiene aquí, tal cual pediste.
"""

from __future__ import annotations
import time, functools
from domain.ports import (
    VoiceInputPort, VoiceOutputPort, CommandRepository,
    BrowserGateway, ShortcutGateway, VolumeGateway,
)
from application.command_dispatcher import CommandDispatcher
from infrastructure.mysql_metrics_repo import MySQLMetricsRepo
from ui.config_loader import load_db_config


class AssistantService:
    # ---------------------------------------------------------------
    def __init__(
        self,
        voice_in : VoiceInputPort,
        voice_out: VoiceOutputPort,
        repo     : CommandRepository,
        browser  : BrowserGateway,
        shortcuts: ShortcutGateway,
        volume   : VolumeGateway,
        db_config: dict | None = None,
    ) -> None:

        # ---- dispatcher ------------------------------------------
        self.dispatcher = CommandDispatcher(
            repo      = repo,
            browser   = browser,
            shortcuts = shortcuts,
            volume    = volume,
            speaker   = voice_out,
        )

        # ---- métricas MySQL --------------------------------------
        if db_config is None:
            db_config = load_db_config()

        self.metrics_repo = MySQLMetricsRepo(**db_config)

        # dispatcher necesita saber el id de tarea para que los
        # wrappers puedan sumar pasos:
        self.dispatcher.metrics_repo   = self.metrics_repo
        self.dispatcher.current_cmd_id = None   # se irá actualizando

        # ---- referencias a gateways ------------------------------
        self.voice_in  = voice_in
        self.voice_out = voice_out
        self.repo      = repo
        self.browser   = browser
        self.shortcuts = shortcuts
        self.volume    = volume

        # ---- envolver métodos que representan “sub-pasos” --------
        self._wrap_gateway(self.browser,   ["open", "open_blank"])
        self._wrap_gateway(self.shortcuts, ["hotkey", "scroll",
                                            "screenshot",
                                            "fullscreen_video",
                                            "exit_fullscreen"])
        self._wrap_gateway(self.volume,    ["set_level", "change"])
        self._wrap_gateway(self.voice_out, ["speak"])

    # ---------------------------------------------------------------
    def run(self) -> None:
        self.voice_out.speak("Hola ,buen dia soy Leya, di !surge! para comenzar")

        while True:
            if "surge" not in self.voice_in.listen(timeout=10):
                continue

            self.voice_out.speak("¿En qué puedo ayudarte?")
            deadline = time.time() + 60                      # 1 min

            while time.time() < deadline:
                texto = self.voice_in.listen(timeout=5)
                if not texto or len(texto.strip()) < 3:
                    continue
                cmd_txt = texto.strip()

                # ---------- FLUJO “CREAR COMANDO” -----------------
                if "crear comando" in cmd_txt:
                    cid = self.metrics_repo.start_task("crear comando")
                    self.dispatcher.current_cmd_id = cid       # activar conteo
                    self._handle_create_command()              # acciones envueltas
                    if cid:
                        self.metrics_repo.end_task(cid)
                        self.dispatcher.current_cmd_id = None
                    deadline = time.time() + 60
                    continue

                # ---------- CUALQUIER OTRO COMANDO ---------------
                cid = self.metrics_repo.start_task(cmd_txt)
                self.dispatcher.current_cmd_id = cid
                keep = self.dispatcher.dispatch(cmd_txt)
                if cid:
                    self.metrics_repo.end_task(cid)
                    self.dispatcher.current_cmd_id = None
                if not keep:            # “adiós”
                    return
                deadline = time.time() + 60

    # ---------------------------------------------------------------
    def _handle_create_command(self) -> None:
        """Diálogo por voz para crear un comando personalizado."""
        self.voice_out.speak(
            "¿Quieres crear un comando para la página en la que te encuentras?"
        )
        if not any(w in self.voice_in.listen(timeout=10)
                   for w in ("sí", "si", "vale", "claro", "por supuesto")):
            self.voice_out.speak("Comando no creado")
            return

        self.voice_out.speak("¿Qué nombre le quieres poner?")
        name = self.voice_in.listen(timeout=10).strip()
        if not name:
            self.voice_out.speak("Nombre inválido, comando no creado")
            return

        url = self.browser.get_active_url()
        if not url:
            self.voice_out.speak("No pude obtener la URL, comando no creado")
            return

        self.repo.add(name, url)
        self.dispatcher.refresh()
        self.voice_out.speak(f"Comando '{name}' agregado correctamente")

    # ---------------------------------------------------------------
    def _wrap_gateway(self, gw, method_names: list[str]) -> None:
        """Añade wrapper que incrementa step_count en cada llamada."""
        for m in method_names:
            if not hasattr(gw, m):
                continue
            original = getattr(gw, m)

            @functools.wraps(original)
            def wrapped(*args, _orig=original, **kw):
                if self.dispatcher.current_cmd_id is not None:
                    self.metrics_repo.increment_step(self.dispatcher.current_cmd_id)
                return _orig(*args, **kw)

            setattr(gw, m, wrapped)
