from datetime import datetime

class Bache:
    def __init__(self, folio, ubicacion, zona, tamano, profundidad, riesgo_vial, trafico,
                 tipo_via="No sé", descripcion="", fecha_reporte=None,
                 puntuacion=0.0, nivel="En revisión", estado="Pendiente de inspección", nota_estado=""):
        self.folio = folio
        self.ubicacion = ubicacion
        self.zona = zona
        self.tamano = int(tamano)
        self.profundidad = int(profundidad)
        self.riesgo_vial = int(riesgo_vial)
        self.trafico = int(trafico)
        self.tipo_via = tipo_via
        self.descripcion = descripcion
        
        if fecha_reporte is None:
            self.fecha_reporte = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.fecha_reporte = fecha_reporte
            
        self.puntuacion = float(puntuacion)
        self.nivel = nivel
        self.estado = estado
        self.nota_estado = nota_estado

    def validar(self):
        if self.folio.strip() == "" or self.ubicacion.strip() == "" or self.zona.strip() == "":
            raise ValueError("El folio, la ubicación y la zona son obligatorios.")
        
        indicadores = [self.tamanio, self.profundidad, self.riesgo_vial, self.trafico]
        for valor in indicadores:
            if valor < 1 or valor > 5:
                raise ValueError("Todos los indicadores deben estar entre 1 y 5.")

    def calcular_prioridad(self):
        self.validar()
        # Normalización de escala 1-5 a escala 0-1: (valor - 1) / 4
        norm_tamanio = (self.tamanio - 1) / 4.0
        norm_profundidad = (self.profundidad - 1) / 4.0
        norm_riesgo = (self.riesgo_vial - 1) / 4.0
        norm_trafico = (self.trafico - 1) / 4.0

        # Suma ponderada explícita
        score = 100.0 * (
            0.15 * norm_tamanio +
            0.30 * norm_profundidad +
            0.35 * norm_riesgo +
            0.20 * norm_trafico
        )
        self.puntuacion = round(score, 2)

        if (self.profundidad >= 5 and self.riesgo_vial >= 4) or self.puntuacion >= 85:
            self.nivel = "Emergencia"
        elif self.puntuacion >= 70:
            self.nivel = "Prioridad alta"
        elif self.puntuacion >= 40:
            self.nivel = "Prioridad media"
        else:
            self.nivel = "Prioridad baja"
        return self