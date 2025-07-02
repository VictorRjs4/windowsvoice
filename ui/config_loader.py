# ui/config_loader.py

import json
import os

def load_db_config() -> dict:
    """
    Lee ui/config.json y devuelve un diccionario con las credenciales MySQL:
    {
  "host": "bmhdjr7hholp07xngwhb-mysql.services.clever-cloud.com",
  "port": 3306,
  "database": "bmhdjr7hholp07xngwhb",
  "user": "u6pci7i5fefzib3l",
  "password": "FUb3gK8mS2ZeDclbFSFT"
    }
    """
    base_dir = os.path.dirname(__file__)
    cfg_path = os.path.join(base_dir, "config.json")
    if not os.path.isfile(cfg_path):
        raise FileNotFoundError(f"No se encontró config.json en {cfg_path}")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)
