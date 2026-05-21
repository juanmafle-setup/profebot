import streamlit as st
import plotly.express as px
import pandas as pd
from modules.db import (
    obtener_estadisticas_dashboard,
    obtener_historial,
    obtener_top_consultas,
    obtener_distribucion_categorias,
    obtener_terminos_frecuentes
)
from modules.search import evaluar_busqueda

def mostrar_dashboard():
    # Estilos CSS modernos para las tarjetas de métricas
    st.markdown("""
    <style>
    .dashboard-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    .metric-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        transition: transform 0.2s;
    }
    .metric-box:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 40px rgba(99,102,241,0.3);
    }
    .metric-value {
        font-size: 2.8rem;
        font-weight: 800;
        color: white;
        margin: 8px 0;
    }
    .metric-label {
        font-size: 0.95rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .section-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #6366f1, transparent);
        margin: 2rem 0 1.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Encabezado
    st.markdown('<h2 class="dashboard-title">📊 Dashboard Docente</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem;">Métricas y análisis del uso de ProfeBot</p>', unsafe_allow_html=True)

    # ========================
    # 1. MÉTRICAS GLOBALES
    # ========================
    try:
        stats = obtener_estadisticas_dashboard()
    except Exception as e:
        st.error(f"Error al cargar métricas globales: {e}")
        stats = None

    if stats is None or stats['total_consultas'] == 0:
        st.info("ℹ️ No hay datos todavía. Realizá algunas consultas en la vista 💬 Chat para ver estadísticas.")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Total consultas</div>
            <div class="metric-value">{stats['total_consultas']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">WER promedio</div>
            <div class="metric-value" style="font-size: 1.8rem;">N/A</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Perplejidad promedio</div>
            <div class="metric-value">{stats['pp_promedio']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Tiempo promedio (ms)</div>
            <div class="metric-value">{stats['tiempo_promedio_ms']:.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ========================
    # 2. TOP 10 CONSULTAS + EVOLUCIÓN TEMPORAL (lado a lado)
    # ========================
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown('### 🔁 Top 10 consultas más frecuentes')
        try:
            top_consultas = obtener_top_consultas(10)
            if top_consultas:
                df_top = pd.DataFrame(top_consultas)
                fig_top = px.bar(df_top, x='frecuencia', y='texto', orientation='h',
                                 labels={'frecuencia': 'Frecuencia', 'texto': 'Pregunta'},
                                 color='frecuencia', color_continuous_scale='blues')
                fig_top.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#e2e8f0',
                    height=400
                )
                st.plotly_chart(fig_top, use_container_width=True)
            else:
                st.info("No hay consultas repetidas aún.")
        except Exception as e:
            st.warning(f"Error: {e}")

    with col_der:
        st.markdown('### 📈 Evolución temporal')
        if stats['consultas_por_dia']:
            df_dias = pd.DataFrame(stats['consultas_por_dia'])
            fig_line = px.line(df_dias, x='fecha', y='cantidad', markers=True,
                               labels={'fecha': 'Fecha', 'cantidad': 'Consultas'})
            fig_line.update_traces(line_color='#6366f1', line_width=3, marker_size=8)
            fig_line.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#e2e8f0',
                height=400
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Sin evolución temporal.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ========================
    # 3. DISTRIBUCIÓN POR CATEGORÍAS (torta) + TÉRMINOS MÁS FRECUENTES
    # ========================
    col_izq2, col_der2 = st.columns(2)

    with col_izq2:
        st.markdown('### 🥧 Distribución por categorías')
        try:
            categorias = obtener_distribucion_categorias()
            if categorias:
                df_cat = pd.DataFrame(categorias)
                fig_pie = px.pie(df_cat, names='categoria', values='frecuencia',
                                 hole=0.4)
                fig_pie.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#e2e8f0',
                    height=400
                )
                fig_pie.update_traces(marker=dict(line=dict(color='#0f172a', width=1)))
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No hay categorías detectadas.")
        except Exception as e:
            st.warning(f"Error: {e}")

    with col_der2:
        st.markdown('### 🔤 Términos más frecuentes')
        try:
            terminos = obtener_terminos_frecuentes(15)
            if terminos:
                df_term = pd.DataFrame(terminos)
                fig_term = px.bar(df_term, x='frecuencia', y='termino', orientation='h',
                                  labels={'frecuencia': 'Frecuencia', 'termino': 'Término'},
                                  color='frecuencia', color_continuous_scale='viridis')
                fig_term.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#e2e8f0',
                    height=400
                )
                st.plotly_chart(fig_term, use_container_width=True)
            else:
                st.info("No hay suficientes palabras.")
        except Exception as e:
            st.warning(f"Error: {e}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ========================
    # 4. MÉTRICAS DE EVALUACIÓN (P, R, F1)
    # ========================
    st.markdown('### 🎯 Métricas de evaluación del motor de búsqueda')
        # ========================
    # 4. MÉTRICAS DE EVALUACIÓN (P, R, F1)
    # ========================
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
   
    
    try:
        metricas_eval = evaluar_busqueda()
        col_p, col_r, col_f1 = st.columns(3)
        with col_p:
            st.metric("Precisión (P)", f"{metricas_eval['precision']:.2f}")
        with col_r:
            st.metric("Recall (R)", f"{metricas_eval['recall']:.2f}")
        with col_f1:
            st.metric("F1-Score", f"{metricas_eval['f1']:.2f}")
        st.caption("Basado en 10 consultas de prueba etiquetadas sobre el corpus actual.")
    except Exception as e:
        st.warning(f"No se pudieron calcular las métricas de evaluación: {e}")

    # ========================
    # 5. ÚLTIMAS CONSULTAS (tabla compacta)
    # ========================
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown('### 📋 Últimas consultas')
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
        st.warning(f"Error: {e}")