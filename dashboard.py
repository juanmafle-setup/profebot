import json
import os
from datetime import datetime
import streamlit as st
import plotly.express as px
import pandas as pd
from modules.db import (obtener_estadisticas_dashboard, obtener_historial,
                         obtener_terminos_frecuentes, obtener_stats_quiz)
from modules.evaluacion import (evaluar_wer_batch, evaluar_busqueda,
                                 evaluar_ner_batch, evaluar_pp_test_set)
from modules.config import cargar_config, guardar_config


@st.cache_data(ttl=300)
def _cargar_wer():
    path = "data/frases_referencia.json"
    if not os.path.exists(path):
        return [], None
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


@st.cache_data(ttl=300)
def _cargar_ner():
    path = "data/ner_evaluacion.json"
    if not os.path.exists(path):
        return [], None
    with open(path, "r", encoding="utf-8") as f:
        ejemplos = json.load(f)
    return evaluar_ner_batch(ejemplos)


@st.cache_data(ttl=300)
def _cargar_pp_test():
    """Evalúa PP sobre el test set para los tres valores de k."""
    path_test   = "data/frases_test_pp.json"
    path_corpus = "data/corpus.txt"
    if not os.path.exists(path_test) or not os.path.exists(path_corpus):
        return [], {}
    with open(path_test, "r", encoding="utf-8") as f:
        frases = json.load(f)
    with open(path_corpus, "r", encoding="utf-8") as f:
        corpus = [l for l in f if l.strip() and not l.strip().startswith("#")]

    from modules.ngrams import ModeloNgramas
    promedios = {}
    for label, k in [("Corpus (k=0.01)", 0.01),
                     ("Equilibrado (k=0.1)", 0.1),
                     ("Agente (k=1.0)", 1.0)]:
        modelo = ModeloNgramas(n=2, k=k)
        modelo.entrenar(corpus)
        _, prom = evaluar_pp_test_set(frases, modelo)
        promedios[label] = prom

    return frases, promedios


def mostrar_dashboard():
    """Vista del dashboard docente con métricas reales."""

    st.markdown("## 📊 Dashboard Docente")
    st.markdown("---")

    # ── CONFIRMACIÓN VISUAL TRAS GUARDAR CONFIG ──────────────────────
    if st.session_state.get("config_guardada"):
        cfg_guardada = st.session_state.pop("config_guardada")
        st.success(
            f"✅ **Configuración guardada.**  \n"
            f"Nivel: **{cfg_guardada['nivel_respuesta']}** · "
            f"Entrada: **{cfg_guardada['modo_entrada']}** · "
            f"Salida: **{cfg_guardada['modo_salida']}**  \n"
            f"La próxima consulta usará estos ajustes."
        )

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
            st.session_state.ultimo_texto_procesado = ""
            st.session_state.ultima_respuesta = None
            st.session_state.config_guardada = {
                "nivel_respuesta": nivel_sel,
                "modo_entrada":    entrada_sel,
                "modo_salida":     salida_sel,
            }
            st.rerun()

    st.markdown("---")

    # ── Datos de la base ────────────────────────────────────────────
    try:
        stats = obtener_estadisticas_dashboard()
    except Exception as e:
        st.error(f"Error al cargar métricas: {e}")
        stats = None

    # ── Evaluaciones fijas ───────────────────────────────────────────
    wer_resultados, wer_promedio = _cargar_wer()
    prf_resultados, prf_global   = _cargar_prf()
    ner_resultados, ner_accuracy = _cargar_ner()
    _frases_test,   pp_promedios = _cargar_pp_test()
    quiz_stats                   = obtener_stats_quiz()

    # ── MÉTRICAS GLOBALES ────────────────────────────────────────────
    st.subheader("📈 Métricas globales del sistema")
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        st.metric("Total consultas", stats["total_consultas"] if stats else 0)
    with c2:
        st.metric("PP promedio", f"{stats['pp_promedio']:.2f}" if stats else "—")
    with c3:
        wer_label = f"{wer_promedio:.1%}" if wer_promedio is not None else "—"
        st.metric("WER promedio", wer_label)
    with c4:
        st.metric("Tiempo prom. (ms)", f"{stats['tiempo_promedio_ms']:.0f}" if stats else "—")
    with c5:
        st.metric("F1 búsqueda", f"{prf_global.get('f1', 0):.3f}" if prf_global else "—")
    with c6:
        ner_label = f"{ner_accuracy:.1%}" if ner_accuracy is not None else "—"
        st.metric("Accuracy NER", ner_label)

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

    # ── PERPLEJIDAD SOBRE TEST SET ───────────────────────────────────
    st.subheader("📐 Evaluación de Perplejidad — conjunto de test (15 frases)")
    if pp_promedios:
        col_pp1, col_pp2, col_pp3 = st.columns(3)
        labels = list(pp_promedios.keys())
        vals   = [pp_promedios[l] for l in labels]
        for col, lbl, val in zip([col_pp1, col_pp2, col_pp3], labels, vals):
            col.metric(f"PP media — {lbl}", f"{val:.2f}" if val is not None else "—")

        df_pp = pd.DataFrame({"Suavizado": labels, "PP media": vals})
        fig_pp = px.bar(df_pp, x="Suavizado", y="PP media",
                        color="Suavizado",
                        color_discrete_sequence=["#6366f1", "#10b981", "#f59e0b"],
                        labels={"PP media": "Perplejidad promedio"})
        fig_pp.update_layout(showlegend=False)
        st.plotly_chart(fig_pp, use_container_width=True)
        st.caption("Menor perplejidad = el modelo predice mejor el texto de test. "
                   "k pequeño (Corpus) memoriza más; k grande (Agente) generaliza más.")
    else:
        st.warning("No se encontró el archivo data/frases_test_pp.json")

    st.markdown("---")

    # ── EVALUACIÓN ACCURACY NER ──────────────────────────────────────
    st.subheader("🏷️ Evaluación NER — Accuracy por ejemplo (23 casos anotados)")
    if ner_resultados:
        df_ner = pd.DataFrame(ner_resultados)
        df_ner.columns = ["Texto", "Esperadas", "Encontradas", "Accuracy", "No halladas"]
        df_ner["Accuracy"] = df_ner["Accuracy"].apply(lambda x: f"{x:.0%}")
        st.dataframe(df_ner, use_container_width=True, hide_index=True)
        st.success(f"**Accuracy NER global: {ner_accuracy:.1%}** "
                   f"({int(ner_accuracy * sum(r['esperadas'] for r in ner_resultados))} / "
                   f"{sum(r['esperadas'] for r in ner_resultados)} entidades detectadas correctamente)")
    else:
        st.warning("No se encontró el archivo data/ner_evaluacion.json")

    st.markdown("---")

    # ── ESTADÍSTICAS DEL QUIZ ────────────────────────────────────────
    st.subheader("🧩 Estadísticas del Quiz")
    if quiz_stats:
        # Extraer conteos por tipo desde la distribución
        _dist_map = {d["tipo"]: d["cantidad"] for d in quiz_stats["distribucion"]}
        _q_corr = _dist_map.get("correcto",   0)
        _q_inco = _dist_map.get("incorrecto", 0)

        qc1, qc2, qc3, qc4 = st.columns(4)
        qc1.metric("📝 Total respondidas", quiz_stats["total"])
        qc2.metric("✅ Correctas",          _q_corr)
        qc3.metric("❌ Incorrectas",        _q_inco)
        qc4.metric("🎯 Accuracy",          f"{quiz_stats['accuracy']:.1%}")

        col_qd, col_qf = st.columns(2)

        with col_qd:
            st.markdown("**Distribución de resultados**")
            df_dist = pd.DataFrame(quiz_stats["distribucion"])
            if not df_dist.empty:
                fig_dist = px.pie(df_dist, names="tipo", values="cantidad",
                                  color="tipo",
                                  color_discrete_map={
                                      "correcto":   "#22c55e",
                                      "incorrecto": "#ef4444",
                                  })
                st.plotly_chart(fig_dist, use_container_width=True)

        with col_qf:
            st.markdown("**Palabras más falladas**")
            if quiz_stats["palabras_falladas"]:
                df_fall = pd.DataFrame(quiz_stats["palabras_falladas"])
                fig_fall = px.bar(df_fall, x="fallos", y="palabra", orientation="h",
                                  labels={"fallos": "Veces fallada", "palabra": "Palabra"},
                                  color="fallos", color_continuous_scale="reds")
                fig_fall.update_layout(yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig_fall, use_container_width=True)
            else:
                st.info("Sin errores registrados aún.")
    else:
        st.info("ℹ️ No hay respuestas de quiz registradas todavía. "
                "Usá el 🧩 Quiz para que aparezcan las estadísticas.")

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
            # Exportar a CSV
            csv_bytes = df_mostrar.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Exportar últimas consultas (CSV)",
                data=csv_bytes,
                file_name=f"consultas_profebot_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Descargá las últimas consultas en formato CSV",
            )
        else:
            st.info("No hay consultas registradas aún.")
    except Exception as e:
        st.warning(f"No se pudieron cargar las últimas consultas: {e}")
