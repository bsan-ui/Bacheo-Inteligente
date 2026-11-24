import csv
import io
from services.reportes import COLONIAS_XOCHIMILCO, crear_reporte

COLUMNAS_CSV = [
    "zona",
    "ubicacion",
    "referencia",
    "tipo_via",
    "tamanio",
    "profundidad",
    "riesgo_vial",
    "trafico",
    "agua_drenaje",
    "descripcion",
]

TIPOS_VIA_VALIDOS = {
    "avenida",
    "calle local",
    "intersección",
    "interseccion",
    "cerca de escuela/hospital",
    "no sé",
    "no se",
}

_NORMALIZAR_TIPO_VIA = {
    "avenida": "Avenida",
    "calle local": "Calle local",
    "intersección": "Intersección",
    "interseccion": "Intersección",
    "cerca de escuela/hospital": "Cerca de escuela/hospital",
    "no sé": "No sé",
    "no se": "No sé",
}


def generar_plantilla_csv(incluir_ejemplo: bool = True) -> bytes:
    """Genera una plantilla CSV en UTF-8-SIG lista para abrir en Excel o Sheets."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNAS_CSV)
    writer.writeheader()
    if incluir_ejemplo:
        writer.writerow(
            {
                "zona": "Santa María Tepepan",
                "ubicacion": "Av. 16 de Septiembre",
                "referencia": "Cruce con Calle 5 de Mayo · Captura telefónica",
                "tipo_via": "Avenida",
                "tamanio": 4,
                "profundidad": 4,
                "riesgo_vial": 4,
                "trafico": 4,
                "agua_drenaje": "no",
                "descripcion": "Bache en carril de circulación detectado por atención telefónica.",
            }
        )
    return buffer.getvalue().encode("utf-8-sig")


def _parsear_entero_1_5(valor, nombre_campo: str) -> int:
    texto = str(valor).strip() if valor is not None else ""
    try:
        num = int(float(texto))
    except ValueError:
        raise ValueError(f"{nombre_campo} debe ser un número entero del 1 al 5 (recibido: '{texto}').")
    if str(num) != texto.split(".")[0] or not (1 <= num <= 5):
        raise ValueError(f"{nombre_campo} debe estar entre 1 y 5 (recibido: '{texto}').")
    return num


def _parsear_booleano(valor) -> bool:
    texto = str(valor).strip().lower() if valor is not None else ""
    if texto in {"1", "si", "sí", "s", "true", "verdadero", "yes", "y"}:
        return True
    if texto in {"", "0", "no", "n", "false", "falso"}:
        return False
    raise ValueError(f"agua_drenaje debe ser 'sí'/'no' o '1'/'0' (recibido: '{texto}').")


def _resolver_zona(valor_zona: str) -> str:
    limpio = (valor_zona or "").strip()
    for zona_oficial in COLONIAS_XOCHIMILCO.keys():
        if zona_oficial.lower() == limpio.lower():
            return zona_oficial
    raise ValueError(
        f"Colonia no válida ('{limpio}'). Usa una de las colonias verificadas: "
        f"{', '.join(COLONIAS_XOCHIMILCO.keys())}."
    )


def _resolver_ubicacion(zona: str, valor_ubicacion: str) -> str:
    limpio = (valor_ubicacion or "").strip()
    if not limpio:
        raise ValueError("La columna 'ubicacion' es obligatoria.")
    calles_zona = COLONIAS_XOCHIMILCO[zona]
    for calle in calles_zona:
        if calle.lower() == limpio.lower():
            return calle
    if limpio.lower().startswith("otra calle"):
        return "Otra calle (indicar en referencia)"
    raise ValueError(
        f"La calle '{limpio}' no figura en '{zona}'. Usa una calle confirmada de esa colonia "
        f"o escribe 'Otra calle (indicar en referencia)' y detalla la calle en 'referencia'."
    )


def _resolver_tipo_via(valor_tipo: str) -> str:
    limpio = (valor_tipo or "").strip().lower()
    if not limpio:
        return "No sé"
    if limpio not in _NORMALIZAR_TIPO_VIA:
        raise ValueError(
            f"tipo_via no reconocido ('{valor_tipo}'). Usa Avenida, Calle local, Intersección o Cerca de escuela/hospital."
        )
    return _NORMALIZAR_TIPO_VIA[limpio]


def validar_csv_reportes(archivo_bytes: bytes) -> dict:
    """Valida cada fila del CSV sin escribir en la base de datos."""
    if not archivo_bytes:
        return {"columnas_faltantes": COLUMNAS_CSV, "filas_validas": [], "errores": []}

    texto = archivo_bytes.decode("utf-8-sig", errors="replace")
    lector = csv.DictReader(io.StringIO(texto))
    encabezados = [c.strip() for c in (lector.fieldnames or [])]
    faltantes = [col for col in COLUMNAS_CSV if col not in encabezados]
    if faltantes:
        return {"columnas_faltantes": faltantes, "filas_validas": [], "errores": []}

    filas_validas = []
    errores = []

    for num_fila, fila in enumerate(lector, start=2):
        # Ignorar filas completamente vacías
        if all(not (str(v or "").strip()) for v in fila.values()):
            continue

        try:
            zona = _resolver_zona(fila.get("zona", ""))
            ubicacion = _resolver_ubicacion(zona, fila.get("ubicacion", ""))
            tipo_via = _resolver_tipo_via(fila.get("tipo_via", ""))
            tamanio = _parsear_entero_1_5(fila.get("tamanio"), "tamanio")
            profundidad = _parsear_entero_1_5(fila.get("profundidad"), "profundidad")
            riesgo_vial = _parsear_entero_1_5(fila.get("riesgo_vial"), "riesgo_vial")
            trafico = _parsear_entero_1_5(fila.get("trafico"), "trafico")
            agua = _parsear_booleano(fila.get("agua_drenaje"))

            referencia = (fila.get("referencia") or "").strip()
            descripcion_base = (fila.get("descripcion") or "").strip()

            partes_desc = []
            if agua:
                partes_desc.append("[Red hidráulica/drenaje]")
            if descripcion_base:
                partes_desc.append(descripcion_base)
            if referencia:
                partes_desc.append(f"Referencia: {referencia}")

            descripcion_final = " | ".join(partes_desc) if partes_desc else "Reporte cargado vía CSV."

            filas_validas.append(
                {
                    "fila_csv": num_fila,
                    "datos": {
                        "ubicacion": ubicacion,
                        "zona": zona,
                        "tamanio": tamanio,
                        "profundidad": profundidad,
                        "riesgo_vial": riesgo_vial,
                        "trafico": trafico,
                        "tipo_via": tipo_via,
                        "descripcion": descripcion_final,
                    },
                }
            )
        except ValueError as exc:
            errores.append({"fila_csv": num_fila, "error": str(exc)})

    return {"columnas_faltantes": [], "filas_validas": filas_validas, "errores": errores}


def importar_filas_validas(filas_validas: list[dict]) -> list[dict]:
    """Inserta en la base de datos solo las filas previamente validadas."""
    creados = []
    for item in filas_validas:
        folio = crear_reporte(item["datos"])
        creados.append(
            {
                "fila_csv": item["fila_csv"],
                "folio": folio,
                "zona": item["datos"]["zona"],
                "ubicacion": item["datos"]["ubicacion"],
            }
        )
    return creados
