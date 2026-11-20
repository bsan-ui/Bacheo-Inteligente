import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # Carga variables desde el archivo .env en tu computadora

DB_PATH = Path("baches.db")


def _obtener_database_url():
    """Busca DATABASE_URL en variables de entorno (.env) o en Streamlit Secrets."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        try:
            import streamlit as st
            url = st.secrets.get("DATABASE_URL", "").strip()
        except Exception:
            url = ""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class ConexionPostgres:
    """Adaptador sencillo para usar PostgreSQL con la misma sintaxis que sqlite3."""
    def __init__(self, url):
        import psycopg2
        from psycopg2.extras import RealDictCursor
        self.conn = psycopg2.connect(url, sslmode="require", cursor_factory=RealDictCursor)

    def execute(self, sql, params=()):
        # Convierte los marcadores '?' de SQLite al formato '%s' de PostgreSQL
        sql_pg = sql.replace("?", "%s")
        cursor = self.conn.cursor()
        cursor.execute(sql_pg, params)
        return cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()


def get_connection():
    """Devuelve conexión a PostgreSQL (Render) si hay URL configurada, o a SQLite local."""
    db_url = _obtener_database_url()
    if db_url:
        return ConexionPostgres(db_url)

    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Crea las tres tablas e índices en PostgreSQL o SQLite si aún no existen."""
    db_url = _obtener_database_url()
    tipo_id = "SERIAL PRIMARY KEY" if db_url else "INTEGER PRIMARY KEY AUTOINCREMENT"

    sentencias = [
        """
        CREATE TABLE IF NOT EXISTS baches (
            folio TEXT PRIMARY KEY,
            ubicacion TEXT NOT NULL,
            zona TEXT NOT NULL,
            tamanio INTEGER NOT NULL CHECK(tamanio BETWEEN 1 AND 5),
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
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS seguimiento (
            id {tipo_id},
            folio TEXT NOT NULL REFERENCES baches(folio),
            fecha TEXT NOT NULL,
            estado TEXT NOT NULL,
            nota TEXT NOT NULL DEFAULT '',
            operador TEXT NOT NULL
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS historial_prioridad (
            id {tipo_id},
            folio TEXT NOT NULL REFERENCES baches(folio),
            fecha TEXT NOT NULL,
            puntuacion REAL NOT NULL,
            nivel TEXT NOT NULL,
            motivo TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_baches_estado ON baches(estado)",
        "CREATE INDEX IF NOT EXISTS idx_seguimiento_folio ON seguimiento(folio)",
        "CREATE INDEX IF NOT EXISTS idx_prioridad_folio ON historial_prioridad(folio)"
    ]

    with get_connection() as conn:
        for sql in sentencias:
            conn.execute(sql)
