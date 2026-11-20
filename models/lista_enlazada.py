class NodoBache:
    def __init__(self, bache):
        self.bache = bache
        self.siguiente = None


class ListaEnlazadaRuta:
    """Lista simplemente enlazada para armar la ruta de reparación en una colonia."""
    def __init__(self):
        self.cabeza = None

    def esta_vacia(self):
        return self.cabeza is None

    def agregar_parada(self, bache):
        nuevo_nodo = NodoBache(bache)
        if self.cabeza is None:
            self.cabeza = nuevo_nodo
        else:
            actual = self.cabeza
            while actual.siguiente is not None:
                actual = actual.siguiente
            actual.siguiente = nuevo_nodo

    def obtener_recorrido(self):
        """Recorre los nodos desde la cabeza hasta el final y devuelve la ruta legible."""
        paradas = []
        actual = self.cabeza
        numero_parada = 1

        while actual is not None:
            b = actual.bache
            if actual.siguiente is not None:
                siguiente_destino = f"Continúa con {actual.siguiente.bache.folio} ({actual.siguiente.bache.ubicacion})"
            else:
                siguiente_destino = "Fin del recorrido"

            paradas.append({
                "Orden": f"Parada {numero_parada}",
                "Folio": b.folio,
                "Calle o avenida": b.ubicacion,
                "Colonia": b.zona,
                "Urgencia": f"{b.nivel} ({b.puntuacion}/100)",
                "Siguiente parada": siguiente_destino,
            })
            actual = actual.siguiente
            numero_parada += 1

        return paradas
