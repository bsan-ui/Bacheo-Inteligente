from services.reportes import crear_reporte, listar_reportes

def seed_demo():
    if listar_reportes():
        return
    ejemplos = [
        dict(
            ubicacion="Av. Guadalupe I. Ramírez",
            zona="Barrio San Pedro",
            tamanio=5, profundidad=5, riesgo_vial=5, trafico=4,
            tipo_via="Avenida",
            descripcion="[Red hidráulica/drenaje] Registro simulado cerca de coladera pluvial."
        ),
        dict(
            ubicacion="Carretera Xochimilco-Tulyehualco",
            zona="Santa Cruz Acalpixca",
            tamanio=4, profundidad=4, riesgo_vial=4, trafico=5,
            tipo_via="Avenida",
            descripcion="Registro simulado en vía primaria de Xochimilco."
        ),
        dict(
            ubicacion="Av. 16 de Septiembre",
            zona="Barrio Xaltocan",
            tamanio=3, profundidad=3, riesgo_vial=3, trafico=3,
            tipo_via="Cruce",
            descripcion="Registro simulado."
        ),
        dict(
            ubicacion="Calle Insurgentes",
            zona="San Gregorio Atlapulco",
            tamanio=2, profundidad=2, riesgo_vial=2, trafico=2,
            tipo_via="Calle local",
            descripcion="Registro simulado."
        ),
    ]
    for datos in ejemplos:
        crear_reporte(datos)