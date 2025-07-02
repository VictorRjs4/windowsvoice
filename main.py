# WINDOWSVOICE/windowsvoice/main.py

"""
main.py  (paquete windowsvoice)

• build(db_config) → AssistantService cableado con las credenciales MySQL
• Ejecución:
      python -m windowsvoice.main          # GUI PyQt5 (por defecto)
      python -m windowsvoice.main --cli    # sólo voz (CLI)
      python main.py                       # GUI, si estás dentro de la carpeta ui
      python main.py --cli                 # CLI desde ui
"""

from __future__ import annotations

# ── Si se ejecuta como script suelto (python main.py), añade la carpeta madre a sys.path ──
if __package__ is None:
    import pathlib, sys
    ROOT = pathlib.Path(__file__).resolve().parent   # …/windowsvoice
    sys.path.append(str(ROOT.parent))
    __package__ = ROOT.name                          # "windowsvoice"
# ──────────────────────────────────────────────────────────────────────────────────────

import sys

# ---- importaciones absolutas de nuestras capas ---------------------------------------

from application     import AssistantService
from ui              import VoiceInput, VoiceOutput
from infrastructure  import (
    Browser,
    SystemShortcuts,
    VolumeControl,
    SQLiteCommands,
)

# Necesitamos cargar config.json para CLI
from ui.config_loader import load_db_config


# ──────────────────────────────────────────────────────────────────────────────────────
def build(db_config: dict) -> AssistantService:
    """
    Construye el AssistantService, inyectando todos los puertos y el repositorio MySQL.
    El parámetro `db_config` es un diccionario con las credenciales MySQL, p.ej:
      {
        "host": "localhost",
        "port": 3306,
        "database": "leya_metrics",
        "user": "root",
        "password": "root"
      }
    """
    return AssistantService(
        voice_in   = VoiceInput(),
        voice_out  = VoiceOutput(),
        repo       = SQLiteCommands(),
        browser    = Browser(),
        shortcuts  = SystemShortcuts(),
        volume     = VolumeControl(),
        db_config  = db_config,
    )


def gui() -> None:
    """Lanza la interfaz PyQt5 (front-end)."""
    # La propia ui/front.py (o ui/main.py) se encargará de leer config.json y pasar db_config a MainGUI.
    from ui.front import main as gui_main
    gui_main()


def cli() -> None:
    """Modo sólo voz (CLI). Carga las credenciales desde config.json y arranca el run() directo."""
    # 1) Leemos config.json (ui/config.json) con load_db_config()
    db_cfg = load_db_config()

    # 2) Construimos el servicio usando esas credenciales y arrancamos el bucle CLI
    build(db_cfg).run()


# ──────────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Si se pasó "--cli" en la línea de comandos, ejecutamos en modo voz (CLI)
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        cli()
    else:
        # Por defecto, lanza la GUI (que internamente vuelve a leer config.json)
        gui()
