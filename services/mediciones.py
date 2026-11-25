import math

DENSIDAD_ASFALTO_KG_M3 = 2350.0
FACTOR_COMPACTACION = 1.15  # 15 % extra por compactación y merma en cajeo
PESO_COSTAL_KG = 25.0

COSTO_M2_MIN_MXN = 400.0
COSTO_M2_MAX_MXN = 500.0
COSTO_M2_REF_MXN = 450.0
VALOR_ESPERADO_CASO_MXN = 925.0  # 15% * $1,500 + 10% * $7,000
REFERENCIA_DANO_VEHICULAR_MXN = 7000.0

CRITERIOS_PELIGRO = [
    (1, "1 — Mínimo: en orilla o calle lenta (< 20 km/h), fácil de esquivar"),
    (2, "2 — Bajo: dentro del carril en calle lenta (20–30 km/h), visible a distancia"),
    (3, "3 — Moderado: en trayectoria de llantas (30–50 km/h), obliga a frenar o cambiar de carril"),
    (4, "4 — Alto: avenida rápida (> 50 km/h), curva, cruce escolar/hospitalario o bajo encharcamiento"),
    (5, "5 — Extremo: hundimiento inevitable en vía rápida, transporte público o ciclovía"),
]

# Valores iniciales de referencia para precargar el formulario según el reporte ciudadano (1–5)
VALORES_REFERENCIA_TAMANIO = {
    1: (30.0, 30.0),
    2: (60.0, 50.0),
    3: (100.0, 80.0),
    4: (140.0, 120.0),
    5: (200.0, 150.0),
}

VALORES_REFERENCIA_PROFUNDIDAD = {
    1: 2.0,
    2: 4.0,
    3: 8.0,
    4: 15.0,
    5: 25.0,
}

VALORES_REFERENCIA_TRAFICO = {
    1: 1,
    2: 4,
    3: 10,
    4: 22,
    5: 35,
}


def clasificar_tamanio(area_m2):
    """Convierte el área de cajeo (m²) a la escala 1–5."""
    if area_m2 < 0.15:
        return 1
    elif area_m2 <= 0.50:
        return 2
    elif area_m2 <= 1.20:
        return 3
    elif area_m2 <= 2.50:
        return 4
    else:
        return 5


def clasificar_profundidad(profundidad_cm):
    """Convierte la profundidad en centímetros a la escala 1–5."""
    if profundidad_cm < 3.0:
        return 1
    elif profundidad_cm <= 5.0:
        return 2
    elif profundidad_cm <= 10.0:
        return 3
    elif profundidad_cm <= 20.0:
        return 4
    else:
        return 5


def clasificar_trafico(vehiculos_por_minuto):
    """Convierte el conteo vehicular por minuto a la escala 1–5."""
    if vehiculos_por_minuto < 2:
        return 1
    elif vehiculos_por_minuto <= 5:
        return 2
    elif vehiculos_por_minuto <= 15:
        return 3
    elif vehiculos_por_minuto <= 30:
        return 4
    else:
        return 5


def calcular_material_y_costo(largo_cm, ancho_cm, profundidad_cm, costo_por_tonelada):
    """Calcula insumos asfálticos, estimación por m² (tabulador superficial) y referencia de riesgo."""
    area_m2 = (largo_cm / 100.0) * (ancho_cm / 100.0)
    volumen_m3 = area_m2 * (profundidad_cm / 100.0) * FACTOR_COMPACTACION
    peso_kg = volumen_m3 * DENSIDAD_ASFALTO_KG_M3
    toneladas = peso_kg / 1000.0
    costales_25kg = math.ceil(peso_kg / PESO_COSTAL_KG)
    costo_por_tonelada_calc = toneladas * costo_por_tonelada

    costo_superficial_min = area_m2 * COSTO_M2_MIN_MXN
    costo_superficial_max = area_m2 * COSTO_M2_MAX_MXN
    costo_superficial_ref = area_m2 * COSTO_M2_REF_MXN

    posible_dano_estructural = profundidad_cm >= 10.0

    return {
        "area_m2": round(area_m2, 2),
        "volumen_m3": round(volumen_m3, 4),
        "peso_kg": round(peso_kg, 1),
        "toneladas": round(toneladas, 3),
        "costales_25kg": costales_25kg,
        "costo_estimado": round(costo_por_tonelada_calc, 2),
        "costo_superficial_min": round(costo_superficial_min, 2),
        "costo_superficial_max": round(costo_superficial_max, 2),
        "costo_superficial_ref": round(costo_superficial_ref, 2),
        "posible_dano_estructural": posible_dano_estructural,
        "valor_esperado_caso": VALOR_ESPERADO_CASO_MXN,
        "referencia_dano_vehicular": REFERENCIA_DANO_VEHICULAR_MXN,
    }
