import altair as alt
import streamlit as st
import pandas as pd
from database.db import init_db
from services.seed import seed_demo
from services.reportes import (
    crear_reporte,
    consultar_reporte,
    listar_reportes,
    actualizar_variables_revision,
    obtener_historial_prioridad,
    buscar_duplicados,
    COLONIAS_XOCHIMILCO,
)
from services.mediciones import (
    CRITERIOS_PELIGRO,
    VALORES_REFERENCIA_TAMANIO,
    VALORES_REFERENCIA_PROFUNDIDAD,
    VALORES_REFERENCIA_TRAFICO,
    clasificar_tamanio,
    clasificar_profundidad,
    clasificar_trafico,
    calcular_material_y_costo,
)
from services.seguimiento import actualizar_estado, obtener_historial, ESTADOS_VALIDOS
from services.carga_csv import (
    generar_plantilla_csv,
    validar_csv_reportes,
    importar_filas_validas,
)
from analytics.tablas import cargar_baches, cargar_reparados, resumen_estados
from analytics.prediccion import (
    probabilidad_nuevo_bache,
    probabilidad_accidente_horario,
    curva_riesgo_24h,
)
from models.lista_enlazada import ListaEnlazadaRuta
from security.auth import verificar_admin


def mostrar_tabla_baches(df):
    nombres = {
        "folio": "Folio",
        "ubicacion": "Calle o avenida",
        "zona": "Colonia / Barrio",
        "tamanio": "Tamaño (1–5)",
        "profundidad": "Profundidad (1–5)",
        "riesgo_vial": "Peligro vial (1–5)",
        "trafico": "Tráfico (1–5)",
        "tipo_via": "Tipo de vialidad",
        "fecha_reporte": "Fecha de registro",
        "puntuacion": "Índice de urgencia (0–100)",
        "nivel": "Nivel de prioridad",
        "estado": "Estado actual",
        "nota_estado": "Última actualización",
    }
    st.dataframe(df.rename(columns=nombres), width='stretch', hide_index=True)


def mostrar_historial(historial):
    if not historial:
        st.info("Aún no hay movimientos registrados para este reporte.")
        return
    filas = []
    for h in historial:
        filas.append({
            "Fecha": h.fecha,
            "Estado": h.estado,
            "Observación": h.nota or "Sin comentarios",
            "Responsable": "Personal operativo" if h.operador and h.operador != "sistema-demo" else "Sistema",
        })
    st.dataframe(filas, width='stretch', hide_index=True)


def mostrar_historial_prioridad(historial_prioridad):
    if not historial_prioridad:
        st.info("Este reporte conserva su evaluación inicial sin modificaciones.")
        return
    filas = []
    for h in historial_prioridad:
        filas.append({
            "Fecha": h.fecha,
            "Índice de urgencia (0–100)": h.puntuacion,
            "Prioridad asignada": h.nivel,
            "Motivo de la actualización": h.motivo,
        })
    st.dataframe(filas, width='stretch', hide_index=True)


def mostrar_resumen_operativo():
    df_resumen = resumen_estados()
    if df_resumen.empty:
        return
    nombres_resumen = {
        "nivel": "Nivel de prioridad",
        "estado": "Estado actual",
        "cantidad": "Total de reportes",
    }
    st.dataframe(df_resumen.rename(columns=nombres_resumen), width='stretch', hide_index=True)


@st.cache_resource
def inicializar_sistema():
    init_db()
    seed_demo()
    return True


st.set_page_config(page_title="Baches Inteligentes — Xochimilco", page_icon="🕳️", layout="wide")
inicializar_sistema()

st.title("🕳️ Baches Inteligentes · Alcaldía Xochimilco")
st.caption("Plataforma de reporte ciudadano y priorización de mantenimiento vial · CDMX")

pagina = st.sidebar.radio("Navegación", ["Portal ciudadano", "Panel administrativo"])

if st.session_state.get("admin_ok", False):
    st.sidebar.divider()
    st.sidebar.caption(f"Sesión activa: **{st.session_state.get('admin_usuario', 'admin')}**")
    if st.sidebar.button("Cerrar sesión", key="logout_sidebar"):
        st.session_state.admin_ok = False
        st.session_state.admin_usuario = ""
        st.rerun()

if pagina == "Portal ciudadano":
    tab_crear, tab_consultar, tab_aviso = st.tabs(
        ["➕ Reportar un bache", "🔍 Consultar seguimiento y riesgo", "ℹ️ Acerca del sistema"]
    )
    with tab_crear:
        st.subheader("Registrar un nuevo reporte en Xochimilco")
        st.info("📍 **Demarcación:** Alcaldía Xochimilco. Selecciona la colonia o barrio para desplegar sus vialidades.")

        col_ubic1, col_ubic2 = st.columns(2)
        lista_colonias = list(COLONIAS_XOCHIMILCO.keys())
        zona = col_ubic1.selectbox("1. Colonia o barrio", lista_colonias)
        calles_disponibles = COLONIAS_XOCHIMILCO[zona]
        calle_seleccionada = col_ubic2.selectbox("2. Calle o avenida", calles_disponibles)

        referencia_extra = st.text_input(
            "3. Referencia cercana (opcional)",
            max_chars=100,
            placeholder="Ej. Frente a la escuela, esquina con cerrada o junto al puente"
        )

        st.markdown("**Evalúa las condiciones aproximadas del bache (1 = leve, 5 = crítico)**")
        with st.expander("📏 Guía rápida para estimar del 1 al 5"):
            st.markdown("""
            * **Tamaño:** 1 = hoja carta / plato (< 0.15 m²) · 2 = mochila (0.15–0.50 m²) · 3 = medio carril (0.51–1.20 m²) · 4 = casi un carril (1.21–2.50 m²) · 5 = tramo colapsado (> 2.50 m²).
            * **Profundidad:** 1 = desgaste superficial (< 3 cm) · 2 = alto de celular (3–5 cm) · 3 = alto de un puño (5–10 cm) · 4 = alto de un ladrillo (10–20 cm) · 5 = posible socavón (> 20 cm).
            * **Flujo vehicular:** 1 = cerrada vecinal (< 2 autos/min) · 2 = calle tranquila (2–5/min) · 3 = calle regular (6–15/min) · 4 = avenida con transporte (16–30/min) · 5 = vía principal saturada (> 30/min).
            * **Peligro vial:** 1 = en orilla, fácil de esquivar · 3 = obliga a frenar o invadir carril · 5 = hundimiento inevitable en vía rápida o ciclovía.
            """)

        col1, col2 = st.columns(2)
        tamanio = col1.slider(
            "Tamaño aproximado", 1, 5, 3,
            help="1: plato (<0.15 m²) · 2: mochila · 3: medio carril · 4: casi todo el carril · 5: tramo colapsado (>2.5 m²)"
        )
        profundidad = col2.slider(
            "Profundidad aproximada", 1, 5, 3,
            help="1: <3 cm · 2: 3–5 cm (un celular) · 3: 5–10 cm (un puño) · 4: 10–20 cm (un ladrillo) · 5: >20 cm (socavón)"
        )
        riesgo = col1.slider(
            "Peligro para vehículos y peatones", 1, 5, 3,
            help="1: en orilla y lento · 2: esquivable · 3: obliga a frenar · 4: vía rápida, curva o charco · 5: riesgo grave inevitable"
        )
        trafico = col2.slider(
            "Flujo vehicular en la zona", 1, 5, 3,
            help="1: <2 autos/min · 2: 2–5/min · 3: 6–15/min · 4: 16–30/min · 5: >30 autos/min"
        )

        tipo = st.selectbox("Entorno de la vialidad", ["Calle local", "Avenida", "Cruce", "Cerca de escuela/hospital", "No sé"])
        red_hidraulica = st.checkbox("💧 Hay una coladera, fuga de agua o registro de drenaje junto al bache")
        descripcion = st.text_area("Comentarios adicionales (evita incluir datos personales)", max_chars=600)

        with st.expander("📄 Consultar Aviso de Privacidad Simplificado y Manejo de Información"):
            st.markdown("""
            **AVISO DE PRIVACIDAD SIMPLIFICADO (PROTOTIPO ACADÉMICO · CDMX)**

            * **Responsables del tratamiento:** Equipo de investigación estudiantil del proyecto *"Baches Inteligentes — Alcaldía Xochimilco"* (Licenciatura en Ciencia de Datos, Ciudad de México).
            * **Datos recabados:** Exclusivamente información técnica y geográfica de infraestructura vial pública (colonia, calle o avenida, dimensiones estimadas del daño, flujo vehicular y presencia de red hidráulica). **Este sistema no recaba ni requiere datos personales identificables** (nombres, teléfonos, correos, placas o domicilios particulares), en apego al principio de minimización de datos de la legislación vigente en la Ciudad de México.
            * **Finalidad:** Los registros se utilizan únicamente con fines académicos, estadísticos, de modelado matemático y de demostración tecnológica en entorno universitario. No se transfieren a terceros ni tienen fines comerciales.
            * **Control y seguimiento:** Cada reporte genera un folio alfanumérico anónimo (`B-XXXXXXXX`) que permite consultar su estado o solicitar su baja de la base de demostración ante los autores del proyecto.
            """)

        confirmar_aviso = st.checkbox(
            "He leído el Aviso de Privacidad, comprendo el manejo académico de los datos y confirmo que mi reporte solo contiene información vial."
        )

        duplicados = buscar_duplicados(zona, calle_seleccionada, tamanio, profundidad)
        forzar_registro = False
        if duplicados:
            st.warning(
                f"⚠️ **Ya existe un reporte similar en esta calle:** Encontramos {len(duplicados)} reporte(s) activo(s) "
                f"en **{calle_seleccionada}** ({zona}) con dimensiones parecidas."
            )
            filas_dup = [{
                "Folio": d.folio,
                "Calle o avenida": d.ubicacion,
                "Tamaño": d.tamanio,
                "Profundidad": d.profundidad,
                "Prioridad": d.nivel,
                "Estado actual": d.estado
            } for d in duplicados]
            st.dataframe(filas_dup, width='stretch', hide_index=True)
            forzar_registro = st.checkbox(
                "Es un bache distinto en la misma calle y deseo generar un nuevo reporte."
            )

        if st.button("Registrar reporte", type="primary"):
            if not confirmar_aviso:
                st.error("Por favor marca la casilla de confirmación antes de enviar tu reporte.")
            elif duplicados and not forzar_registro:
                st.error("Ya hay un reporte similar registrado. Puedes darle seguimiento con ese folio o confirmar arriba si se trata de otro bache.")
            else:
                ubicacion_final = calle_seleccionada
                if referencia_extra.strip():
                    ubicacion_final = f"{calle_seleccionada} ({referencia_extra.strip()})"

                desc_final = descripcion.strip()
                if red_hidraulica:
                    desc_final = f"[Red hidráulica/drenaje] {desc_final}".strip()

                try:
                    folio = crear_reporte({
                        "ubicacion": ubicacion_final,
                        "zona": zona,
                        "tamanio": tamanio,
                        "profundidad": profundidad,
                        "riesgo_vial": riesgo,
                        "trafico": trafico,
                        "tipo_via": tipo,
                        "descripcion": desc_final,
                    })
                    st.success(f"¡Reporte registrado con éxito! Conserva tu número de folio para darle seguimiento: **{folio}**")
                    mostrar_tabla_baches(cargar_baches().head(10))
                except Exception as exc:
                    st.error(f"Ocurrió un problema al guardar el reporte: {exc}")

    with tab_consultar:
        st.subheader("Consulta el avance y análisis de riesgo de tu reporte")
        folio_consulta = st.text_input("Ingresa tu número de folio", placeholder="Ej. B-XXXXXXXX", key="folio_publico")
        if st.button("Consultar folio", key="btn_consultar"):
            bache = consultar_reporte(folio_consulta)
            if bache and bache.estado == "Reparado":
                st.success("✅ Este bache ya fue atendido y marcado como **Reparado**.")
            elif bache:
                st.write(f"**Ubicación:** {bache.ubicacion} · **Colonia:** {bache.zona}")
                tiene_agua = "[Red hidráulica/drenaje]" in bache.descripcion
                prob_bache = probabilidad_nuevo_bache(bache.profundidad, bache.trafico, tiene_agua, dias=30)
                prob_acc = probabilidad_accidente_horario(bache.tamanio, bache.profundidad, bache.riesgo_vial, bache.trafico, 6, 22)

                c_m1, c_m2, c_m3 = st.columns(3)
                c_m1.metric("Urgencia asignada", f"{bache.puntuacion}/100 ({bache.nivel})")
                c_m2.metric("Riesgo de expansión o nuevo bache (30 días)", f"{prob_bache} %")
                c_m3.metric("Probabilidad de incidente vial (6:00 a 22:00 h)", f"{prob_acc} %")

                st.markdown("**Comportamiento del riesgo vial a lo largo del día**")
                st.caption("El área sombreada representa el riesgo acumulado conforme varía el flujo vehicular entre las 0:00 y las 24:00 horas.")
                df_curva = curva_riesgo_24h(bache.tamanio, bache.profundidad, bache.riesgo_vial, bache.trafico)
                st.area_chart(df_curva)

                st.subheader("Historial de atención")
                mostrar_historial(obtener_historial(bache.folio))
            else:
                st.warning("No encontramos ningún reporte con ese folio. Verifica que esté bien escrito.")

    with tab_aviso:
        st.subheader("Acerca de Baches Inteligentes · Xochimilco")
        st.write(
            "**Baches Inteligentes** es un Sistema de Apoyo a la Decisión (DSS) diseñado para transformar "
            "reportes ciudadanos dispersos en rutas de mantenimiento vial priorizadas mediante Ciencia de Datos."
        )

        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.markdown(r"""
            **1. ¿Cómo se calcula la urgencia (0 a 100)?**
            Cada variable capturada en escala de 1 a 5 se normaliza al rango $[0, 1]$ y se pondera según su impacto vial:
            * **Peligro vial:** 35 %
            * **Profundidad:** 30 %
            * **Flujo vehicular:** 20 %
            * **Tamaño superficial:** 15 %
            * **Factor hidráulico:** +8 puntos adicionales si existe fuga o coladera cercana.
            * *Regla crítica:* Todo bache con profundidad nivel 5 y peligro $\ge 4$ se clasifica automáticamente como **Emergencia**.
            """)
        with col_info2:
            st.markdown("""
            **2. Modelado Matemático y Estructuras**
            * **Cálculo Integral (Regla del Trapecio):** Estima el riesgo acumulado de incidente vial entre las 6:00 y 22:00 h integrando la curva de flujo horario, así como la probabilidad de expansión del daño a 30 días.
            * **Listas Simplemente Enlazadas:** Organiza las paradas de cada cuadrilla por colonia enlazando cada reporte activo con el siguiente nodo de mayor urgencia.
            * **Inspección Técnica y Material:** En campo, el personal captura medidas reales en centímetros para calcular mezcla asfáltica y costo estimado.
            * **Persistencia Relacional:** Base de datos en la nube con auditoría histórica de estados y reevaluaciones.
            """)

        st.warning(
            "**Alcance institucional:** Este desarrollo es un prototipo académico con fines de investigación y docencia; "
            "no constituye un canal oficial de atención de la Alcaldía Xochimilco ni del Gobierno de la CDMX."
        )

else:
    if not st.session_state.get("admin_ok", False):
        st.subheader("Acceso para personal operativo y administradores")
        with st.form("login_admin"):
            usuario = st.text_input("Usuario", value="admin")
            clave = st.text_input("Contraseña", type="password")
            login = st.form_submit_button("Iniciar sesión")
            if login:
                if verificar_admin(usuario, clave):
                    st.session_state.admin_ok = True
                    st.session_state.admin_usuario = usuario.strip()
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos. Inténtalo nuevamente.")
        st.info("Credenciales de acceso para la demostración: usuario `admin` y contraseña `Demo-2026!`.")
    else:
        col_titulo, col_salir = st.columns([5, 1])
        with col_titulo:
            st.subheader("Panel de Gestión Vial · Alcaldía Xochimilco")
        with col_salir:
            if st.button("Cerrar sesión", key="logout_top", type="secondary"):
                st.session_state.admin_ok = False
                st.session_state.admin_usuario = ""
                st.rerun()

        operador_actual = st.session_state.get("admin_usuario", "admin")

        tab_cola, tab_ruta, tab_revision, tab_reparados, tab_csv = st.tabs([
            "📋 Reportes pendientes",
            "🚚 Ruta para cuadrillas",
            "🔧 Inspección y ajuste",
            "✅ Historial de reparados",
            "📤 Carga de CSV",
        ])

        with tab_cola:
            df = cargar_baches()
            if df.empty:
                st.info("Por el momento no hay reportes pendientes de atención.")
            else:
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Reportes activos", len(df))
                col_m2.metric("Casos en Emergencia", int((df["nivel"] == "Emergencia").sum()))
                col_m3.metric("Urgencia promedio", f"{df['puntuacion'].mean():.1f}/100")

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.markdown("**Distribución por colonia y prioridad**")
                    tabla_cruzada = pd.crosstab(df["zona"], df["nivel"])
                    mapa_colores = {
                        "Emergencia": "#E53935",
                        "Prioridad alta": "#FB8C00",
                        "Prioridad media": "#FDD835",
                        "Prioridad baja": "#1E88E5",
                    }
                    colores = [mapa_colores.get(col, "#757575") for col in tabla_cruzada.columns]
                    st.bar_chart(tabla_cruzada, color=colores)

                with col_g2:
                    st.markdown("**Relación entre profundidad e índice de urgencia**")
                    df_dispersion = df[["profundidad", "puntuacion", "nivel", "tamanio"]].rename(
                        columns={
                            "profundidad": "Profundidad (1–5)",
                            "puntuacion": "Urgencia (0–100)",
                            "nivel": "Nivel de prioridad",
                            "tamanio": "Tamaño (1–5)",
                        }
                    )
                
                    niveles_orden = [
                        "Emergencia",
                        "Prioridad alta",
                        "Prioridad media",
                        "Prioridad baja",
                        "En revisión",
                    ]
                    colores_fijos = [
                        "#E53935",
                        "#FB8C00",
                        "#FDD835",
                        "#1E88E5",
                        "#757575",
                    ]
                
                    escala_color = alt.Scale(domain=niveles_orden, range=colores_fijos)
                
                    dispersion_chart = (
                        alt.Chart(df_dispersion)
                        .mark_circle(opacity=0.88, stroke="#1d1b16", strokeWidth=0.6)
                        .encode(
                            x=alt.X(
                                "Profundidad (1–5):Q",
                                scale=alt.Scale(domain=[0.5, 5.5]),
                                title="Profundidad (1–5)",
                            ),
                            y=alt.Y(
                                "Urgencia (0–100):Q",
                                scale=alt.Scale(domain=[0, 105]),
                                title="Urgencia (0–100)",
                            ),
                            color=alt.Color(
                                "Nivel de prioridad:N",
                                scale=escala_color,
                                legend=alt.Legend(title="Nivel de prioridad"),
                            ),
                            size=alt.Size(
                                "Tamaño (1–5):Q",
                                scale=alt.Scale(range=[80, 420]),
                                legend=alt.Legend(title="Tamaño (1–5)"),
                            ),
                            tooltip=[
                                "Nivel de prioridad:N",
                                "Profundidad (1–5):Q",
                                "Urgencia (0–100):Q",
                                "Tamaño (1–5):Q",
                            ],
                        )
                        .interactive()
                    )
                
                    st.altair_chart(dispersion_chart, use_container_width=True)

                st.markdown("**Resumen por prioridad y estado**")
                mostrar_resumen_operativo()
                st.divider()

                st.markdown("**Listado general de reportes por atender**")
                mostrar_tabla_baches(df)
                
                st.divider()
                st.subheader("Actualizar estado de atención")
                folio_estado = st.selectbox("Selecciona el folio a actualizar", df.folio.tolist(), key="folio_cambio_estado")
                estado_nuevo = st.selectbox("Nuevo estado del reporte", sorted(ESTADOS_VALIDOS), key="estado_nuevo")
                nota_estado = st.text_input("Nota de seguimiento", placeholder="Ej. Cuadrilla asignada para revisión matutina", key="nota_cambio_estado")
                if st.button("Guardar cambio de estado", key="guardar_estado"):
                    try:
                        actualizar_estado(folio_estado, estado_nuevo, nota_estado.strip(), operador_actual)
                        st.success("Estado actualizado correctamente.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

        with tab_ruta:
            st.subheader("Ruta sugerida de atención por colonia")
            st.caption("Orden secuencial de paradas para la cuadrilla de mantenimiento, comenzando por los baches de mayor urgencia.")
            df_activos = cargar_baches()
            if df_activos.empty:
                st.info("No hay reportes activos para generar una ruta de trabajo.")
            else:
                colonias_con_baches = sorted(df_activos["zona"].unique().tolist())
                colonia_ruta = st.selectbox("Selecciona la colonia a atender", colonias_con_baches)

                lista_ruta = ListaEnlazadaRuta()
                for reporte_obj in listar_reportes():
                    if reporte_obj.estado != "Reparado" and reporte_obj.zona == colonia_ruta:
                        lista_ruta.agregar_parada(reporte_obj)

                recorrido = lista_ruta.obtener_recorrido()
                st.dataframe(recorrido, width='stretch', hide_index=True)
                st.download_button(
                    label=f"Descargar CSV de ruta ({colonia_ruta})",
                    data=generar_csv_ruta_cuadrilla(recorrido),
                    file_name=f"ruta_{colonia_ruta.lower().replace(' ', '_')}.csv",
                    mime="text/csv",
                )

        with tab_revision:
            df = cargar_baches()
            st.subheader("Inspección en campo por medidas reales y cálculo de material")
            st.caption(
                "Ingresa las mediciones verificadas en sitio. El sistema calcula automáticamente el nivel (1–5), "
                "la mezcla asfáltica necesaria (con 15 % por compactación) y el presupuesto estimado."
            )
            if df.empty:
                st.info("No hay reportes pendientes por revisar.")
            else:
                folio_revision = st.selectbox("Selecciona el reporte inspeccionado", df.folio.tolist(), key="folio_revision_variables")
                bache_actual = consultar_reporte(folio_revision)
                st.write(
                    f"**Ubicación:** {bache_actual.ubicacion} ({bache_actual.zona}) · "
                    f"**Prioridad actual:** {bache_actual.nivel} ({bache_actual.puntuacion}/100)"
                )

                largo_def, ancho_def = VALORES_REFERENCIA_TAMANIO.get(int(bache_actual.tamanio), (100.0, 80.0))
                prof_def = VALORES_REFERENCIA_PROFUNDIDAD.get(int(bache_actual.profundidad), 8.0)
                trafico_def = VALORES_REFERENCIA_TRAFICO.get(int(bache_actual.trafico), 10)
                idx_riesgo_def = max(0, min(4, int(bache_actual.riesgo_vial) - 1))

                c_med1, c_med2, c_med3 = st.columns(3)
                largo_cm = c_med1.number_input(
                    "Largo del cajeo (cm)", min_value=10.0, max_value=1000.0,
                    value=float(largo_def), step=5.0, key=f"med_largo_{folio_revision}"
                )
                ancho_cm = c_med2.number_input(
                    "Ancho del cajeo (cm)", min_value=10.0, max_value=1000.0,
                    value=float(ancho_def), step=5.0, key=f"med_ancho_{folio_revision}"
                )
                profundidad_cm = c_med3.number_input(
                    "Profundidad medida (cm)", min_value=1.0, max_value=200.0,
                    value=float(prof_def), step=1.0, key=f"med_prof_{folio_revision}"
                )

                c_op1, c_op2 = st.columns(2)
                vehiculos_min = c_op1.number_input(
                    "Flujo vehicular contado (vehículos por minuto)", min_value=0, max_value=200,
                    value=int(trafico_def), step=1, key=f"med_trafico_{folio_revision}"
                )
                costo_tonelada = c_op2.number_input(
                    "Costo unitario de mezcla colocada ($ MXN / tonelada)", min_value=500.0, max_value=20000.0,
                    value=2500.0, step=100.0, key=f"med_costo_{folio_revision}",
                    help="Valor editable según el tabulador vigente de obra pública."
                )

                opciones_riesgo = [texto for _, texto in CRITERIOS_PELIGRO]
                criterio_elegido = st.selectbox(
                    "Criterio observable de peligro vial en sitio",
                    opciones_riesgo,
                    index=idx_riesgo_def,
                    key=f"med_riesgo_{folio_revision}"
                )
                riesgo_nuevo = opciones_riesgo.index(criterio_elegido) + 1

                estimacion = calcular_material_y_costo(largo_cm, ancho_cm, profundidad_cm, costo_tonelada)
                tamanio_nuevo = clasificar_tamanio(estimacion["area_m2"])
                profundidad_nueva = clasificar_profundidad(profundidad_cm)
                trafico_nuevo = clasificar_trafico(vehiculos_min)

                st.markdown("**Estimación técnica de insumos y equivalencia de escala**")
                m_ins1, m_ins2, m_ins3, m_ins4 = st.columns(4)
                m_ins1.metric("Área de cajeo", f"{estimacion['area_m2']} m²", f"Nivel Tamaño: {tamanio_nuevo}/5")
                m_ins2.metric("Profundidad", f"{profundidad_cm:.1f} cm", f"Nivel Prof.: {profundidad_nueva}/5")
                m_ins3.metric(
                    "Mezcla asfáltica",
                    f"{estimacion['peso_kg']} kg",
                    f"{estimacion['costales_25kg']} costales (25 kg) · {estimacion['toneladas']} t"
                )
                m_ins4.metric("Gasto estimado", f"${estimacion['costo_estimado']:,.2f} MXN", f"Nivel Tráfico: {trafico_nuevo}/5")

                nota_revision = st.text_area(
                    "Observaciones técnicas de la inspección (obligatorio)",
                    placeholder="Ej. Se midió con flexómetro tras lluvias; se requiere recorte rectangular y compactación de base.",
                    key=f"nota_med_{folio_revision}"
                )

                if st.button("Guardar inspección y recalcular prioridad", type="primary", key=f"btn_med_{folio_revision}"):
                    if not nota_revision.strip():
                        st.error("Escribe una observación breve sobre la inspección realizada.")
                    else:
                        resumen_medicion = (
                            f"[Medición: {largo_cm:.0f}x{ancho_cm:.0f} cm ({estimacion['area_m2']} m²), "
                            f"Prof: {profundidad_cm:.1f} cm, Flujo: {vehiculos_min} veh/min | "
                            f"Asfalto: {estimacion['peso_kg']} kg ({estimacion['costales_25kg']} costales) | "
                            f"Gasto est.: ${estimacion['costo_estimado']:,.2f} MXN]"
                        )
                        nota_completa = f"{resumen_medicion} {nota_revision.strip()}"
                        try:
                            actualizar_variables_revision(
                                folio_revision,
                                {
                                    "tamanio": tamanio_nuevo,
                                    "profundidad": profundidad_nueva,
                                    "riesgo_vial": riesgo_nuevo,
                                    "trafico": trafico_nuevo,
                                },
                                nota_completa,
                                operador_actual,
                            )
                            st.success("Inspección por medidas guardada y prioridad recalculada.")
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))

                st.divider()
                st.subheader("Historial de ajustes de urgencia")
                mostrar_historial_prioridad(obtener_historial_prioridad(folio_revision))

        with tab_reparados:
            df_reparados = cargar_reparados()
            st.subheader("Archivo de reportes atendidos y reparados")
            if df_reparados.empty:
                st.info("Aún no hay baches marcados como reparados.")
            else:
                mostrar_tabla_baches(df_reparados)
                folio_reparado = st.selectbox("Consultar bitácora del folio:", df_reparados.folio.tolist())
                st.subheader("Bitácora de estados")
                mostrar_historial(obtener_historial(folio_reparado))
                st.subheader("Historial de ajustes de urgencia")
                mostrar_historial_prioridad(obtener_historial_prioridad(folio_reparado))

        with tab_csv:
            st.subheader("Carga masiva por CSV (teléfono, ventanilla, brigadas y jornadas)")
            st.caption(
                "Usa la plantilla oficial con las colonias verificadas (Santa María Tepepan, "
                "Bosque Residencial del Sur y San Juan Tepepan) y valores del 1 al 5."
            )

            plantilla_csv = generar_plantilla_csv(incluir_ejemplo=True)
            st.download_button(
                label="Descargar plantilla CSV",
                data=plantilla_csv,
                file_name="plantilla_baches_xochimilco.csv",
                mime="text/csv",
            )

            archivo_csv = st.file_uploader(
                "Sube el archivo CSV completado",
                type=["csv"],
                key="uploader_carga_csv_admin",
            )

            if archivo_csv is not None:
                resultado_csv = validar_csv_reportes(archivo_csv.getvalue())

                if resultado_csv["columnas_faltantes"]:
                    st.error(
                        "Al archivo le faltan columnas obligatorias: "
                        + ", ".join(resultado_csv["columnas_faltantes"])
                    )
                else:
                    filas_validas = resultado_csv["filas_validas"]
                    errores = resultado_csv["errores"]

                    col_v, col_e = st.columns(2)
                    col_v.metric("Filas válidas", len(filas_validas))
                    col_e.metric("Filas con error", len(errores))

                    if filas_validas:
                        st.markdown("**Vista previa de filas válidas listas para guardar**")
                        st.dataframe(
                            [
                                {
                                    "Fila CSV": item["fila_csv"],
                                    "Colonia": item["datos"]["zona"],
                                    "Ubicación": item["datos"]["ubicacion"],
                                    "Tipo de vía": item["datos"]["tipo_via"],
                                    "Tamaño": item["datos"]["tamanio"],
                                    "Profundidad": item["datos"]["profundidad"],
                                    "Riesgo vial": item["datos"]["riesgo_vial"],
                                    "Tráfico": item["datos"]["trafico"],
                                }
                                for item in filas_validas
                            ],
                            width='stretch',
                            hide_index=True,
                        )

                    if errores:
                        st.markdown("**Filas con observaciones / errores (no se insertarán)**")
                        st.dataframe(errores, width='stretch', hide_index=True)

                    if filas_validas and st.button(
                        f"Importar {len(filas_validas)} reporte(s) válido(s)",
                        type="primary",
                        key="btn_importar_csv_admin",
                    ):
                        creados = importar_filas_validas(filas_validas)
                        st.success(f"Se registraron {len(creados)} reporte(s) en la base de datos.")
                        st.dataframe(creados, width='stretch', hide_index=True)
                        st.rerun()
                        
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888888; font-size: 0.85em; padding-top: 20px;'>"
    "© 2026 Proyecto Académico de Ciencia de Datos (CDMX). — Bacheo inteligente<br>"
    "Licenciatura en ciencia de datos para negocios | Universidad Nacional Rosario Castellanos<br>"
    "Unidad académica Magdalena Contreras<br><br>"
    "<b>Autores:</b> Martinez Ventura Andrea, Gonzalez Manriquez Jose Fernando, "
    "Sánchez Flores Brandon."
    "</div>",
    unsafe_allow_html=True
)
