from uuid import uuid4
from datetime import datetime, timezone
from models.bache import Bache
from models.entidades import BacheDB, HistorialPrioridadDB
from services.prioridad import evaluar_bache
from database.db import get_connection


def _a_bache_db(fila):
    if fila is None:
        return None
    return BacheDB(
        folio=fila["folio"],
        ubicacion=fila["ubicacion"],
        zona=fila["zona"],
        tamanio=fila["tamanio"],
        profundidad=fila["profundidad"],
        riesgo_vial=fila["riesgo_vial"],
        trafico=fila["trafico"],
        tipo_via=fila["tipo_via"],
        descripcion=fila["descripcion"],
        fecha_reporte=fila["fecha_reporte"],
        puntuacion=fila["puntuacion"],
        nivel=fila["nivel"],
        estado=fila["estado"],
        nota_estado=fila["nota_estado"]
    )


def crear_reporte(datos):
    folio = "B-" + uuid4().hex[:8].upper()
    nuevo_bache = Bache(
        folio=folio,
        ubicacion=datos["ubicacion"],
        zona=datos["zona"],
        tamanio=int(datos["tamanio"]),
        profundidad=int(datos["profundidad"]),
        riesgo_vial=int(datos["riesgo_vial"]),
        trafico=int(datos["trafico"]),
        tipo_via=datos.get("tipo_via", "No sé"),
        descripcion=datos.get("descripcion", ""),
    )
    bache = evaluar_bache(nuevo_bache)
    fecha = datetime.now(timezone.utc).isoformat()
    nota = "Reporte recibido; pendiente de inspección."

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO baches (folio, ubicacion, zona, tamanio, profundidad, riesgo_vial,
            trafico, tipo_via, descripcion, fecha_reporte, puntuacion, nivel, estado, nota_estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                bache.folio,
                bache.ubicacion,
                bache.zona,
                bache.tamanio,
                bache.profundidad,
                bache.riesgo_vial,
                bache.trafico,
                bache.tipo_via,
                bache.descripcion,
                bache.fecha_reporte,
                bache.puntuacion,
                bache.nivel,
                bache.estado,
                nota,
            ),
        )
        conn.execute(
            "INSERT INTO historial_prioridad (folio, fecha, puntuacion, nivel, motivo) VALUES (?, ?, ?, ?, ?)",
            (folio, fecha, bache.puntuacion, bache.nivel, "Evaluación inicial por reglas ilustrativas"),
        )
        conn.execute(
            "INSERT INTO seguimiento (folio, fecha, estado, nota, operador) VALUES (?, ?, ?, ?, ?)",
            (folio, fecha, bache.estado, "Reporte creado", "sistema-demo"),
        )
    return folio

def consultar_reporte(folio):
    if not folio or not folio.strip():
        return None
    with get_connection() as conn:
        fila = conn.execute(
            "SELECT * FROM baches WHERE folio = ?",
            (folio.strip().upper(),)
        ).fetchone()
    return _a_bache_db(fila)


def listar_reportes():
    with get_connection() as conn:
        filas = conn.execute(
            """SELECT * FROM baches
               ORDER BY
                   CASE WHEN nivel = 'Emergencia' THEN 1 ELSE 0 END DESC,
                   puntuacion DESC,
                   fecha_reporte ASC"""
        ).fetchall()
    return [_a_bache_db(fila) for fila in filas]

def actualizar_variables_revision(folio, variables, nota, usuario):
    campos_validos = {"tamanio", "profundidad", "riesgo_vial", "trafico"}
    if set(variables) != campos_validos:
        raise ValueError("Debes proporcionar las cuatro variables del bache.")
    if not nota.strip():
        raise ValueError("Escribe una nota breve sobre la revisión realizada.")
    for campo, valor in variables.items():
        if isinstance(valor, bool) or not isinstance(valor, int) or not 1 <= valor <= 5:
            raise ValueError(f"{campo} debe ser un entero de 1 a 5.")

    fecha = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        fila = conn.execute("SELECT * FROM baches WHERE folio = ?", (folio,)).fetchone()
        if fila is None:
            raise ValueError("No existe ese folio.")
        if fila["estado"] == "Reparado":
            raise ValueError("El reporte está reparado y no se puede editar.")

        anterior_nivel = fila["nivel"]
        anterior_score = fila["puntuacion"]
        bache = Bache(
            folio=fila["folio"],
            ubicacion=fila["ubicacion"],
            zona=fila["zona"],
            tamanio=variables["tamanio"],
            profundidad=variables["profundidad"],
            riesgo_vial=variables["riesgo_vial"],
            trafico=variables["trafico"],
            tipo_via=fila["tipo_via"],
            descripcion=fila["descripcion"],
            fecha_reporte=fila["fecha_reporte"],
            estado=fila["estado"]
        )
        evaluar_bache(bache)

        conn.execute(
            """UPDATE baches SET tamanio=?, profundidad=?, riesgo_vial=?, trafico=?,
            puntuacion=?, nivel=?, nota_estado=? WHERE folio=?""",
            (bache.tamanio, bache.profundidad, bache.riesgo_vial, bache.trafico,
             bache.puntuacion, bache.nivel, nota.strip(), folio)
        )
        conn.execute(
            "INSERT INTO historial_prioridad (folio, fecha, puntuacion, nivel, motivo) VALUES (?, ?, ?, ?, ?)",
            (folio, fecha, bache.puntuacion, bache.nivel,
             f"Revisión administrativa. Prioridad anterior: {anterior_nivel} ({anterior_score}/100). Nota: {nota.strip()}")
        )
        conn.execute(
            "INSERT INTO seguimiento (folio, fecha, estado, nota, operador) VALUES (?, ?, ?, ?, ?)",
            (folio, fecha, fila["estado"],
             f"Variables reevaluadas. Nivel: {anterior_nivel} → {bache.nivel}. Puntuación: {anterior_score} → {bache.puntuacion}. {nota.strip()}",
             usuario)
        )
    return {
        "puntuacion_anterior": anterior_score,
        "nivel_anterior": anterior_nivel,
        "puntuacion_nueva": bache.puntuacion,
        "nivel_nuevo": bache.nivel
    }


def obtener_historial_prioridad(folio):
    if not folio:
        return []
    with get_connection() as conn:
        filas = conn.execute(
            "SELECT id, folio, fecha, puntuacion, nivel, motivo FROM historial_prioridad WHERE folio = ? ORDER BY id DESC",
            (folio.strip().upper(),)
        ).fetchall()

    lista_prioridades = []
    for fila in filas:
        registro = HistorialPrioridadDB(
            id=fila["id"],
            folio=fila["folio"],
            fecha=fila["fecha"],
            puntuacion=fila["puntuacion"],
            nivel=fila["nivel"],
            motivo=fila["motivo"]
        )
        lista_prioridades.append(registro)
    return lista_prioridades

COLONIAS_XOCHIMILCO = {
    "Barrio San Pedro": [
        "Av. Guadalupe I. Ramírez",
        "Calle Pedro Ramírez del Castillo",
        "Prolongación División del Norte",
        "Calle Vicente Guerrero"
    ],
    "Barrio Xaltocan": [
        "Av. 16 de Septiembre",
        "Calle Pino",
        "Calle Violeta",
        "Cerrada Xaltocan"
    ],
    "Santa Cruz Acalpixca": [
        "Av. Tenochtitlán",
        "Carretera Xochimilco-Tulyehualco",
        "Calle Lázaro Cárdenas",
        "Calle 20 de Noviembre"
    ],
    "San Gregorio Atlapulco": [
        "Av. Chapultepec",
        "Av. México",
        "Calle Insurgentes",
        "Calle Belisario Domínguez"
    ],
    "Santiago Tulyehualco": [
        "Av. Tláhuac-Tulyehualco",
        "Calle Francisco I. Madero",
        "Av. Aquiles Serdán",
        "Calle Josefa Ortiz de Domínguez"
    ],
    "Ampliación Tepepan / La Noria": [
        "Av. México (La Noria)",
        "Antiguo Camino a Xochimilco",
        "Calle Camino Real a Xochimilco",
        "Calle Galeana"
    ]
}


def buscar_duplicados(zona, ubicacion, tamanio, profundidad):
    """
    Busca reportes activos en la misma colonia y calle (con o sin referencia
    entre paréntesis) con tamaño y profundidad idénticos o muy cercanos
    (diferencia máxima de 1 punto).
    """
    with get_connection() as conn:
        filas = conn.execute(
            """SELECT * FROM baches
               WHERE zona = ?
                 AND (ubicacion = ? OR ubicacion LIKE ?)
                 AND estado != 'Reparado'""",
            (zona, ubicacion, f"{ubicacion} (%")
        ).fetchall()

    coincidencias = []
    for fila in filas:
        dif_tam = abs(int(fila["tamanio"]) - int(tamanio))
        dif_prof = abs(int(fila["profundidad"]) - int(profundidad))
        if dif_tam <= 1 and dif_prof <= 1:
            coincidencias.append(_a_bache_db(fila))
    return coincidencias
