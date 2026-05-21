import streamlit as st
import os
import time
from datetime import datetime
import re

def tokenizar(texto):
    """Devuelve una lista de tokens (palabras y signos de puntuación por separado)."""
    return re.findall(r'\w+|[^\w\s]', texto)

from modules.asr import transcribir
from modules.search import buscar, hay_respuesta, UMBRAL_SIMILITUD
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

# Cargar estilos desde archivo externo
with open("styles.css", "r", encoding="utf-8") as f:
    css = f.read()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

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
                corpus = [l for l in f.readlines() if l.strip() and not l.strip().startswith("#")]
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
    def generar_respuesta(resultados):
        for r, score in resultados:
            if score >= UMBRAL_SIMILITUD:
                return r.strip()
        return "No encontré información sobre ese tema en el corpus. Intentá reformular la pregunta."

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
                respuesta = generar_respuesta(resultados)

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
    from dashboard import mostrar_dashboard
    mostrar_dashboard()