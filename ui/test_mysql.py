# test_mysql.py

import json
import os
import mysql.connector
from mysql.connector import Error

def load_db_config() -> dict:
    base_dir = os.path.dirname(__file__)
    cfg_path = os.path.join(base_dir, "config.json")
    if not os.path.isfile(cfg_path):
        raise FileNotFoundError(f"No se encontró config.json en {cfg_path}")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)

def prueba_conexion():
    cfg = load_db_config()
    try:
        conn = mysql.connector.connect(
            host=cfg["host"],
            port=cfg["port"],
            database=cfg["database"],
            user=cfg["user"],
            password=cfg["password"]
        )
        if conn.is_connected():
            print("✅ Conexión exitosa a MySQL local:")
            print(f"   Host:     {cfg['host']}:{cfg['port']}")
            print(f"   Base:     {cfg['database']}")
            print(f"   Usuario:  {cfg['user']}")
            conn.close()
        else:
            print("❌ No se pudo conectar (conn.is_connected() == False)")
    except Error as e:
        print(f"❌ Error al conectar: {e}")

if __name__ == "__main__":
    prueba_conexion()