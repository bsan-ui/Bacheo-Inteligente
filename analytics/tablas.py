import pandas as pd
from services.reportes import listar_reportes

COLUMNAS = [
    "folio", "ubicacion", "zona", "tamano", "profundidad",
    "riesgo_vial", "trafico", "tipo_via", "fecha_reporte",
    "puntuacion", "nivel", "estado", "nota_estado"
]

# Los niveles se ordenan por severidad, no alfabéticamente.
ORDEN_NIVEL = {
    "Emergencia": 0,
    "Prioridad alta": 1,
    "Prioridad media": 2,
    "Prioridad baja": 3,
    "En revisión": 4,
}


def _a_dataframe(reportes):
    """Convierte objetos BacheDB en un DataFrame con columnas consistentes."""
    df = pd.DataFrame(
        [{col: getattr(reporte, col) for col in COLUMNAS} for reporte in reportes],
        columns=COLUMNAS,
    )
    if df.empty:
        return df

    df["_orden_nivel"] = df["nivel"].map(ORDEN_NIVEL).fillna(99)
    df = df.sort_values(
        by=["_orden_nivel", "puntuacion", "fecha_reporte"],
        ascending=[True, False, True],
    ).drop(columns="_orden_nivel")
    return df.reset_index(drop=True)


def cargar_baches():
    """DataFrame operativo: reportes que todavía no están reparados."""
    reportes = [r for r in listar_reportes() if r.estado != "Reparado"]
    return _a_dataframe(reportes)


def cargar_reparados():
    """DataFrame separado con reportes reparados; úsese solo en el panel admin."""
    reportes = [r for r in listar_reportes() if r.estado == "Reparado"]
    return _a_dataframe(reportes)


def resumen_estados():
    """Resume por nivel y estado únicamente los reportes aún no reparados."""
    df = cargar_baches()
    if df.empty:
        return pd.DataFrame(columns=["nivel", "estado", "cantidad"])
    
    resumen = (
        df.groupby(["nivel", "estado"])
        .size()
        .reset_index(name="cantidad")
    )
    resumen["_orden"] = resumen["nivel"].map(ORDEN_NIVEL).fillna(99)
    resumen = resumen.sort_values(["_orden", "estado"]).drop(columns="_orden")
    return resumen.reset_index(drop=True)