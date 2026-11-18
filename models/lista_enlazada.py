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
        """Recorre los nodos desde la cabeza hasta None y devuelve las paradas ordenadas."""
        paradas = []
        actual = self.cabeza
        numero_parada = 1
        while actual is not None:
            b = actual.bache
            siguiente_folio = actual.siguiente.bache.folio if actual.siguiente else "Fin de ruta (None)"
            paradas.append({
                "Parada": f"#{numero_parada}",
                "Folio actual": b.folio,
                "Calle (Ubicación)": b.ubicacion,
                "Colonia": b.zona,
                "Prioridad": f"{b.nivel} ({b.puntuacion}/100)",
                "Siguiente nodo (->)": siguiente_folio
            })
            actual = actual.siguiente
            numero_parada += 1
        return paradas