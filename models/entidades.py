class BacheDB:
    def __init__(self, folio, ubicacion, zona, tamanio, profundidad,
                 riesgo_vial, trafico, tipo_via, descripcion,
                 fecha_reporte, puntuacion, nivel, estado, nota_estado):
        self.folio = folio
        self.ubicacion = ubicacion
        self.zona = zona
        self.tamanio = int(tamanio)
        self.profundidad = int(profundidad)
        self.riesgo_vial = int(riesgo_vial)
        self.trafico = int(trafico)
        self.tipo_via = tipo_via
        self.descripcion = descripcion
        self.fecha_reporte = fecha_reporte
        self.puntuacion = float(puntuacion)
        self.nivel = nivel
        self.estado = estado
        self.nota_estado = nota_estado


class SeguimientoDB:
    def __init__(self, id, folio, fecha, estado, nota, operador):
        self.id = int(id)
        self.folio = folio
        self.fecha = fecha
        self.estado = estado
        self.nota = nota
        self.operador = operador


class HistorialPrioridadDB:
    def __init__(self, id, folio, fecha, puntuacion, nivel, motivo):
        self.id = int(id)
        self.folio = folio
        self.fecha = fecha
        self.puntuacion = float(puntuacion)
        self.nivel = nivel
        self.motivo = motivo