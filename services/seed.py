from services.reportes import crear_reporte, listar_reportes


def seed_demo():
    if listar_reportes():
        return

    ejemplos = [
        dict(
            ubicacion="Av. 16 de Septiembre",
            zona="Santa María Tepepan",
            tamanio=5,
            profundidad=5,
            riesgo_vial=5,
            trafico=4,
            tipo_via="Avenida",
            descripcion="[Red hidráulica/drenaje] Hundimiento profundo junto a coladera con acumulación de agua en carril de alto tránsito."
        ),
        dict(
            ubicacion="Calle Cuauhtémoc",
            zona="Santa María Tepepan",
            tamanio=4,
            profundidad=4,
            riesgo_vial=4,
            trafico=5,
            tipo_via="Avenida",
            descripcion="Bache amplio en zona de alta concentración de reportes cerca del cruce con Av. 16 de Septiembre."
        ),
        dict(
            ubicacion="Calz. Guadalupe I. Ramírez",
            zona="San Juan Tepepan",
            tamanio=3,
            profundidad=3,
            riesgo_vial=3,
            trafico=3,
            tipo_via="Avenida",
            descripcion="Desgaste moderado sobre el carril lateral que obliga a frenar a vehículos y transporte público."
        ),
        dict(
            ubicacion="Calle Rincón Sur",
            zona="Bosque Residencial del Sur",
            tamanio=2,
            profundidad=2,
            riesgo_vial=2,
            trafico=2,
            tipo_via="Calle local",
            descripcion="Grieta superficial en vialidad residencial con tránsito ligero."
        ),
    ]

    for datos in ejemplos:
        crear_reporte(datos)
