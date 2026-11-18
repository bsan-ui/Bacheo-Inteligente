PESOS = {"tamanio": 0.15, "profundidad": 0.30, "riesgo_vial": 0.35, "trafico": 0.20}


def evaluar_bache(bache):
    bache.validar()
    norm_tamanio = (bache.tamanio - 1) / 4.0
    norm_profundidad = (bache.profundidad - 1) / 4.0
    norm_riesgo = (bache.riesgo_vial - 1) / 4.0
    norm_trafico = (bache.trafico - 1) / 4.0

    score = 100.0 * (
        PESOS["tamanio"] * norm_tamanio +
        PESOS["profundidad"] * norm_profundidad +
        PESOS["riesgo_vial"] * norm_riesgo +
        PESOS["trafico"] * norm_trafico
    )

    
    if "[Red hidráulica/drenaje]" in bache.descripcion:
        score = min(100.0, score + 8.0)

    bache.puntuacion = round(score, 2)

    if (bache.profundidad >= 5 and bache.riesgo_vial >= 4) or bache.puntuacion >= 85:
        bache.nivel = "Emergencia"
    elif bache.puntuacion >= 70:
        bache.nivel = "Prioridad alta"
    elif bache.puntuacion >= 40:
        bache.nivel = "Prioridad media"
    else:
        bache.nivel = "Prioridad baja"
    return bache