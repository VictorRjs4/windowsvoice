# ui/main.py

import sys
import os
from PyQt5.QtWidgets import QApplication
from config_loader import load_db_config
from front import MainGUI

def main() -> None:
    try:
        db_config = load_db_config()
    except Exception as e:
        print(f"Error al cargar config.json: {e}")
        sys.exit(1)

    app = QApplication(sys.argv)
    win = MainGUI(db_config=db_config)
    win.show()
    ret = app.exec_()
    sys.exit(ret)

if __name__ == "__main__":
    main()