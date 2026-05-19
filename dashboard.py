import streamlit as st
import plotly.express as px
import pandas as pd
from modules.db import obtener_estadisticas_dashboard, obtener_historial

def mostrar_dashboard():
    """Vista del dashboard docente con métricas reales desde la base de datos."""
    st.markdown("## 📊 Dashboard Docente")
    st.markdown("---")

    try:
        stats = obtener_estadisticas_dashboard()
    except Exception as e:
        st.error(f"Error al cargar métricas: {e}")
        stats = None

    if stats is None or stats['total_consultas'] == 0:
        st.info("ℹ️ No hay datos todavía. Realizá algunas consultas en la vista 💬 Chat para ver estadísticas.")
        return

    # Métricas globales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total consultas", stats['total_consultas'])
    with col2:
        st.metric("Perplejidad promedio", f"{stats['pp_promedio']:.2f}")
    with col3:
        st.metric("Tiempo promedio (ms)", f"{stats['tiempo_promedio_ms']:.0f}")
    with col4:
        st.metric("Score máx promedio", f"{stats['score_promedio']:.2f}")

    st.markdown("---")
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.subheader("📈 Consultas por día")
        if stats['consultas_por_dia']:
            df_dias = pd.DataFrame(stats['consultas_por_dia'])
            fig = px.line(df_dias, x='fecha', y='cantidad', markers=True,
                          labels={'fecha': 'Fecha', 'cantidad': 'Consultas'})
            fig.update_traces(line_color='#6366f1')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin evolución temporal.")

    with col_der:
        st.subheader("🧠 Conceptos más preguntados")
        if stats['top_conceptos']:
            df_conceptos = pd.DataFrame(stats['top_conceptos'])
            fig = px.bar(df_conceptos, x='frecuencia', y='concepto', orientation='h',
                         labels={'frecuencia': 'Frecuencia', 'concepto': 'Concepto'},
                         color='frecuencia', color_continuous_scale='blues')
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No se detectaron conceptos aún.")

    st.markdown("---")
    st.subheader("📋 Últimas consultas")
    try:
        ultimas = obtener_historial(limite=10)
        if ultimas:
            df_ultimas = pd.DataFrame(ultimas)
            columnas_mostrar = ['timestamp', 'texto_original', 'respuesta', 'pp', 'tiempo_ms']
            df_mostrar = df_ultimas[columnas_mostrar].copy()
            df_mostrar.rename(columns={
                'timestamp': 'Fecha',
                'texto_original': 'Pregunta',
                'respuesta': 'Respuesta',
                'pp': 'Perplejidad',
                'tiempo_ms': 'Tiempo (ms)'
            }, inplace=True)
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
        else:
            st.info("No hay consultas registradas.")
    except Exception as e:
        st.warning(f"No se pudieron cargar las últimas consultas: {e}")