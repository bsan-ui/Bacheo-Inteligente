from datetime import datetime, timezone
from database.db import get_connection
from models.entidades import SeguimientoDB

ESTADOS_VALIDOS = {"Pendiente de inspección", "En evaluación", "Asignado", "En reparación", "Reparado"}

def actualizar_estado(folio, estado, nota, usuario):
    if estado not in ESTADOS_VALIDOS:
        raise ValueError("Estado no válido.")
    fecha = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        fila = conn.execute("SELECT folio FROM baches WHERE folio = ?", (folio,)).fetchone()
        if fila is None:
            raise ValueError("No existe ese folio.")
        conn.execute("UPDATE baches SET estado=?, nota_estado=? WHERE folio=?", (estado, nota, folio))
        conn.execute("INSERT INTO seguimiento (folio, fecha, estado, nota, operador) VALUES (?, ?, ?, ?, ?)",
                     (folio, fecha, estado, nota, usuario))

def obtener_historial(folio):
    with get_connection() as conn:
        filas = conn.execute(
            "SELECT * FROM seguimiento WHERE folio=? ORDER BY id DESC",
            (folio,)
        ).fetchall()
    
    historial = []
    for fila in filas:
        registro = SeguimientoDB(
            id=fila["id"],
            folio=fila["folio"],
            fecha=fila["fecha"],
            estado=fila["estado"],
            nota=fila["nota"],
            operador=fila["operador"]
        )
        historial.append(registro)
    return historial