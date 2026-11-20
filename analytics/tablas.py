import pandas as pd
from services.reportes import listar_reportes

COLUMNAS = [
    "folio",
    "ubicacion",
    "zona",
    "tamanio",
    "profundidad",
    "riesgo_vial",
    "trafico",
    "tipo_via",
    "fecha_reporte",
    "puntuacion",
    "nivel",
    "estado",
    "nota_estado",
]

ORDEN_NIVEL = {
    "Emergencia": 0,
    "Prioridad alta": 1,
    "Prioridad media": 2,
    "Prioridad baja": 3,
    "En revisión": 4,
}


def _a_dataframe(reportes):
    """Convierte una lista de objetos en un DataFrame ordenado por severidad."""
    filas = []
    for r in reportes:
        if r is None:
            continue
        filas.append({
            "folio": r.folio,
            "ubicacion": r.ubicacion,
            "zona": r.zona,
            "tamanio": r.tamanio,
            "profundidad": r.profundidad,
            "riesgo_vial": r.riesgo_vial,
            "trafico": r.trafico,
            "tipo_via": r.tipo_via,
            "fecha_reporte": r.fecha_reporte,
            "puntuacion": r.puntuacion,
            "nivel": r.nivel,
            "estado": r.estado,
            "nota_estado": r.nota_estado,
        })

    df = pd.DataFrame(filas, columns=COLUMNAS)
    if df.empty:
        return df

    df["_orden_nivel"] = df["nivel"].map(ORDEN_NIVEL).fillna(99)
    df = df.sort_values(
        by=["_orden_nivel", "puntuacion", "fecha_reporte"],
        ascending=[True, False, True],
    ).drop(columns="_orden_nivel")
    return df.reset_index(drop=True)


def cargar_baches():
    """Devuelve un DataFrame con los reportes activos (aún no reparados)."""
    pendientes = []
    for r in listar_reportes():
        if r is not None and r.estado != "Reparado":
            pendientes.append(r)
    return _a_dataframe(pendientes)


def cargar_reparados():
    """Devuelve un DataFrame con los reportes ya marcados como reparados."""
    reparados = []
    for r in listar_reportes():
        if r is not None and r.estado == "Reparado":
            reparados.append(r)
    return _a_dataframe(reparados)


def resumen_estados():
    """Agrupa y cuenta los reportes activos por nivel de prioridad y estado."""
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
