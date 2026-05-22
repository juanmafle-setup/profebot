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
from modules.evaluacion import detectar_intencion
from modules.tts import hablar
from modules.ngrams import ModeloNgramas
from modules.nlp import procesar
from modules.mic import grabar_audio
from modules.db import crear_tablas, guardar_consulta, obtener_historial, limpiar_historial
from modules.config import cargar_config

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
    vista = st.radio("Seleccioná una vista", ["💬 Chat", "🧩 Quiz", "📊 Dashboard"])
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
        k_valor = st.slider(
            "⚙️ Suavizado Add-k",
            min_value=0.01, max_value=1.0, value=0.1, step=0.01,
            help="Controla el suavizado del modelo de N-gramas. k=0.01 confía más en el corpus; k=1.0 es el suavizado de Laplace clásico."
        )
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
    else:
        k_valor = 0.1  # valor por defecto fuera del chat

# =====================================================
# VISTA CHAT
# =====================================================

if vista == "💬 Chat":

    # MODELO N-GRAMAS (se recarga si cambia k)
    @st.cache_resource
    def cargar_modelo(k=0.1):
        if not os.path.exists("data/corpus.txt"):
            return None
        try:
            with open("data/corpus.txt", "r", encoding="utf-8") as f:
                corpus = [l for l in f.readlines() if l.strip() and not l.strip().startswith("#")]
            modelo = ModeloNgramas(n=2, k=k)
            modelo.entrenar(corpus)
            return modelo
        except Exception as e:
            return None

    modelo_ng = cargar_modelo(k=k_valor)

    # HEADER
    st.markdown("""
    <h1 class="main-title">🤖 PROFEBOT</h1>
    <p class="subtitle">
    Asistente Inteligente de Procesamiento del Lenguaje Natural y Reconocimiento de Voz
    </p>
    """, unsafe_allow_html=True)

    # ── EXTRACCIÓN DE TÉRMINO CLAVE ─────────────────────────────────
    # Palabras que se eliminan para quedarse con el concepto central de la pregunta.
    _SW_EXTRACCION = {
        "que", "qué", "como", "cómo", "cual", "cuál", "cuales", "cuáles",
        "donde", "dónde", "cuando", "cuándo", "por", "con", "entre",
        "es", "son", "un", "una", "el", "la", "los", "las", "del", "de",
        "al", "en", "para", "a", "ante", "sobre",
        "mide", "hace", "sirve", "calcula", "obtiene", "representa",
        "indica", "define", "significa", "funciona", "refiere",
        "evalua", "expresa", "determina",
        "se", "y", "o", "e", "u", "ni",
    }

    def _extraer_termino(query):
        """Extrae el concepto clave de la pregunta quitando stopwords de intención."""
        q = re.sub(r'[¿?¡!.,;:]', '', query.lower()).strip()
        tokens = [t for t in q.split() if t not in _SW_EXTRACCION and len(t) > 2]
        return " ".join(tokens[:3])   # máximo 3 palabras clave

    # ── BONUS DIRECTO: {término}: / {término} {verbo} ────────────────
    # Verbos que indican que la oración responde directamente la intención.
    _VERBOS_DIRECTOS = {
        "DEFINICION":       ["es ", "son ", "mide ", "indica ", "consiste",
                             "se define", "evalua ", "expresa ", "representa "],
        "CALCULO":          ["se calcula", "es igual", "se obtiene", "formula"],
        "APLICACION":       ["sirve para", "se usa", "permite ", "se aplica", "se utiliza"],
        "COMPARACION":      ["a diferencia", "mientras que"],
        "EJEMPLO":          ["por ejemplo", "como ejemplo"],
        "CONSULTA_GENERAL": [],
    }

    # Palabras que indican inicio de pregunta Q&A (el corpus usa este formato)
    _QA_INICIO = {"que", "qué", "como", "cómo", "para", "cual", "cuál",
                  "cuales", "cuáles", "donde", "dónde", "por", "cuando", "cuándo"}

    def _bonus_directo(termino, doc, intencion):
        """
        Devuelve un bonus grande si la oración es una respuesta directa al término.

        Lógica Q&A (bonus 0.5): el fragmento antes del ':' tiene ≤10 palabras,
        EMPIEZA con palabra interrogativa (que/como/para/…) y contiene el término.
        La comparación se normaliza (sin guiones/espacios) para igualar
        'tfidf' con 'tf-idf' o 'similitud coseno' con 'similitud del coseno'.
        Evita falsos positivos como 'El WER considera tres tipos de errores:'.

        Lógica sujeto-verbo (bonus 0.4): doc contiene '{término} {verbo_intención}'
        (ej: 'La perplejidad mide que tan bien...').
        """
        if not termino or len(termino) < 3:
            return 0.0
        doc_l  = doc.lower()
        _n     = lambda s: re.sub(r'[-\s]', '', s)
        term_n = _n(termino)

        # Formato Q&A real (empieza con palabra interrogativa)
        if ':' in doc_l:
            pregunta = doc_l.split(':')[0]
            pwords   = pregunta.split()
            if (len(pwords) <= 10
                    and pwords                          # no vacío
                    and pwords[0] in _QA_INICIO):      # empieza con interrogativa
                preg_n    = _n(pregunta)
                pwords_set = set(pwords)               # palabras exactas (evita substring)
                tokens_ok = all(t in pwords_set for t in termino.split())
                norm_ok   = len(term_n) >= 3 and term_n in preg_n
                if tokens_ok or norm_ok:
                    return 0.5

        # Sujeto-verbo directo
        verbos = _VERBOS_DIRECTOS.get(intencion, [])
        for verbo in verbos:
            if f"{termino} {verbo.strip()}" in doc_l:
                return 0.4
        return 0.0

    # ── PATRONES SECUNDARIOS DE INTENCIÓN ───────────────────────────
    # Bonus pequeño (×0.08): no reemplaza TF-IDF, solo desempata.
    _PATRONES_INTENCION = {
        "DEFINICION":       ["es ", "son ", "se define", "significa ",
                             "consiste en", "se refiere", "se denomina",
                             "se conoce como", "es un ", "es una "],
        "CALCULO":          ["se calcula", "formula", "dividiendo", "multiplicando",
                             "se obtiene", "es igual", "la ecuacion", "el valor de"],
        "APLICACION":       ["se usa", "sirve para", "permite ", "se aplica",
                             "se utiliza", "ayuda a", "facilita"],
        "COMPARACION":      ["diferencia", "mientras que", "a diferencia", "en cambio",
                             "mayor que", "menor que", "en contraste"],
        "EJEMPLO":          ["por ejemplo", "como ejemplo", "supongamos", "considera"],
        "CONSULTA_GENERAL": [],
    }
    _BONUS_INTENCION_PESO = 0.08   # techo: +0.08 por patrón encontrado

    # ── RESPUESTA INTELIGENTE ────────────────────────────────────────
    def generar_respuesta(resultados, intencion="CONSULTA_GENERAL",
                          num_resultados=1, query=""):
        """
        Tres capas de puntuación (sin aprendizaje en línea):
          1. TF-IDF score  — relevancia temática (dominante)
          2. Bonus directo — +0.4/0.5 si la oración responde exactamente {término} + verbo
          3. Bonus intención — +0.08 × patrones léxicos de la intención

        La suma garantiza que TF-IDF siga siendo el factor principal.
        El bonus directo identifica oraciones Q&A o sujeto-verbo precisas.
        """
        candidatos = [(r.strip(), s) for r, s in resultados if s >= UMBRAL_SIMILITUD]
        if not candidatos:
            return "No encontré información sobre ese tema en el corpus. Intentá reformular la pregunta."

        termino   = _extraer_termino(query)
        patrones  = _PATRONES_INTENCION.get(intencion, [])

        def score_total(doc, tfidf):
            b_directo  = _bonus_directo(termino, doc, intencion)
            b_intencion = sum(1 for p in patrones if p in doc.lower()) * _BONUS_INTENCION_PESO
            return tfidf + b_directo + b_intencion

        candidatos_reranked = sorted(
            candidatos,
            key=lambda x: score_total(x[0], x[1]),
            reverse=True
        )

        # Filtro de coherencia: 2ª y 3ª oración solo si TF-IDF ≥ 55% del top
        top_tfidf = candidatos_reranked[0][1]
        umbral_coherencia = top_tfidf * 0.55

        seleccionados = []
        for doc, tfidf in candidatos_reranked:
            if len(seleccionados) == 0:
                seleccionados.append(doc)
            elif tfidf >= umbral_coherencia:
                seleccionados.append(doc)
            if len(seleccionados) >= num_resultados:
                break

        return " ".join(seleccionados)

    # INPUT ALINEADO
    st.markdown("## 💬 Consulta")

    _cfg_entrada = cargar_config()
    _modo_entrada = _cfg_entrada.get("modo_entrada", "ambos")

    col1, col2 = st.columns([8, 1], vertical_alignment="center")

    with col1:
        texto_input = st.text_input(
            "",
            placeholder="Escribí tu pregunta...",
            label_visibility="collapsed",
            key="input_texto",
            disabled=(_modo_entrada == "audio"),
        )

    with col2:
        hablar_btn = st.button(
            "🎤",
            use_container_width=True,
            disabled=(_modo_entrada == "texto"),
            help="Deshabilitado: modo entrada = solo texto" if _modo_entrada == "texto" else "Grabar audio",
        )

    # AUTOCOMPLETADO CON N-GRAMAS
    if texto_input and modelo_ng:
        tokens = texto_input.lower().split()
        if tokens:
            sugerencias_auto = modelo_ng.sugerir([tokens[-1]], top_n=5)
            stopwords_auto = {"de", "la", "el", "en", "y", "a", "con", "que", "es", "un", "una"}
            sugerencias_limpias = [p for p, _ in sugerencias_auto if p not in stopwords_auto][:4]
            if sugerencias_limpias:
                st.caption("💡 **Autocompletado:** " + "  ·  ".join(f"`{p}`" for p in sugerencias_limpias))

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

                # Leer config actual (sin cachear, para reflejar cambios del dashboard)
                _cfg = cargar_config()
                _num_res = _cfg.get("num_resultados", 1)
                _modo_salida = _cfg.get("modo_salida", "ambos")

                status.update(label="🔎 Buscando información...")
                resultados = buscar(texto_input)

                status.update(label="🎯 Detectando intención...")
                intencion = detectar_intencion(texto_input)

                status.update(label="💡 Generando respuesta...")
                respuesta = generar_respuesta(resultados, intencion=intencion,
                                              num_resultados=_num_res, query=texto_input)

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
                    "intencion": intencion,
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

        # TTS y respuesta visual (respeta modo_salida de config)
        _cfg_out = cargar_config()
        _modo_salida_out = _cfg_out.get("modo_salida", "ambos")
        if _modo_salida_out in ("audio", "ambos"):
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
                🎯 score máx: {score_max:.2f}<br>
                ⚙️ k = {k_valor}
            </div>
            <div class="soft-text" style="margin-top:15px;">Tokens: {tokens_preview}</div>
            </div>
            """, unsafe_allow_html=True)

        # TABLA DE N-GRAMAS
        if modelo_ng:
            st.markdown("### 📊 Top-10 continuaciones del modelo de N-gramas")
            tokens_ngrama = texto_input.lower().split()
            contexto_ng = [tokens_ngrama[-1]] if tokens_ngrama else ["<s>"]
            sugerencias_ng = modelo_ng.sugerir(contexto_ng, top_n=10)
            import pandas as _pd
            df_ng = _pd.DataFrame(
                [(p, round(prob, 6)) for p, prob in sugerencias_ng],
                columns=["Palabra siguiente", "Probabilidad"]
            )
            st.dataframe(df_ng, use_container_width=True, hide_index=True)

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
# VISTA QUIZ
# =====================================================

elif vista == "🧩 Quiz":
    import random

    st.markdown("""
    <h1 class="main-title">🧩 Quiz de Repaso</h1>
    <p class="subtitle">Completá la oración con la palabra que falta</p>
    """, unsafe_allow_html=True)

    # Inicializar estado del quiz
    for key, val in [("quiz_oracion", None), ("quiz_palabra", None),
                     ("quiz_mostrar", False), ("quiz_correctas", 0), ("quiz_total", 0)]:
        if key not in st.session_state:
            st.session_state[key] = val

    STOPWORDS_QUIZ = {"de", "la", "el", "en", "y", "a", "con", "que", "es",
                      "un", "una", "los", "las", "por", "para", "se", "del",
                      "al", "su", "como", "si", "no", "o", "e", "u"}

    def nueva_pregunta():
        with open("data/corpus.txt", "r", encoding="utf-8") as f:
            lineas = [l.strip() for l in f
                      if l.strip() and not l.strip().startswith("#")
                      and len(l.strip().split()) >= 7]
        linea = random.choice(lineas)
        palabras = linea.split()
        candidatos = [
            (i, p) for i, p in enumerate(palabras)
            if p.lower().rstrip(".,;:") not in STOPWORDS_QUIZ and len(p) > 3
        ]
        if not candidatos:
            nueva_pregunta()
            return
        idx, correcta = random.choice(candidatos)
        palabras[idx] = "___"
        st.session_state.quiz_oracion  = " ".join(palabras)
        st.session_state.quiz_palabra  = correcta.lower().rstrip(".,;:")
        st.session_state.quiz_mostrar  = False

    col_btn, col_score = st.columns([2, 1])
    with col_btn:
        if st.button("🎲 Nueva pregunta", use_container_width=True):
            nueva_pregunta()
    with col_score:
        c = st.session_state.quiz_correctas
        t = st.session_state.quiz_total
        pct = f"{c/t:.0%}" if t > 0 else "—"
        st.metric("Puntaje", f"{c} / {t}", pct)

    if st.session_state.quiz_oracion is None:
        nueva_pregunta()

    st.markdown("---")
    st.markdown("**Completá la oración:**")
    st.markdown(
        f"<div style='font-size:1.2rem; padding:16px; background:#1e293b; border-radius:10px; "
        f"color:#e2e8f0; line-height:2;'>{st.session_state.quiz_oracion}</div>",
        unsafe_allow_html=True
    )
    st.markdown("")

    respuesta_quiz = st.text_input("✏️ Tu respuesta:", key="quiz_input",
                                   placeholder="Escribí la palabra que falta...")

    if st.button("✅ Verificar", use_container_width=True):
        st.session_state.quiz_total += 1
        st.session_state.quiz_mostrar = True
        correcta = st.session_state.quiz_palabra
        usuario  = respuesta_quiz.lower().strip().rstrip(".,;:")

        if usuario == correcta:
            st.session_state.quiz_correctas += 1
            st.success(f"✅ ¡Correcto! La palabra era: **{correcta}**")
        elif correcta.startswith(usuario) or usuario.startswith(correcta):
            st.session_state.quiz_correctas += 1
            st.warning(f"⚠️ ¡Muy cerca! La palabra exacta es: **{correcta}**")
        else:
            st.error(f"❌ Incorrecto. La respuesta correcta era: **{correcta}**")

        # Mostrar la oración completa
        oracion_completa = st.session_state.quiz_oracion.replace("___", f"**{correcta}**")
        st.markdown(f"📖 Oración completa: *{oracion_completa}*")

    st.markdown("---")
    if st.button("🔄 Reiniciar puntaje"):
        st.session_state.quiz_correctas = 0
        st.session_state.quiz_total = 0
        st.rerun()

# =====================================================
# VISTA DASHBOARD
# =====================================================

elif vista == "📊 Dashboard":
    from dashboard import mostrar_dashboard
    mostrar_dashboard()