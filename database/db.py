import sqlite3
from pathlib import Path

DB_PATH = Path("baches.db")

def get_connection():
    """Abre una conexión SQLite con claves foráneas activadas."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Crea las tablas necesarias si aún no existen."""
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS baches (
            folio TEXT PRIMARY KEY,
            ubicacion TEXT NOT NULL,
            zona TEXT NOT NULL,
            tamano INTEGER NOT NULL CHECK(tamano BETWEEN 1 AND 5),
            profundidad INTEGER NOT NULL CHECK(profundidad BETWEEN 1 AND 5),
            riesgo_vial INTEGER NOT NULL CHECK(riesgo_vial BETWEEN 1 AND 5),
            trafico INTEGER NOT NULL CHECK(trafico BETWEEN 1 AND 5),
            tipo_via TEXT NOT NULL DEFAULT 'No sé',
            descripcion TEXT NOT NULL DEFAULT '',
            fecha_reporte TEXT NOT NULL,
            puntuacion REAL NOT NULL,
            nivel TEXT NOT NULL,
            estado TEXT NOT NULL,
            nota_estado TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS seguimiento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio TEXT NOT NULL REFERENCES baches(folio),
            fecha TEXT NOT NULL,
            estado TEXT NOT NULL,
            nota TEXT NOT NULL DEFAULT '',
            operador TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS historial_prioridad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio TEXT NOT NULL REFERENCES baches(folio),
            fecha TEXT NOT NULL,
            puntuacion REAL NOT NULL,
            nivel TEXT NOT NULL,
            motivo TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_baches_estado ON baches(estado);
        CREATE INDEX IF NOT EXISTS idx_seguimiento_folio ON seguimiento(folio);
        CREATE INDEX IF NOT EXISTS idx_prioridad_folio ON historial_prioridad(folio);
        """)
