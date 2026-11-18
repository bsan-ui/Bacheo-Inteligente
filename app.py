import streamlit as st
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
from services.seguimiento import actualizar_estado, obtener_historial, ESTADOS_VALIDOS
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
        "ubicacion": "Calle (Xochimilco)",
        "zona": "Colonia / Barrio",
        "tamanio": "Tamaño (1–5)",
        "profundidad": "Profundidad (1–5)",
        "riesgo_vial": "Peligro vial (1–5)",
        "trafico": "Tráfico (1–5)",
        "tipo_via": "Tipo de vía",
        "fecha_reporte": "Fecha de registro",
        "puntuacion": "Prioridad (0–100)",
        "nivel": "Nivel de prioridad",
        "estado": "Estado",
        "nota_estado": "Último comentario",
    }
    st.dataframe(df.rename(columns=nombres), width='stretch', hide_index=True)


def mostrar_historial(historial):
    if not historial:
        st.info("Sin registros de seguimiento para este reporte.")
        return
    filas = []
    for h in historial:
        filas.append({
            "Fecha": h.fecha,
            "Estado del reporte": h.estado,
            "Comentario": h.nota or "Sin comentario",
            "Actualizado por": "Personal administrador" if h.operador else "Sistema",
        })
    st.dataframe(filas, width='stretch', hide_index=True)


def mostrar_historial_prioridad(historial_prioridad):
    if not historial_prioridad:
        st.info("Sin historial de cambios de prioridad para este reporte.")
        return
    filas = []
    for h in historial_prioridad:
        filas.append({
            "Fecha": h.fecha,
            "Puntuación (0–100)": h.puntuacion,
            "Nivel asignado": h.nivel,
            "Motivo del cálculo": h.motivo,
        })
    st.dataframe(filas, width='stretch', hide_index=True)


def mostrar_resumen_operativo():
    df_resumen = resumen_estados()
    if df_resumen.empty:
        return
    nombres_resumen = {
        "nivel": "Nivel de prioridad",
        "estado": "Estado actual",
        "cantidad": "Cantidad de baches",
    }
    st.dataframe(df_resumen.rename(columns=nombres_resumen), width='stretch', hide_index=True)


st.set_page_config(page_title="Baches Inteligentes — Xochimilco", page_icon="🕳️", layout="wide")
init_db()
seed_demo()

st.title("🕳️ Baches Inteligentes · Alcaldía Xochimilco")
st.caption("Prototipo académico · Demarcación territorial: Xochimilco, CDMX")
pagina = st.sidebar.radio("¿Qué quieres hacer?", ["Inicio", "Panel administrativo"])

if pagina == "Inicio":
    tab_crear, tab_consultar, tab_aviso = st.tabs(
        ["➕ Reportar un bache", "🔍 Consultar un reporte y riesgo", "ℹ️ Información importante"]
    )
    with tab_crear:
        st.subheader("Reportar un bache en la Alcaldía Xochimilco")
        st.info("📍 **Alcaldía fija de estudio:** Xochimilco. Selecciona primero la colonia para cargar sus calles.")

        col_ubic1, col_ubic2 = st.columns(2)
        lista_colonias = list(COLONIAS_XOCHIMILCO.keys())
        zona = col_ubic1.selectbox("1. ¿En qué colonia o barrio de Xochimilco está?", lista_colonias)
        calles_disponibles = COLONIAS_XOCHIMILCO[zona]
        calle_seleccionada = col_ubic2.selectbox("2. Selecciona la calle o avenida", calles_disponibles)

        referencia_extra = st.text_input(
            "3. Entre qué calles o referencia aproximada (opcional, sin datos personales)",
            max_chars=100,
            placeholder="Ej. Frente al mercado o esquina con cerrada"
        )

        col1, col2 = st.columns(2)
        tamanio = col1.slider("Tamaño del bache (1 = pequeño, 5 = muy grande)", 1, 5, 3)
        profundidad = col2.slider("Profundidad (1 = superficial, 5 = socavón)", 1, 5, 3)
        riesgo = col1.slider("Peligro para quienes pasan por ahí (1 a 5)", 1, 5, 3)
        trafico = col2.slider("Cantidad de tráfico en la vía (1 a 5)", 1, 5, 3)

        tipo = st.selectbox("¿Qué tipo de lugar es?", ["Calle local", "Avenida", "Cruce", "Cerca de escuela/hospital", "No sé"])
        red_hidraulica = st.checkbox("💧 ¿Pasa una red hidráulica, coladera pluvial o fuga de agua junto al bache?")
        descripcion = st.text_area("Describe brevemente cómo está el bache (sin datos personales)", max_chars=600)
        confirmar_aviso = st.checkbox("Entiendo que no debo incluir datos personales.")

        # Verificación preventiva de duplicados en tiempo real antes de insertar
        duplicados = buscar_duplicados(zona, calle_seleccionada, tamanio, profundidad)
        forzar_registro = False
        if duplicados:
            st.warning(
                f"⚠️ **Aviso de posible duplicado:** Ya tenemos {len(duplicados)} reporte(s) activo(s) "
                f"en **{calle_seleccionada}** ({zona}) con tamaño y profundidad similares."
            )
            filas_dup = [{
                "Folio existente": d.folio,
                "Calle": d.ubicacion,
                "Tamaño": d.tamanio,
                "Profundidad": d.profundidad,
                "Prioridad": d.nivel,
                "Estado": d.estado
            } for d in duplicados]
            st.dataframe(filas_dup, width='stretch', hide_index=True)
            forzar_registro = st.checkbox(
                "Confirmo que se trata de un bache distinto en la misma calle y deseo registrarlo de todos modos."
            )

        if st.button("Enviar reporte de prueba", type="primary"):
            if not confirmar_aviso:
                st.error("Antes de continuar, confirma que usarás únicamente información sin datos personales.")
            elif duplicados and not forzar_registro:
                st.error("Se detectó un reporte muy similar. Usa el folio existente o marca la casilla de confirmación de arriba para registrar uno nuevo.")
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
                    st.success(f"¡Listo! Registramos el bache en Xochimilco. Guarda este folio: {folio}")
                    mostrar_tabla_baches(cargar_baches().head(10))
                except Exception as exc:
                    st.error(f"No se pudo crear el reporte: {exc}")

    with tab_consultar:
        st.subheader("Consulta el estado y la predicción matemática de un reporte")
        folio_consulta = st.text_input("Escribe el folio del reporte", placeholder="Ej. B-XXXXXXXX", key="folio_publico")
        if st.button("Buscar reporte", key="btn_consultar"):
            bache = consultar_reporte(folio_consulta)
            if bache and bache.estado == "Reparado":
                st.info("Este bache ya fue reparado. Su expediente completo está en el panel administrativo.")
            elif bache:
                st.write(f"**Alcaldía:** Xochimilco · **Colonia:** {bache.zona} · **Calle:** {bache.ubicacion}")
                tiene_agua = "[Red hidráulica/drenaje]" in bache.descripcion
                prob_bache = probabilidad_nuevo_bache(bache.profundidad, bache.trafico, tiene_agua, dias=30)
                prob_acc = probabilidad_accidente_horario(bache.tamanio, bache.profundidad, bache.riesgo_vial, bache.trafico, 6, 22)

                c_m1, c_m2, c_m3 = st.columns(3)
                c_m1.metric("Prioridad actual", f"{bache.puntuacion}/100 ({bache.nivel})")
                c_m2.metric("Prob. de nuevo bache (30 días)", f"{prob_bache} %")
                c_m3.metric("Riesgo acumulado de accidente (6–22 h)", f"{prob_acc} %")

                st.markdown("**Curva de riesgo horario e integral bajo la curva (0:00 a 24:00 h)**")
                df_curva = curva_riesgo_24h(bache.tamanio, bache.profundidad, bache.riesgo_vial, bache.trafico)
                st.area_chart(df_curva)

                st.subheader("Actualizaciones del reporte")
                mostrar_historial(obtener_historial(bache.folio))
            else:
                st.warning("No encontramos un reporte con ese folio.")

    with tab_aviso:
        st.subheader("Sobre este prototipo para Xochimilco")
        st.write("Prototipo escolar enfocado en las colonias de Xochimilco con datos sintéticos.")

else:
    st.subheader("Entrada para personal administrador")
    with st.form("login_admin"):
        usuario = st.text_input("Usuario de demostración", value="admin")
        clave = st.text_input("Contraseña de demostración", type="password")
        login = st.form_submit_button("Entrar")
        if login:
            st.session_state.admin_ok = verificar_admin(usuario, clave)
            if not st.session_state.admin_ok:
                st.error("Usuario o contraseña incorrectos.")

    if not st.session_state.get("admin_ok", False):
        st.info("Credenciales de demo: usuario `admin` y contraseña `Demo-2026!`.")
    else:
        tab_cola, tab_ruta, tab_revision, tab_reparados = st.tabs([
            "📋 Reportes y gráficas",
            "🚚 Ruta en Lista Enlazada",
            "🔧 Revisar un bache",
            "✅ Baches reparados"
        ])

        with tab_cola:
            df = cargar_baches()
            st.subheader("Panel operativo de Xochimilco")
            if df.empty:
                st.info("No hay reportes pendientes.")
            else:
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Total pendientes", len(df))
                col_m2.metric("En Emergencia", int((df["nivel"] == "Emergencia").sum()))
                col_m3.metric("Prioridad promedio", f"{df['puntuacion'].mean():.1f}/100")

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.markdown("**Baches activos por colonia de Xochimilco**")
                    st.bar_chart(df["zona"].value_counts())
                with col_g2:
                    st.markdown("**Baches activos por nivel de prioridad**")
                    st.bar_chart(df["nivel"].value_counts())

                st.markdown("**Resumen por nivel de prioridad y estado**")
                mostrar_resumen_operativo()
                st.divider()

                mostrar_tabla_baches(df)
                st.download_button("Descargar lista CSV", df.to_csv(index=False).encode("utf-8-sig"), "baches_xochimilco.csv", "text/csv")

                st.divider()
                st.subheader("Actualizar el avance de un bache")
                folio_estado = st.selectbox("Reporte a actualizar", df.folio.tolist(), key="folio_cambio_estado")
                estado_nuevo = st.selectbox("Nuevo estado", sorted(ESTADOS_VALIDOS), key="estado_nuevo")
                nota_estado = st.text_input("Comentario sobre el avance", key="nota_cambio_estado")
                if st.button("Guardar actualización", key="guardar_estado"):
                    try:
                        actualizar_estado(folio_estado, estado_nuevo, nota_estado.strip(), usuario)
                        st.success("Estado actualizado.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

        with tab_ruta:
            st.subheader("Orden de recorrido para cuadrilla (Lista Simplemente Enlazada)")
            st.caption("Enlaza cada bache activo como un nodo (`NodoBache`) apuntando al siguiente según su urgencia.")
            df_activos = cargar_baches()
            if df_activos.empty:
                st.info("No hay baches activos para armar una ruta.")
            else:
                colonias_con_baches = sorted(df_activos["zona"].unique().tolist())
                colonia_ruta = st.selectbox("Selecciona la colonia de Xochimilco para despachar cuadrilla", colonias_con_baches)

                lista_ruta = ListaEnlazadaRuta()
                for reporte_obj in listar_reportes():
                    if reporte_obj.estado != "Reparado" and reporte_obj.zona == colonia_ruta:
                        lista_ruta.agregar_parada(reporte_obj)

                recorrido = lista_ruta.obtener_recorrido()
                st.dataframe(recorrido, width='stretch', hide_index=True)

        with tab_revision:
            df = cargar_baches()
            st.subheader("Actualizar evaluación tras inspección")
            if df.empty:
                st.info("No hay baches pendientes.")
            else:
                folio_revision = st.selectbox("Elige el reporte a revisar", df.folio.tolist(), key="folio_revision_variables")
                bache_actual = consultar_reporte(folio_revision)
                st.write(f"**Calle:** {bache_actual.ubicacion} ({bache_actual.zona}) · **Prioridad:** {bache_actual.nivel} ({bache_actual.puntuacion}/100)")
                with st.form(f"form_revision_{folio_revision}"):
                    c1, c2 = st.columns(2)
                    tamanio_nuevo = c1.slider("Tamaño actual (1–5)", 1, 5, int(bache_actual.tamanio))
                    profundidad_nueva = c2.slider("Profundidad actual (1–5)", 1, 5, int(bache_actual.profundidad))
                    riesgo_nuevo = c1.slider("Peligro vial (1–5)", 1, 5, int(bache_actual.riesgo_vial))
                    trafico_nuevo = c2.slider("Tráfico (1–5)", 1, 5, int(bache_actual.trafico))
                    nota_revision = st.text_area("Observaciones de la inspección (obligatorio)")
                    guardar_revision = st.form_submit_button("Guardar revisión y recalcular")
                if guardar_revision:
                    try:
                        actualizar_variables_revision(
                            folio_revision,
                            {"tamanio": tamanio_nuevo, "profundidad": profundidad_nueva, "riesgo_vial": riesgo_nuevo, "trafico": trafico_nuevo},
                            nota_revision,
                            usuario,
                        )
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

                st.divider()
                st.subheader("Historial de reevaluaciones de prioridad")
                mostrar_historial_prioridad(obtener_historial_prioridad(folio_revision))

        with tab_reparados:
            df_reparados = cargar_reparados()
            st.subheader("Expediente de baches reparados en Xochimilco")
            if df_reparados.empty:
                st.info("Todavía no hay baches marcados como reparados.")
            else:
                mostrar_tabla_baches(df_reparados)
                folio_reparado = st.selectbox("Ver historial del folio:", df_reparados.folio.tolist())
                st.subheader("Historial de estados")
                mostrar_historial(obtener_historial(folio_reparado))
                st.subheader("Historial de prioridad")
                mostrar_historial_prioridad(obtener_historial_prioridad(folio_reparado))