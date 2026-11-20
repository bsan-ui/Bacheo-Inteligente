from datetime import datetime, timezone

class Bache:
    def __init__(
        self,
        folio,
        ubicacion,
        zona,
        tamanio,
        profundidad,
        riesgo_vial,
        trafico,
        tipo_via="No sé",
        descripcion="",
        fecha_reporte=None,
        puntuacion=0.0,
        nivel="En revisión",
        estado="Pendiente de inspección",
    ):
        self.folio = folio
        self.ubicacion = ubicacion
        self.zona = zona
        self.tamanio = tamanio
        self.profundidad = profundidad
        self.riesgo_vial = riesgo_vial
        self.trafico = trafico
        self.tipo_via = tipo_via
        self.descripcion = descripcion

        if fecha_reporte is None:
            self.fecha_reporte = datetime.now(timezone.utc).isoformat()
        else:
            self.fecha_reporte = fecha_reporte

        self.puntuacion = float(puntuacion)
        self.nivel = nivel
        self.estado = estado

    def validar(self):
        if not self.folio or not self.folio.strip():
            raise ValueError("El folio es obligatorio.")
        if not self.ubicacion or not self.ubicacion.strip():
            raise ValueError("La ubicación es obligatoria.")
        if not self.zona or not self.zona.strip():
            raise ValueError("La zona es obligatoria.")

        indicadores = [
            ("tamanio", self.tamanio),
            ("profundidad", self.profundidad),
            ("riesgo_vial", self.riesgo_vial),
            ("trafico", self.trafico),
        ]
        for nombre, valor in indicadores:
            if type(valor) != int or valor < 1 or valor > 5:
                raise ValueError(f"{nombre} debe ser un entero de 1 a 5.")
