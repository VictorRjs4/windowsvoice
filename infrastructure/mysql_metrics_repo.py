import os
import uuid
import logging
from datetime import datetime
import mysql.connector
from mysql.connector import Error

# Configuración por defecto (evita dependencias de archivos externos)
DEFAULT_DB_CONFIG = {
    "host": "bmhdjr7hholp07xngwhb-mysql.services.clever-cloud.com",
    "port": 3306,
    "database": "bmhdjr7hholp07xngwhb",
    "user": "u6pci7i5fefzib3l",
    "password": "FUb3gK8mS2ZeDclbFSFT"
}

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MySQLMetricsRepo:
    r"""
    Repositorio para guardar métricas en la tabla `task_metrics` del esquema `leya_metrics`.
    Cada instalación genera o lee un user_id local en %APPDATA%/LeyaApp/.user_id (Windows)
    o ~/.config/LeyaApp/.user_id (Linux/Mac).
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        generate_user_id: bool = True,
    ):
        # Cargar configuración por defecto si no se pasan parámetros
        if host is None:
            cfg = DEFAULT_DB_CONFIG
            host = cfg['host']
            port = cfg['port']
            database = cfg['database']
            user = cfg['user']
            password = cfg['password']

        # Generar o leer user_id local
        if generate_user_id:
            self.user_id = self._load_or_create_user_id()
        else:
            self.user_id = None

        # Conectar a MySQL deshabilitando SSL (para evitar errores en EXE)
        try:
            self.conn = mysql.connector.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                ssl_disabled=True,
                use_pure=True
            )
            self.conn.autocommit = True
            self.cursor = self.conn.cursor(dictionary=True)
            logging.info("[MySQLMetricsRepo] Conexión a MySQL establecida correctamente")
        except Error as e:
            logging.error(f"[MySQLMetricsRepo] Error al conectar: {repr(e)}")
            raise

    @classmethod
    def from_default_config(cls, **kwargs):
        """Crea una instancia usando la configuración por defecto."""
        return cls(**kwargs)

    def _load_or_create_user_id(self) -> str:
        r"""
        Guarda/lee un UUID en un archivo local para identificar siempre la misma instalación.
        En Windows: %APPDATA%\\LeyaApp\\.user_id
        En Linux/Mac: ~/.config/LeyaApp/.user_id
        """
        if os.name == "nt":
            base_folder = os.getenv("APPDATA", os.path.expanduser("~"))
        else:
            base_folder = os.path.expanduser("~/.config")
        app_folder = os.path.join(base_folder, "LeyaApp")
        os.makedirs(app_folder, exist_ok=True)

        user_id_file = os.path.join(app_folder, ".user_id")
        if os.path.isfile(user_id_file):
            with open(user_id_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        else:
            new_id = str(uuid.uuid4())
            with open(user_id_file, "w", encoding="utf-8") as f:
                f.write(new_id)
            return new_id

    def start_task(self, task_name: str) -> int | None:
        r"""
        Inserta un registro en `task_metrics` con user_id, task_name, start_time y step_count=0.
        Devuelve el id AUTO_INCREMENT (int) o None si falla.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = """
        INSERT INTO task_metrics (user_id, task_name, start_time, step_count)
        VALUES (%s, %s, %s, 0)
        """
        try:
            self.cursor.execute(sql, (self.user_id, task_name, now))
            return self.cursor.lastrowid
        except Error as e:
            print(f"[MySQLMetricsRepo] Error en start_task: {e}")
            return None

    def increment_step(self, task_id: int, pasos: int = 1) -> bool:
        r"""
        Incrementa `step_count` en `pasos` unidades para la fila id = task_id.
        Retorna True si se actualizó, False si hubo error.
        """
        sql = "UPDATE task_metrics SET step_count = step_count + %s WHERE id = %s"
        try:
            self.cursor.execute(sql, (pasos, task_id))
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[MySQLMetricsRepo] Error en increment_step: {e}")
            return False

    def end_task(self, task_id: int) -> bool:
        r"""
        Actualiza `end_time = NOW()` para la fila id=task_id si no tiene end_time.
        Retorna True si se actualizó, False si hubo error o ya estaba cerrado.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = "UPDATE task_metrics SET end_time = %s WHERE id = %s AND end_time IS NULL"
        try:
            self.cursor.execute(sql, (now, task_id))
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[MySQLMetricsRepo] Error en end_task: {e}")
            return False

    def get_all(self) -> list[dict]:
        r"""
        Devuelve todas las filas de `task_metrics` ordenadas por start_time DESC.
        """
        sql = "SELECT * FROM task_metrics ORDER BY start_time DESC"
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def close(self) -> None:
        r"""
        Cierra la conexión a MySQL.
        """
        if hasattr(self, "cursor") and self.cursor:
            self.cursor.close()
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
