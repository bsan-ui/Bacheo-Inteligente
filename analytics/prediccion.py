import math
import pandas as pd


def integrar_trapecio(funcion, a, b, n=100):
    """Calcula la integral definida de 'funcion' en [a, b] con n trapecios."""
    if b <= a:
        return 0.0
    base = (b - a) / float(n)
    suma_areas = 0.5 * (funcion(a) + funcion(b))
    for i in range(1, n):
        x_actual = a + i * base
        suma_areas += funcion(x_actual)
    return suma_areas * base


def probabilidad_nuevo_bache(profundidad, trafico, tiene_red_hidraulica=False, dias=30):
    """Integra la densidad exponencial f(x) = lambda * e^(-lambda * x) de 0 a 'dias'."""
    norm_prof = (profundidad - 1) / 4.0
    norm_traf = (trafico - 1) / 4.0
    extra_agua = 0.03 if tiene_red_hidraulica else 0.0

    tasa_lambda = 0.01 + (0.07 * norm_prof) + (0.05 * norm_traf) + extra_agua

    def densidad_exponencial(x):
        return tasa_lambda * math.exp(-tasa_lambda * x)

    area_integral = integrar_trapecio(densidad_exponencial, 0, dias, n=150)
    return round(area_integral * 100, 2)


def probabilidad_accidente_horario(tamanio, profundidad, riesgo_vial, trafico, hora_inicio=6, hora_fin=22):
    """Integra la función de riesgo horario entre hora_inicio y hora_fin."""
    severidad = (
        0.15 * ((tamanio - 1) / 4.0) +
        0.35 * ((profundidad - 1) / 4.0) +
        0.35 * ((riesgo_vial - 1) / 4.0) +
        0.15 * ((trafico - 1) / 4.0)
    )

    def riesgo_por_hora(t):
        pico_manana = math.exp(-0.5 * ((t - 8.0) / 1.5) ** 2)
        pico_tarde = math.exp(-0.5 * ((t - 19.0) / 2.0) ** 2)
        factor_trafico_hora = 0.2 + 0.8 * max(pico_manana, pico_tarde)
        return 0.018 * severidad * factor_trafico_hora

    integral_riesgo = integrar_trapecio(riesgo_por_hora, hora_inicio, hora_fin, n=100)
    probabilidad = 1.0 - math.exp(-integral_riesgo)
    return round(probabilidad * 100, 2)


def curva_riesgo_24h(tamanio, profundidad, riesgo_vial, trafico):
    """Genera un DataFrame hora por hora (0 a 24 h) para graficar el área bajo la curva."""
    severidad = (
        0.15 * ((tamanio - 1) / 4.0) +
        0.35 * ((profundidad - 1) / 4.0) +
        0.35 * ((riesgo_vial - 1) / 4.0) +
        0.15 * ((trafico - 1) / 4.0)
    )
    datos = []
    for hora in range(0, 25):
        pico_m = math.exp(-0.5 * ((hora - 8.0) / 1.5) ** 2)
        pico_t = math.exp(-0.5 * ((hora - 19.0) / 2.0) ** 2)
        tasa = 100 * (0.018 * severidad * (0.2 + 0.8 * max(pico_m, pico_t)))
        datos.append({"Hora del día": hora, "Índice de riesgo instantáneo f(t)": round(tasa, 2)})
    return pd.DataFrame(datos).set_index("Hora del día")