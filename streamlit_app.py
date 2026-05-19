import streamlit as st
import os
import time
from datetime import datetime
import re

def tokenizar(texto):
    """Devuelve una lista de tokens (palabras y signos de puntuación por separado)."""
    return re.findall(r'\w+|[^\w\s]', texto)

from modules.asr import transcribir
from modules.search import buscar
from modules.tts import hablar
from modules.ngrams import ModeloNgramas
from modules.nlp import procesar
from modules.mic import grabar_audio
from modules.db import crear_tablas, guardar_consulta, obtener_historial, limpiar_historial

crear_tablas()  # Aseguramos que las tablas existan al iniciar la app

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="PROFEBOT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# SESSION (inicialización obligatoria)
# =====================================================

if "chat" not in st.session_state:
    st.session_state.chat = []
if "feedback" not in st.session_state:
    st.session_state.feedback = {}
if "estudiante" not in st.session_state:
    st.session_state.estudiante = "Estudiante1"
if "ultimo_audio" not in st.session_state:
    st.session_state.ultimo_audio = None
if "chat_cleared" not in st.session_state:
    st.session_state.chat_cleared = False
if "historial_cargado" not in st.session_state:
    st.session_state.historial_cargado = False
if "ultimo_texto_procesado" not in st.session_state:
    st.session_state.ultimo_texto_procesado = ""
if "procesando" not in st.session_state:
    st.session_state.procesando = False

# ========== CARGA DE HISTORIAL DESDE DB ==========
if not st.session_state.historial_cargado:
    st.session_state.chat = []   # limpiar para evitar duplicados
    try:
        historial_db = obtener_historial(limite=20)
        for consulta in reversed(historial_db):
            ts = consulta["timestamp"]
            if " " in ts:
                ts = ts.split(" ")[1][:5]
            st.session_state.chat.append(("Usuario", consulta["texto_original"] or "", ts))
            st.session_state.chat.append(("Bot", consulta["respuesta"] or "", ts))
    except Exception:
        pass
    st.session_state.historial_cargado = True

# =====================================================
# CSS MODERNO
# =====================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"]{
    font-family:'Inter',sans-serif;
}

/* FONDO */

.stApp{

    background:
        radial-gradient(circle at top left, rgba(59,130,246,0.14), transparent 30%),
        radial-gradient(circle at top right, rgba(139,92,246,0.10), transparent 25%),
        linear-gradient(180deg,#020617 0%, #0f172a 100%);

    color:white;
}

/* CONTENEDOR */

.block-container{

    max-width:1200px;

    padding-top:2rem;
}

/* SIDEBAR */

section[data-testid="stSidebar"]{

    background:#020617;

    border-right:1px solid rgba(255,255,255,0.05);
}

/* TITULO */

.main-title{

    font-size:4rem;

    font-weight:900;

    margin-bottom:0;

    background:linear-gradient(90deg,#60a5fa,#818cf8,#22d3ee);

    -webkit-background-clip:text;

    -webkit-text-fill-color:transparent;
}

.subtitle{

    color:#94a3b8;

    font-size:1.1rem;

    margin-bottom:35px;
}

/* INPUT */

.stTextInput input{

    background:rgba(15,23,42,0.92)!important;

    border:1px solid rgba(255,255,255,0.08)!important;

    border-radius:18px!important;

    color:white!important;

    padding:16px!important;

    font-size:16px!important;
}

.stTextInput input:focus{

    border:1px solid #6366f1!important;

    box-shadow:0 0 25px rgba(99,102,241,0.35)!important;
}

/* BOTONES */

.stButton button{

    border:none;

    border-radius:18px;

    background:linear-gradient(135deg,#2563eb,#7c3aed);

    color:white;

    font-weight:700;

    padding:0.9rem;

    transition:0.3s ease;

    width:100%;
}

.stButton button:hover{

    transform:translateY(-2px);

    box-shadow:0 0 20px rgba(124,58,237,0.35);
}

/* CARD RESPUESTA */

.response-card{

    background:rgba(15,23,42,0.88);

    border:1px solid rgba(255,255,255,0.05);

    border-radius:24px;

    padding:24px;

    margin-top:10px;

    box-shadow:0 10px 35px rgba(0,0,0,0.22);

    backdrop-filter:blur(12px);
}

/* METRICAS */

.metric-card{

    background:rgba(15,23,42,0.88);

    border:1px solid rgba(255,255,255,0.05);

    border-radius:24px;

    padding:28px;

    text-align:center;

    min-height:270px;

    box-shadow:0 8px 25px rgba(0,0,0,0.18);

    transition:0.3s ease;
}

.metric-card:hover{

    transform:translateY(-4px);

    box-shadow:0 0 30px rgba(99,102,241,0.2);
}

/* ICONOS */

.metric-icon{

    font-size:42px;

    margin-bottom:10px;
}

/* TITULO METRICA */

.metric-title{

    font-size:24px;

    font-weight:700;

    margin-bottom:20px;
}

/* TEXTO */

.soft-text{

    color:#94a3b8;

    font-size:15px;

    line-height:1.6;
}

/* BADGES */

.entity-badge{

    display:inline-block;

    padding:10px 14px;

    border-radius:999px;

    background:rgba(99,102,241,0.16);

    border:1px solid rgba(255,255,255,0.06);

    color:#c4b5fd;

    margin:5px;

    font-size:14px;

    font-weight:600;
}

/* NUMERO */

.big-number{

    font-size:56px;

    font-weight:900;

    margin-top:10px;

    background:linear-gradient(90deg,#60a5fa,#a78bfa);

    -webkit-background-clip:text;

    -webkit-text-fill-color:transparent;
}

/* CHAT */

.user-message{

    background:linear-gradient(135deg,#2563eb,#1d4ed8);

    padding:14px 18px;

    border-radius:18px 18px 6px 18px;

    margin-bottom:14px;

    margin-left:auto;

    width:fit-content;

    max-width:70%;

    color:white;

    box-shadow:0 6px 20px rgba(37,99,235,0.2);
}

.bot-message{

    background:rgba(15,23,42,0.92);

    border:1px solid rgba(255,255,255,0.05);

    padding:14px 18px;

    border-radius:18px 18px 18px 6px;

    margin-bottom:14px;

    width:fit-content;

    max-width:70%;

    color:white;

    box-shadow:0 6px 20px rgba(0,0,0,0.2);
}

/* DIVIDER */

.divider{

    height:1px;

    background:rgba(255,255,255,0.06);

    margin:35px 0;
}

/* EXPANDER PERSONALIZADO */
.streamlit-expanderHeader {
    background: rgba(99,102,241,0.1) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    color: #c4b5fd !important;
    font-weight: 600 !important;
}

.streamlit-expanderContent {
    background: rgba(15,23,42,0.5) !important;
    border-radius: 0 0 12px 12px !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    padding: 15px !important;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:
    st.markdown("# 🤖 PROFEBOT")
    vista = st.radio("Seleccioná una vista", ["💬 Chat", "📊 Dashboard"])
    st.markdown("---")

    if vista == "💬 Chat":
        with st.expander("🔧 ¿Qué herramientas usa?", expanded=False):
            st.markdown("""
            **🎤 Whisper**  
            Es el *oído* del asistente. Convierte tu voz en texto.
                        
            **🧠 spaCy**  
            Es el *cerebro lingüístico*. Encuentra nombres, lugares y palabras clave.
                        
            **🔍 TF-IDF**  
            Buscador inteligente que elige la información más relevante.
                        
            **📊 N-Gramas**  
            Predictor de palabras, como el sugeridor del teclado del celular.
                        
            **🔊 gTTS**  
            La *voz* del asistente, para que puedas escuchar las respuestas.
                        
            **🐍 Python**  
            El lenguaje con el que construimos todo el sistema.
            """)
        st.markdown("---")
        st.info("Asistente académico para Procesamiento del Lenguaje Natural y reconocimiento de voz.")
        if st.button("🗑️ Limpiar conversación"):
            st.session_state.chat = []
            st.session_state.feedback = {}
            limpiar_historial()
            st.session_state.historial_cargado = False
            st.rerun()
        st.markdown("---")
        if st.session_state.chat:
            chat_texto = ""
            for rol, mensaje, hora in st.session_state.chat:
                if rol == "Usuario":
                    chat_texto += f"🧑 Usuario ({hora}): {mensaje}\n"
                else:
                    chat_texto += f"🤖 ProfeBot ({hora}): {mensaje}\n"
                chat_texto += "-" * 40 + "\n"
            st.download_button(
                label="📥 Descargar conversación (TXT)",
                data=chat_texto,
                file_name=f"conversacion_profebot_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )

# =====================================================
# VISTA CHAT
# =====================================================

if vista == "💬 Chat":

    # MODELO N-GRAMAS
    @st.cache_resource
    def cargar_modelo():
        if not os.path.exists("data/corpus.txt"):
            st.error("❌ No se encontró el archivo data/corpus.txt.")
            return None
        try:
            with open("data/corpus.txt", "r", encoding="utf-8") as f:
                corpus = f.readlines()
            modelo = ModeloNgramas(n=2, k=0.1)
            modelo.entrenar(corpus)
            return modelo
        except Exception as e:
            st.error(f"❌ Error al cargar el modelo: {e}")
            return None

    modelo_ng = cargar_modelo()

    # HEADER
    st.markdown("""
    <h1 class="main-title">🤖 PROFEBOT</h1>
    <p class="subtitle">
    Asistente Inteligente de Procesamiento del Lenguaje Natural y Reconocimiento de Voz
    </p>
    """, unsafe_allow_html=True)

    # RESPUESTA
    def generar_respuesta(texto, resultados):
        texto = texto.lower()
        if "tf idf" in texto or "tf-idf" in texto:
            return "TF-IDF mide la importancia de una palabra respecto a otros documentos."
        if "tf" in texto:
            return "TF representa la frecuencia de aparición de una palabra."
        if "perplejidad" in texto:
            return "La perplejidad mide qué tan bien un modelo predice una secuencia."
        if "n-grama" in texto:
            return "Un N-Grama es una secuencia de palabras utilizada en modelos de lenguaje."
        for r, score in resultados:
            if not r.strip().startswith("#"):
                return r.strip()
        return "No encontré una respuesta clara."

    # INPUT ALINEADO
    st.markdown("## 💬 Consulta")

    col1, col2 = st.columns([8, 1], vertical_alignment="center")

    with col1:
        texto_input = st.text_input(
            "",
            placeholder="Escribí tu pregunta...",
            label_visibility="collapsed",
            key="input_texto"
        )

    with col2:
        hablar_btn = st.button("🎤", use_container_width=True)

    # MICROFONO
    if hablar_btn:
        with st.spinner("🎙️ Escuchando..."):
            try:
                audio_path = grabar_audio()
                if audio_path and os.path.exists(audio_path):
                    texto_input = transcribir(audio_path)
                    st.success(f"Texto detectado: {texto_input}")
                    st.session_state.ultimo_audio = audio_path
                    os.remove(audio_path)
                else:
                    st.error("No se pudo grabar el audio. Verificá el micrófono.")
            except Exception as e:
                st.error(f"Error al grabar o transcribir: {e}")

    # PROCESAMIENTO
    if texto_input and not st.session_state.procesando:
        if texto_input == st.session_state.ultimo_texto_procesado:
            st.stop()

        st.session_state.procesando = True
        st.session_state.ultimo_texto_procesado = texto_input

        with st.status("🧠 Procesando tu consulta...", expanded=True) as status:
            try:
                inicio = time.time()

                status.update(label="🔎 Buscando información...")
                resultados = buscar(texto_input)

                status.update(label="💡 Generando respuesta...")
                respuesta = generar_respuesta(texto_input, resultados)

                status.update(label="📊 Analizando texto...")
                data = procesar(texto_input)

                status.update(label="📈 Calculando métricas...")
                pp = modelo_ng.perplejidad(texto_input) if modelo_ng else None

                fin = time.time()
                tiempo_ms = round((fin - inicio) * 1000, 1)

                # Tokens
                tokens = tokenizar(texto_input)
                cant_tokens = len(tokens)
                tokens_preview = " ".join(tokens[:5]) + ("..." if len(tokens) > 5 else "")

                score_max = max([s for _, s in resultados]) if resultados else 0
                hora = datetime.now().strftime("%H:%M")

                st.session_state.chat.append(("Usuario", texto_input, hora))
                st.session_state.chat.append(("Bot", respuesta, hora))

                # GUARDAR EN BASE DE DATOS
                entidades_data = data.get("entidades", []) if isinstance(data, dict) else []
                path_audio = st.session_state.get("ultimo_audio")
                datos_consulta = {
                    "estudiante_id": st.session_state.estudiante,
                    "audio_path": path_audio,
                    "texto_transcripto": texto_input,
                    "texto_original": texto_input,
                    "concepto_detectado": ", ".join([ent[0] for ent in entidades_data]) if entidades_data else None,
                    "intencion": None,
                    "seccion_resultado_id": None,
                    "similitud_coseno": score_max,
                    "pp": pp,
                    "wer": None,
                    "tiempo_ms": tiempo_ms,
                    "respuesta": respuesta,
                    "feedback": None
                }
                guardar_consulta(datos_consulta)

                status.update(label="✅ ¡Listo!", state="complete", expanded=False)

            except Exception as e:
                status.update(label="❌ Error en el procesamiento", state="error")
                st.error(f"Ocurrió un error: {e}")
            finally:
                st.session_state.procesando = False

        # TTS y respuesta visual
        try:
            audio_data = hablar(respuesta)
            if audio_data:
                st.audio(audio_data, format='audio/mp3')
        except Exception as e:
            st.warning(f"⚠️ No se pudo generar el audio: {e}")

        st.markdown("## 🤖 Respuesta")
        st.markdown(f"""
        <div class="response-card">
        <b>🤖 ProfeBot • {hora}</b>
        <div style="margin-top:12px; line-height:1.7; font-size:17px;">
        {respuesta}
        </div>
        </div>
        """, unsafe_allow_html=True)

        # Análisis
        st.markdown("## 📊 Análisis")
        c1, c2, c3 = st.columns(3)

        with c1:
            entidades = data.get("entidades", []) if isinstance(data, dict) else []
            entidades_html = ""
            if isinstance(entidades, list) and len(entidades) > 0:
                for ent in entidades:
                    if isinstance(ent, (tuple, list)) and len(ent) >= 2:
                        entidades_html += f'<div class="entity-badge">{ent[0]} • {ent[1]}</div>'
                    elif isinstance(ent, str):
                        entidades_html += f'<div class="entity-badge">{ent}</div>'
                    else:
                        entidades_html += f'<div class="entity-badge">{str(ent)}</div>'
            elif isinstance(entidades, str) and entidades.strip():
                entidades_html = f'<div class="entity-badge">{entidades}</div>'
            else:
                entidades_html = '<div class="soft-text">No se detectaron entidades en el texto.</div>'
            st.markdown(f"""
            <div class="metric-card">
            <div class="metric-icon">🧠</div>
            <div class="metric-title">Entidades</div>
            <div>{entidades_html}</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            pp_texto = f"{round(pp, 2)}" if pp is not None else "N/A"
            st.markdown(f"""
            <div class="metric-card">
            <div class="metric-icon">📈</div>
            <div class="metric-title">Perplejidad</div>
            <div class="big-number">{pp_texto}</div>
            <div class="soft-text">Menor valor = mejor predicción</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="metric-card">
            <div class="metric-icon">⚡</div>
            <div class="metric-title">Rendimiento</div>
            <div style="color: #e2e8f0; font-size: 1.1rem; margin-top: 20px;">
                ⏱️ {tiempo_ms} ms<br>
                🧮 {cant_tokens} tokens<br>
                🎯 score máx: {score_max:.2f}
            </div>
            <div class="soft-text" style="margin-top:15px;">Tokens: {tokens_preview}</div>
            </div>
            """, unsafe_allow_html=True)

    # HISTORIAL
    if st.session_state.chat:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("## 💬 Historial")

        for i in range(0, len(st.session_state.chat), 2):
            if i+1 < len(st.session_state.chat):
                usr, usr_msg, usr_hora = st.session_state.chat[i]
                bot, bot_msg, bot_hora = st.session_state.chat[i+1]

                st.markdown(f"""
                <div class="user-message">
                <b>🧑 Usuario • {usr_hora}</b>
                <div style="margin-top:8px;">{usr_msg}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="bot-message">
                <b>🤖 ProfeBot • {bot_hora}</b>
                <div style="margin-top:8px;">{bot_msg}</div>
                </div>
                """, unsafe_allow_html=True)

    # FOOTER
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="
    text-align:center;
    color:#64748b;
    padding-bottom:30px;
    line-height:1.8;
    ">

    <b>Instituto de Formación Docente y Técnica N°57 – Chascomús</b>
    <br>
    Ciencia de Datos e Inteligencia Artificial
    <br>
    Técnicas de Procesamiento del Habla — Trayecto F
    <br><br>
    🚀 Grupo 4 — PROFEBOT

    </div>
    """, unsafe_allow_html=True)

# =====================================================
# VISTA DASHBOARD
# =====================================================

elif vista == "📊 Dashboard":
    import plotly.express as px
    import pandas as pd
    from modules.db import obtener_estadisticas_dashboard

    st.markdown("## 📊 Dashboard Docente")
    st.markdown("---")

    try:
        stats = obtener_estadisticas_dashboard()
    except Exception as e:
        st.error(f"Error al cargar métricas: {e}")
        stats = None

    if stats is None or stats['total_consultas'] == 0:
        st.info("ℹ️ No hay datos todavía. Realizá algunas consultas en la vista 💬 Chat para ver estadísticas.")
    else:
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
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
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