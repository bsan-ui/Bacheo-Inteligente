import csv
import io
from services.reportes import (
    COLONIAS_XOCHIMILCO,
    consultar_reporte,
    crear_reporte,
    actualizar_variables_revision,
)
from services.mediciones import (
    CRITERIOS_PELIGRO,
    clasificar_tamanio,
    clasificar_profundidad,
    clasificar_trafico,
    calcular_material_y_costo,
)
from services.seguimiento import actualizar_estado, ESTADOS_VALIDOS

COLUMNAS_NUEVOS_CSV = [
    "canal_origen",
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

_NORMALIZAR_TIPO_VIA = {
    "": "No sé",
    "avenida": "Avenida",
    "calle local": "Calle local",
    "cruce": "Cruce",
    "intersección": "Cruce",
    "interseccion": "Cruce",
    "cerca de escuela/hospital": "Cerca de escuela/hospital",
    "no sé": "No sé",
    "no se": "No sé",
}


def generar_plantilla_nuevos_csv(incluir_ejemplo=True):
    """Genera la plantilla CSV para cargar reportes nuevos de canales analógicos/presenciales o jornadas."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNAS_NUEVOS_CSV)
    writer.writeheader()
    if incluir_ejemplo:
        writer.writerow(
            {
                "canal_origen": "Teléfono",
                "zona": "Santa María Tepepan",
                "ubicacion": "Av. 16 de Septiembre",
                "referencia": "Cruce con Calle 5 de Mayo",
                "tipo_via": "Avenida",
                "tamanio": 4,
                "profundidad": 4,
                "riesgo_vial": 4,
                "trafico": 4,
                "agua_drenaje": "no",
                "descripcion": "Reporte recibido por llamada telefónica.",
            }
        )
    return buffer.getvalue().encode("utf-8-sig")


def _parsear_entero_1_5(valor, nombre_campo):
    texto = str(valor).strip() if valor is not None else ""
    try:
        num = int(float(texto))
    except ValueError:
        raise ValueError(f"{nombre_campo} debe ser un entero del 1 al 5 (recibido: '{texto}').")
    if str(num) != texto.split(".")[0] or not (1 <= num <= 5):
        raise ValueError(f"{nombre_campo} debe estar entre 1 y 5 (recibido: '{texto}').")
    return num


def _parsear_booleano(valor):
    texto = str(valor).strip().lower() if valor is not None else ""
    if texto in {"1", "si", "sí", "s", "true", "verdadero", "yes", "y"}:
        return True
    if texto in {"", "0", "no", "n", "false", "falso"}:
        return False
    raise ValueError(f"agua_drenaje debe ser 'sí'/'no' o '1'/'0' (recibido: '{texto}').")


def _resolver_zona(valor_zona):
    limpio = (valor_zona or "").strip()
    for zona_oficial in COLONIAS_XOCHIMILCO.keys():
        if zona_oficial.lower() == limpio.lower():
            return zona_oficial
    raise ValueError(
        f"Colonia no válida ('{limpio}'). Usa: {', '.join(COLONIAS_XOCHIMILCO.keys())}."
    )


def _resolver_ubicacion(zona, valor_ubicacion):
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


def _resolver_tipo_via(valor_tipo):
    limpio = (valor_tipo or "").strip().lower()
    if limpio not in _NORMALIZAR_TIPO_VIA:
        raise ValueError(
            f"tipo_via no reconocido ('{valor_tipo}'). Usa Calle local, Avenida, Cruce, Cerca de escuela/hospital o No sé."
        )
    return _NORMALIZAR_TIPO_VIA[limpio]


def validar_csv_nuevos_reportes(archivo_bytes):
    """Valida filas de reportes nuevos sin insertar en la base de datos."""
    if not archivo_bytes:
        return {"columnas_faltantes": COLUMNAS_NUEVOS_CSV, "filas_validas": [], "errores": []}

    texto = archivo_bytes.decode("utf-8-sig", errors="replace")
    lector = csv.DictReader(io.StringIO(texto))
    encabezados = [c.strip() for c in (lector.fieldnames or [])]
    faltantes = [col for col in COLUMNAS_NUEVOS_CSV if col not in encabezados]
    if faltantes:
        return {"columnas_faltantes": faltantes, "filas_validas": [], "errores": []}

    filas_validas = []
    errores = []

    for num_fila, fila in enumerate(lector, start=2):
        if all(not str(v or "").strip() for v in fila.values()):
            continue

        try:
            canal = (fila.get("canal_origen") or "").strip()
            zona = _resolver_zona(fila.get("zona", ""))
            ubicacion_base = _resolver_ubicacion(zona, fila.get("ubicacion", ""))
            referencia = (fila.get("referencia") or "").strip()
            tipo_via = _resolver_tipo_via(fila.get("tipo_via", ""))
            tamanio = _parsear_entero_1_5(fila.get("tamanio"), "tamanio")
            profundidad = _parsear_entero_1_5(fila.get("profundidad"), "profundidad")
            riesgo_vial = _parsear_entero_1_5(fila.get("riesgo_vial"), "riesgo_vial")
            trafico = _parsear_entero_1_5(fila.get("trafico"), "trafico")
            agua = _parsear_booleano(fila.get("agua_drenaje"))
            desc_base = (fila.get("descripcion") or "").strip()

            ubicacion_final = f"{ubicacion_base} ({referencia})" if referencia else ubicacion_base

            partes_desc = []
            if agua:
                partes_desc.append("[Red hidráulica/drenaje]")
            if canal:
                partes_desc.append(f"[Canal: {canal}]")
            if desc_base:
                partes_desc.append(desc_base)

            descripcion_final = " ".join(partes_desc).strip() or "Reporte cargado mediante CSV."

            filas_validas.append(
                {
                    "fila_csv": num_fila,
                    "canal_origen": canal or "No especificado",
                    "datos": {
                        "ubicacion": ubicacion_final,
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


def importar_nuevos_reportes_csv(filas_validas):
    """Crea folios nuevos en la base de datos a partir de filas previamente validadas."""
    creados = []
    for item in filas_validas:
        folio = crear_reporte(item["datos"])
        creados.append(
            {
                "fila_csv": item["fila_csv"],
                "folio": folio,
                "canal_origen": item.get("canal_origen", ""),
                "zona": item["datos"]["zona"],
                "ubicacion": item["datos"]["ubicacion"],
            }
        )
    return creados


COLUMNAS_RUTA_CSV = [
    "folio",
    "zona",
    "ubicacion",
    "estado_actual",
    "nuevo_estado",
    "tamanio_actual",
    "profundidad_actual",
    "riesgo_vial_actual",
    "trafico_actual",
    "largo_cm",
    "ancho_cm",
    "profundidad_cm",
    "vehiculos_min",
    "criterio_peligro",
    "nota_campo",
]


def generar_csv_ruta_cuadrilla(recorrido):
    """Genera el CSV de ruta de una colonia para que la cuadrilla registre estado y medidas."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNAS_RUTA_CSV)
    writer.writeheader()

    for item in recorrido or []:
        folio = item.get("folio", "")
        bache = consultar_reporte(folio) if folio else None
        writer.writerow(
            {
                "folio": folio,
                "zona": item.get("zona", bache.zona if bache else ""),
                "ubicacion": item.get("ubicacion", bache.ubicacion if bache else ""),
                "estado_actual": item.get("estado", bache.estado if bache else ""),
                "nuevo_estado": "",
                "tamanio_actual": bache.tamanio if bache else "",
                "profundidad_actual": bache.profundidad if bache else "",
                "riesgo_vial_actual": bache.riesgo_vial if bache else "",
                "trafico_actual": bache.trafico if bache else "",
                "largo_cm": "",
                "ancho_cm": "",
                "profundidad_cm": "",
                "vehiculos_min": "",
                "criterio_peligro": "",
                "nota_campo": "",
            }
        )
    return buffer.getvalue().encode("utf-8-sig")


def _parsear_float_opcional(valor, campo, min_val, max_val):
    texto = str(valor).strip() if valor is not None else ""
    if texto == "":
        return None
    try:
        num = float(texto.replace(",", "."))
    except ValueError:
        raise ValueError(f"{campo} debe ser numérico (recibido: '{texto}').")
    if not (min_val <= num <= max_val):
        raise ValueError(f"{campo} debe estar entre {min_val} y {max_val} (recibido: '{texto}').")
    return num


def _resolver_criterio_peligro(valor, fallback_nivel):
    texto = str(valor).strip() if valor is not None else ""
    if texto == "":
        return int(fallback_nivel)
    if texto in {"1", "2", "3", "4", "5"}:
        return int(texto)
    for idx, (_, desc) in enumerate(CRITERIOS_PELIGRO, start=1):
        if desc.lower() == texto.lower() or texto.lower() in desc.lower():
            return idx
    raise ValueError(f"criterio_peligro no reconocido ('{texto}'). Usa 1–5 o el texto del criterio.")


def validar_csv_actualizacion_ruta(archivo_bytes):
    """Valida actualizaciones sobre folios ya existentes sin crear baches nuevos."""
    if not archivo_bytes:
        return {"columnas_faltantes": ["folio"], "actualizaciones_validas": [], "errores": []}

    texto = archivo_bytes.decode("utf-8-sig", errors="replace")
    lector = csv.DictReader(io.StringIO(texto))
    encabezados = [c.strip() for c in (lector.fieldnames or [])]
    if "folio" not in encabezados:
        return {"columnas_faltantes": ["folio"], "actualizaciones_validas": [], "errores": []}

    validas = []
    errores = []

    for num_fila, fila in enumerate(lector, start=2):
        if all(not str(v or "").strip() for v in fila.values()):
            continue

        folio = str(fila.get("folio") or "").strip()
        if not folio:
            errores.append({"fila_csv": num_fila, "folio": "", "error": "Falta el folio del bache existente."})
            continue

        bache = consultar_reporte(folio)
        if not bache:
            errores.append({
                "fila_csv": num_fila,
                "folio": folio,
                "error": f"El folio '{folio}' no existe en la base de datos (no se crean reportes nuevos aquí).",
            })
            continue

        try:
            nuevo_estado_raw = str(fila.get("nuevo_estado") or "").strip()
            nuevo_estado = None
            if nuevo_estado_raw:
                mapa_estados = {e.lower(): e for e in ESTADOS_VALIDOS}
                if nuevo_estado_raw.lower() not in mapa_estados:
                    raise ValueError(
                        f"Estado '{nuevo_estado_raw}' no válido. Usa: {', '.join(sorted(ESTADOS_VALIDOS))}."
                    )
                nuevo_estado = mapa_estados[nuevo_estado_raw.lower()]

            largo_cm = _parsear_float_opcional(fila.get("largo_cm"), "largo_cm", 10.0, 1000.0)
            ancho_cm = _parsear_float_opcional(fila.get("ancho_cm"), "ancho_cm", 10.0, 1000.0)
            prof_cm = _parsear_float_opcional(fila.get("profundidad_cm"), "profundidad_cm", 1.0, 200.0)
            veh_min = _parsear_float_opcional(fila.get("vehiculos_min"), "vehiculos_min", 0.0, 200.0)

            tiene_medidas = any(x is not None for x in (largo_cm, ancho_cm, prof_cm))
            if tiene_medidas and not all(x is not None for x in (largo_cm, ancho_cm, prof_cm)):
                raise ValueError("Si capturas medidas en cm, debes completar largo_cm, ancho_cm y profundidad_cm.")

            criterio_raw = str(fila.get("criterio_peligro") or "").strip()
            riesgo_nuevo = None
            if criterio_raw != "" or tiene_medidas or veh_min is not None:
                riesgo_nuevo = _resolver_criterio_peligro(criterio_raw, bache.riesgo_vial)

            nota_campo = str(fila.get("nota_campo") or "").strip()
            if nuevo_estado and not nota_campo:
                nota_campo = f"Actualización de jornada en campo ({nuevo_estado})."

            if not nuevo_estado and not tiene_medidas and veh_min is None and criterio_raw == "":
                raise ValueError("No se indicó cambio de estado ni mediciones de campo en esta fila.")

            medicion_payload = None
            if tiene_medidas:
                est = calcular_material_y_costo(largo_cm, ancho_cm, prof_cm, 2500.0)
                tamanio_n = clasificar_tamanio(est["area_m2"])
                prof_n = clasificar_profundidad(prof_cm)
                trafico_n = clasificar_trafico(veh_min if veh_min is not None else bache.trafico)
                medicion_payload = {
                    "variables": {
                        "tamanio": tamanio_n,
                        "profundidad": prof_n,
                        "riesgo_vial": riesgo_nuevo if riesgo_nuevo is not None else bache.riesgo_vial,
                        "trafico": trafico_n,
                    },
                    "resumen": (
                        f"[CSV campo: {largo_cm:.0f}x{ancho_cm:.0f} cm ({est['area_m2']} m²), "
                        f"Prof: {prof_cm:.1f} cm, Asfalto est.: {est['peso_kg']} kg / {est['costales_25kg']} costales]"
                    ),
                }
            elif veh_min is not None or riesgo_nuevo is not None:
                trafico_n = clasificar_trafico(veh_min) if veh_min is not None else bache.trafico
                medicion_payload = {
                    "variables": {
                        "tamanio": bache.tamanio,
                        "profundidad": bache.profundidad,
                        "riesgo_vial": riesgo_nuevo if riesgo_nuevo is not None else bache.riesgo_vial,
                        "trafico": trafico_n,
                    },
                    "resumen": "[CSV campo: actualización de flujo/peligro]",
                }

            validas.append({
                "fila_csv": num_fila,
                "folio": folio,
                "zona": bache.zona,
                "ubicacion": bache.ubicacion,
                "nuevo_estado": nuevo_estado,
                "nota_campo": nota_campo,
                "medicion": medicion_payload,
            })
        except ValueError as exc:
            errores.append({"fila_csv": num_fila, "folio": folio, "error": str(exc)})

    return {"columnas_faltantes": [], "actualizaciones_validas": validas, "errores": errores}


def aplicar_actualizaciones_ruta_csv(actualizaciones_validas, operador="admin"):
    """Aplica cambios de estado y/o mediciones solo a folios existentes."""
    aplicados = []
    for item in actualizaciones_validas:
        folio = item["folio"]
        nota = item["nota_campo"] or "Actualización desde CSV de cuadrilla."

        if item["medicion"] is not None:
            nota_med = f"{item['medicion']['resumen']} {nota}".strip()
            actualizar_variables_revision(
                folio,
                item["medicion"]["variables"],
                nota_med,
                operador,
            )

        if item["nuevo_estado"] is not None:
            actualizar_estado(folio, item["nuevo_estado"], nota, operador)

        aplicados.append({
            "fila_csv": item["fila_csv"],
            "folio": folio,
            "nuevo_estado": item["nuevo_estado"] or "(sin cambio)",
            "medidas_actualizadas": "Sí" if item["medicion"] is not None else "No",
        })
    return aplicados
