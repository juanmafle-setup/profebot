import json
import os
import streamlit as st
import plotly.express as px
import pandas as pd
from modules.db import obtener_estadisticas_dashboard, obtener_historial, obtener_terminos_frecuentes
from modules.evaluacion import evaluar_wer_batch, evaluar_busqueda
from modules.config import cargar_config, guardar_config


@st.cache_data(ttl=300)
def _cargar_wer():
    path = "data/frases_referencia.json"
    if not os.path.exists(path):
        return [], 0.0
    with open(path, "r", encoding="utf-8") as f:
        frases = json.load(f)
    resultados, promedio = evaluar_wer_batch(frases)
    return resultados, promedio


@st.cache_data(ttl=300)
def _cargar_prf():
    path = "data/consultas_evaluacion.json"
    if not os.path.exists(path):
        return [], {}
    with open(path, "r", encoding="utf-8") as f:
        consultas = json.load(f)
    return evaluar_busqueda(consultas, top_k=5)


def mostrar_dashboard():
    """Vista del dashboard docente con métricas reales."""

    st.markdown("## 📊 Dashboard Docente")
    st.markdown("---")

    # ── PANEL DE CONFIGURACIÓN DEL AGENTE ───────────────────────────
    with st.expander("⚙️ Configuración del agente", expanded=False):
        cfg = cargar_config()

        st.markdown("### 🎛️ Ajustes de respuesta y modalidad")
        col_cfg1, col_cfg2 = st.columns(2)

        with col_cfg1:
            nivel_opciones = {
                "breve":    "Breve (1 oración)",
                "normal":   "Normal (1–2 oraciones)",
                "detallada":"Detallada (hasta 3 oraciones)",
            }
            nivel_actual = cfg.get("nivel_respuesta", "normal")
            nivel_sel = st.selectbox(
                "📝 Nivel de respuesta",
                options=list(nivel_opciones.keys()),
                format_func=lambda k: nivel_opciones[k],
                index=list(nivel_opciones.keys()).index(nivel_actual),
                help="Controla cuántas oraciones del corpus concatena la respuesta.",
            )

            entrada_opciones = {"texto": "Solo texto", "audio": "Solo audio", "ambos": "Texto y audio"}
            entrada_actual = cfg.get("modo_entrada", "ambos")
            entrada_sel = st.selectbox(
                "🎤 Modo de entrada",
                options=list(entrada_opciones.keys()),
                format_func=lambda k: entrada_opciones[k],
                index=list(entrada_opciones.keys()).index(entrada_actual),
                help="Define qué modalidad de entrada habilita el agente.",
            )

        with col_cfg2:
            salida_opciones = {"texto": "Solo texto", "audio": "Solo audio", "ambos": "Texto y audio"}
            salida_actual = cfg.get("modo_salida", "ambos")
            salida_sel = st.selectbox(
                "🔊 Modo de salida",
                options=list(salida_opciones.keys()),
                format_func=lambda k: salida_opciones[k],
                index=list(salida_opciones.keys()).index(salida_actual),
                help="Define si el agente responde en texto, audio o ambos.",
            )

            # num_resultados derivado del nivel
            num_map = {"breve": 1, "normal": 2, "detallada": 3}
            num_actual = num_map.get(nivel_sel, 1)
            st.info(
                f"🔢 **Oraciones en respuesta:** {num_actual}  \n"
                f"({'máximo 1' if num_actual == 1 else f'hasta {num_actual}'})"
            )

        if st.button("💾 Guardar configuración", use_container_width=True):
            nueva_cfg = {
                "nivel_respuesta": nivel_sel,
                "num_resultados":  num_map.get(nivel_sel, 1),
                "modo_entrada":    entrada_sel,
                "modo_salida":     salida_sel,
            }
            guardar_config(nueva_cfg)
            st.success("✅ Configuración guardada. Se aplicará en el próximo mensaje del chat.")
            st.rerun()

    st.markdown("---")

    # ── Datos de la base ────────────────────────────────────────────
    try:
        stats = obtener_estadisticas_dashboard()
    except Exception as e:
        st.error(f"Error al cargar métricas: {e}")
        stats = None

    # ── Evaluaciones fijas (WER y P/R/F1) ───────────────────────────
    wer_resultados, wer_promedio = _cargar_wer()
    prf_resultados, prf_global   = _cargar_prf()

    # ── MÉTRICAS GLOBALES ────────────────────────────────────────────
    st.subheader("📈 Métricas globales del sistema")
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric("Total consultas", stats["total_consultas"] if stats else 0)
    with c2:
        st.metric("PP promedio", f"{stats['pp_promedio']:.2f}" if stats else "—")
    with c3:
        wer_label = f"{wer_promedio:.1%}" if wer_promedio else "—"
        st.metric("WER promedio", wer_label)
    with c4:
        st.metric("Tiempo prom. (ms)", f"{stats['tiempo_promedio_ms']:.0f}" if stats else "—")
    with c5:
        st.metric("F1 búsqueda", f"{prf_global.get('f1', 0):.3f}" if prf_global else "—")

    st.markdown("---")

    if stats is None or stats["total_consultas"] == 0:
        st.info("ℹ️ No hay datos todavía. Realizá algunas consultas en el 💬 Chat para ver estadísticas.")
    else:
        # ── FILA 1: Evolución temporal + Top consultas ───────────────
        col_izq, col_der = st.columns(2)

        with col_izq:
            st.subheader("📅 Consultas por día")
            if stats["consultas_por_dia"]:
                df = pd.DataFrame(stats["consultas_por_dia"])
                fig = px.line(df, x="fecha", y="cantidad", markers=True,
                              labels={"fecha": "Fecha", "cantidad": "Consultas"})
                fig.update_traces(line_color="#6366f1")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin datos de evolución temporal.")

        with col_der:
            st.subheader("🔥 Top 10 consultas frecuentes")
            if stats.get("top_consultas"):
                df = pd.DataFrame(stats["top_consultas"])
                fig = px.bar(df, x="frecuencia", y="consulta", orientation="h",
                             labels={"frecuencia": "Veces", "consulta": "Consulta"},
                             color="frecuencia", color_continuous_scale="purples")
                fig.update_layout(yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay consultas repetidas aún.")

        st.markdown("---")

        # ── FILA 2: Intenciones + Términos frecuentes ────────────────
        col_izq2, col_der2 = st.columns(2)

        with col_izq2:
            st.subheader("🎯 Distribución de intenciones")
            if stats.get("dist_intenciones"):
                df = pd.DataFrame(stats["dist_intenciones"])
                fig = px.pie(df, names="intencion", values="frecuencia",
                             color_discrete_sequence=px.colors.qualitative.Set2)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin intenciones detectadas aún.")

        with col_der2:
            st.subheader("📊 Términos más buscados")
            terminos = obtener_terminos_frecuentes(limite=15)
            if terminos:
                df = pd.DataFrame(terminos)
                fig = px.bar(df, x="termino", y="frecuencia",
                             labels={"termino": "Término", "frecuencia": "Frecuencia"},
                             color="frecuencia", color_continuous_scale="teal")
                fig.update_layout(xaxis_tickangle=-35)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sin términos para mostrar aún.")

    st.markdown("---")

    # ── EVALUACIÓN WER ───────────────────────────────────────────────
    st.subheader("🎤 Evaluación ASR — Word Error Rate (10 frases de prueba)")
    if wer_resultados:
        df_wer = pd.DataFrame(wer_resultados)
        df_wer["wer"] = df_wer["wer"].apply(lambda x: f"{x:.1%}")
        df_wer.columns = ["Referencia", "Transcripción ASR", "WER"]
        st.dataframe(df_wer, use_container_width=True, hide_index=True)
        st.success(f"**WER promedio: {wer_promedio:.1%}**")
    else:
        st.warning("No se encontró el archivo data/frases_referencia.json")

    st.markdown("---")

    # ── EVALUACIÓN P / R / F1 ────────────────────────────────────────
    st.subheader("🔍 Evaluación del motor de búsqueda — Precisión, Recall y F1")
    if prf_resultados:
        df_prf = pd.DataFrame(prf_resultados)
        df_prf = df_prf[["query", "precision", "recall", "f1",
                          "recuperados", "relevantes_encontrados"]]
        df_prf.columns = ["Consulta", "Precisión", "Recall", "F1",
                           "Docs recuperados", "Relevantes encontrados"]
        st.dataframe(df_prf, use_container_width=True, hide_index=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Precisión promedio", f"{prf_global['precision']:.3f}")
        c2.metric("Recall promedio",    f"{prf_global['recall']:.3f}")
        c3.metric("F1 promedio",        f"{prf_global['f1']:.3f}")

        fig = px.bar(
            df_prf.melt(id_vars="Consulta", value_vars=["Precisión", "Recall", "F1"]),
            x="Consulta", y="value", color="variable", barmode="group",
            labels={"value": "Score", "variable": "Métrica"},
            color_discrete_sequence=["#6366f1", "#10b981", "#f59e0b"]
        )
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se encontró el archivo data/consultas_evaluacion.json")

    st.markdown("---")

    # ── ÚLTIMAS CONSULTAS ────────────────────────────────────────────
    st.subheader("📋 Últimas consultas registradas")
    try:
        ultimas = obtener_historial(limite=10)
        if ultimas:
            df = pd.DataFrame(ultimas)
            cols = ["timestamp", "texto_original", "intencion", "respuesta", "pp", "wer", "tiempo_ms"]
            cols_presentes = [c for c in cols if c in df.columns]
            df_mostrar = df[cols_presentes].copy()
            df_mostrar.rename(columns={
                "timestamp":      "Fecha",
                "texto_original": "Pregunta",
                "intencion":      "Intención",
                "respuesta":      "Respuesta",
                "pp":             "Perplejidad",
                "wer":            "WER",
                "tiempo_ms":      "Tiempo (ms)",
            }, inplace=True)
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
        else:
            st.info("No hay consultas registradas aún.")
    except Exception as e:
        st.warning(f"No se pudieron cargar las últimas consultas: {e}")
