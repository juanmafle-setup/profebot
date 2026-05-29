import html as _html
import streamlit as st
import os
import random
import time
from datetime import datetime
import re
import pandas as pd


def tokenizar(texto):
    """Devuelve una lista de tokens (palabras y signos de puntuación por separado)."""
    return re.findall(r'\w+|[^\w\s]', texto)


from modules.asr import transcribir
from modules.search import buscar, UMBRAL_SIMILITUD
from modules.evaluacion import detectar_intencion, similitud_respuesta_quiz
from modules.tts import hablar
from modules.ngrams import ModeloNgramas
from modules.nlp import procesar
from modules.mic import grabar_audio
from modules.db import (crear_tablas, guardar_consulta, obtener_historial,
                         limpiar_historial, guardar_resultado_quiz)
from modules.config import cargar_config


# ── CONSTANTES DE MODELO N-GRAMAS ──────────────────────────────────────────
# Definidas a nivel de módulo: se crean una vez y no se recrean en cada rerun.

_MODOS_K = {
    "📄 Tal cual el corpus":      0.01,
    "⚖️ Equilibrado":             0.1,
    "🤖 Formulado por el agente": 1.0,
}
# Etiqueta corta para el panel de análisis, derivada de la clave del dict.
_MODOS_LABEL = {
    "📄 Tal cual el corpus":      "Corpus",
    "⚖️ Equilibrado":             "Equilibrado",
    "🤖 Formulado por el agente": "Agente",
}
# Nombre interno del modo de respuesta para cada opción del radio.
_MODOS_RESP = {
    "📄 Tal cual el corpus":      "corpus",
    "⚖️ Equilibrado":             "equilibrado",
    "🤖 Formulado por el agente": "agente",
}


# ── CONSTANTES DE BÚSQUEDA / RESPUESTA ─────────────────────────────────────

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

# Palabras que indican inicio de pregunta Q&A (el corpus usa este formato).
_QA_INICIO = {"que", "qué", "como", "cómo", "para", "cual", "cuál",
              "cuales", "cuáles", "donde", "dónde", "por", "cuando", "cuándo"}

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
_BONUS_INTENCION_PESO = 0.08

# Stopwords que el autocompletado filtra de las sugerencias.
_STOPWORDS_AUTO = {"de", "la", "el", "en", "y", "a", "con", "que", "es", "un", "una"}

# Stopwords que el quiz ignora al elegir la palabra a ocultar.
_STOPWORDS_QUIZ = {"de", "la", "el", "en", "y", "a", "con", "que", "es",
                   "un", "una", "los", "las", "por", "para", "se", "del",
                   "al", "su", "como", "si", "no", "o", "e", "u"}


def _extraer_palabra_quiz(texto):
    """
    Extrae la palabra más probable de una transcripción de voz para el quiz.

    Toma el ÚLTIMO token significativo (no stopword, longitud > 3) porque cuando
    el usuario dice 'creo que es perplejidad', la respuesta viene al final.
    Si no hay candidatos, devuelve la última palabra de la transcripción.
    """
    texto_limpio = re.sub(r'[^a-záéíóúñü\s]', '', texto.lower()).strip()
    tokens = texto_limpio.split()
    candidatos = [t for t in tokens if t not in _STOPWORDS_QUIZ and len(t) > 3]
    if candidatos:
        return candidatos[-1]
    return tokens[-1] if tokens else ""


# ── FUNCIONES DE BÚSQUEDA / RESPUESTA ──────────────────────────────────────

def _extraer_termino(query):
    """Extrae el concepto clave de la pregunta quitando stopwords de intención."""
    q = re.sub(r'[¿?¡!.,;:]', '', query.lower()).strip()
    tokens = [t for t in q.split() if t not in _SW_EXTRACCION and len(t) > 2]
    return " ".join(tokens[:3])   # máximo 3 palabras clave


def _bonus_directo(termino, doc, intencion, term_n):
    """
    Devuelve un bonus grande si la oración es una respuesta directa al término.

    Lógica Q&A (bonus 0.5): el fragmento antes del ':' tiene ≤10 palabras,
    EMPIEZA con palabra interrogativa (que/como/para/…) y contiene el término.
    La comparación se normaliza (sin guiones/espacios) para igualar
    'tfidf' con 'tf-idf' o 'similitud coseno' con 'similitud del coseno'.
    Evita falsos positivos como 'El WER considera tres tipos de errores:'.

    Lógica sujeto-verbo (bonus 0.4): doc contiene '{término} {verbo_intención}'
    (ej: 'La perplejidad mide que tan bien...').

    term_n: versión normalizada del término (sin guiones/espacios), pre-computada
            en generar_respuesta() para evitar recalcular por cada documento.
    """
    if not termino or len(termino) < 3:
        return 0.0
    doc_l = doc.lower()

    # Formato Q&A real (empieza con palabra interrogativa)
    if ':' in doc_l:
        pregunta = doc_l.split(':')[0]
        pwords   = pregunta.split()
        if (len(pwords) <= 10
                and pwords
                and pwords[0] in _QA_INICIO):
            preg_n     = re.sub(r'[-\s]', '', pregunta)
            pwords_set = set(pwords)              # exacto, evita coincidencias de substring
            tokens_ok  = all(t in pwords_set for t in termino.split())
            norm_ok    = len(term_n) >= 3 and term_n in preg_n
            if tokens_ok or norm_ok:
                return 0.5

    # Sujeto-verbo directo
    for verbo in _VERBOS_DIRECTOS.get(intencion, []):
        if f"{termino} {verbo.strip()}" in doc_l:
            return 0.4
    return 0.0


def _quitar_prefijo(doc):
    """
    Quita el prefijo Q&A antes de mostrar la respuesta.
    'Que es un bigrama: es un par...' → 'Es un par...'
    Solo actúa si la parte antes del ':' tiene ≤8 palabras y empieza
    con palabra interrogativa, para no tocar frases normales con ':'.
    """
    if ':' not in doc:
        return doc
    pre, _, resto = doc.partition(':')
    if len(pre.split()) <= 8 and pre.split() and pre.split()[0].lower() in _QA_INICIO:
        resto = resto.strip()
        return resto[0].upper() + resto[1:] if resto else doc
    return doc


def _continuar_ngramas(texto_base, modelo_ng, max_palabras=8):
    """
    Extiende texto_base con hasta max_palabras nuevas generadas por el modelo de n-gramas.
    Usa 8 palabras por defecto: suficiente para mostrar la predicción del modelo sin que
    los bigrams pierdan coherencia (con 20 el texto se vuelve incoherente rápidamente).

    Limpia el texto igual que el corpus (sin puntuación) para que los tokens coincidan
    con el vocabulario entrenado.  Detecta ciclos con un set de palabras visitadas.
    Retorna texto_base sin cambios si no hay continuaciones disponibles.
    """
    if not modelo_ng or not texto_base.strip():
        return texto_base

    clean    = re.sub(r'[^\w\sáéíóúñü]', '', texto_base.lower()).strip()
    tokens   = clean.split()
    if not tokens:
        return texto_base

    contexto  = [tokens[-1]]
    extension = []
    visitados = set(tokens[-3:])  # bloquea las últimas 3 palabras del ancla

    for _ in range(max_palabras):
        sugerencias = modelo_ng.sugerir(contexto, top_n=8)
        candidatos  = [
            (p, prob) for p, prob in sugerencias
            if p not in {"</s>", "<s>"} and p not in visitados
        ]
        if not candidatos:
            break
        siguiente = candidatos[0][0]
        extension.append(siguiente)
        visitados.add(siguiente)
        contexto = [siguiente]

    if not extension:
        return ""   # señal: no hay extensión disponible

    ext_text = " ".join(extension)
    base     = texto_base.rstrip(" .")
    return f"{base} {ext_text}."


def _generar_desde_concepto(termino, modelo_ng, max_palabras=15):
    """
    Genera texto partiendo del concepto clave cuando _continuar_ngramas no puede
    extender la respuesta (la última palabra no tiene continuaciones en el corpus).

    Arranca desde el último token del término (ej: 'wer' → 'wer es una metrica…')
    y genera una oración usando el modelo de n-gramas de forma greedy.
    """
    if not modelo_ng or not termino:
        return None

    tokens    = re.sub(r'[^\w\sáéíóúñü]', '', termino.lower()).split()
    if not tokens:
        return None

    contexto  = [tokens[-1]]
    generado  = list(tokens)
    visitados = set(tokens)

    for _ in range(max_palabras):
        sugerencias = modelo_ng.sugerir(contexto, top_n=8)
        candidatos  = [
            (p, prob) for p, prob in sugerencias
            if p not in {"</s>", "<s>"} and p not in visitados
        ]
        if not candidatos:
            break
        siguiente = candidatos[0][0]
        generado.append(siguiente)
        visitados.add(siguiente)
        contexto = [siguiente]

    if len(generado) <= len(tokens):
        return None   # no se generó nada nuevo

    result = " ".join(generado)
    return result[0].upper() + result[1:] + "."


def generar_respuesta(resultados, intencion="CONSULTA_GENERAL",
                      num_resultados=1, query="",
                      modo="equilibrado", modelo_ng=None):
    """
    Genera la respuesta según el modo seleccionado (sin aprendizaje en línea):

    'corpus'      — devuelve la línea del corpus tal cual, sin ningún procesamiento.
                    Muestra exactamente lo que está guardado en el corpus.

    'equilibrado' — TF-IDF + intent re-ranking + limpieza de prefijos Q&A + unión
                    de hasta num_resultados oraciones coherentes.

    'agente'      — igual que 'equilibrado' para obtener el ancla temática,
                    luego el modelo de n-gramas extiende la respuesta generando
                    hasta 20 palabras adicionales a partir del último token.
                    El modelo es estático: no aprende de las consultas.
    """
    candidatos = [(r.strip(), s) for r, s in resultados if s >= UMBRAL_SIMILITUD]
    if not candidatos:
        return "No encontré información sobre ese tema en el corpus. Intentá reformular la pregunta."

    # ── MODO 1: tal cual el corpus ───────────────────────────────────────────
    # Siempre devuelve las 3 líneas con mayor similitud TF-IDF, sin ningún
    # procesamiento: con prefijo Q&A si lo tienen, sin limpiar, sin re-rankear.
    # Así el resultado SIEMPRE es visiblemente distinto del modo Equilibrado.
    if modo == "corpus":
        top3 = [doc for doc, _ in candidatos[:3]]
        return "\n".join(f"{i + 1}. {doc}" for i, doc in enumerate(top3))

    # ── MODOS 2 y 3: recuperación inteligente ───────────────────────────────
    termino  = _extraer_termino(query)
    term_n   = re.sub(r'[-\s]', '', termino)   # pre-computado: evita recalcular por doc
    patrones = _PATRONES_INTENCION.get(intencion, [])

    def score_total(doc, tfidf):
        b_directo   = _bonus_directo(termino, doc, intencion, term_n)
        b_intencion = sum(1 for p in patrones if p in doc.lower()) * _BONUS_INTENCION_PESO
        return tfidf + b_directo + b_intencion

    candidatos_reranked = sorted(
        candidatos,
        key=lambda x: score_total(x[0], x[1]),
        reverse=True,
    )

    # Filtro de coherencia: 2ª y 3ª oración solo si TF-IDF ≥ 55 % del top.
    # En modo agente usamos solo 1 oración ancla para que la extensión sea limpia.
    n_sel             = 1 if modo == "agente" else num_resultados
    umbral_coherencia = candidatos_reranked[0][1] * 0.55

    seleccionados = []
    for doc, tfidf in candidatos_reranked:
        if len(seleccionados) == 0:
            seleccionados.append(doc)
        elif tfidf >= umbral_coherencia:
            seleccionados.append(doc)
        if len(seleccionados) >= n_sel:
            break

    limpios = [_quitar_prefijo(d) for d in seleccionados]
    base    = " ".join(limpios)

    # ── MODO 3: generación con n-gramas ─────────────────────────────────────
    # Intenta extender el final de la respuesta (8 palabras máx para mantener
    # coherencia con bigrams). Si la última palabra no tiene continuaciones en
    # el corpus, genera desde el concepto clave de la consulta como fallback.
    if modo == "agente":
        extendida = _continuar_ngramas(base, modelo_ng, max_palabras=8)
        if extendida:
            return extendida
        # Fallback: generar desde el concepto (ej: "wer es una metrica que…")
        desde_concepto = _generar_desde_concepto(termino, modelo_ng, max_palabras=15)
        return desde_concepto if desde_concepto else base

    return base


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
# CSS
# =====================================================


@st.cache_data
def _leer_css():
    with open("styles.css", "r", encoding="utf-8") as f:
        return f.read()


st.markdown(f"<style>{_leer_css()}</style>", unsafe_allow_html=True)

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
if "historial_cargado" not in st.session_state:
    st.session_state.historial_cargado = False
if "ultima_respuesta" not in st.session_state:
    st.session_state.ultima_respuesta = None

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

        # ── MODO DE SUAVIZADO (3 opciones fijas) ──────────────────
        # Radio en vez de slider → solo 3 modelos en cache, sin freeze al cambiar.
        _modo_sel = st.radio(
            "🧮 Suavizado N-gramas",
            options=list(_MODOS_K.keys()),
            index=1,           # Equilibrado por defecto
            help=(
                "**Tal cual el corpus** (k=0.01): el modelo confía casi exclusivamente en "
                "las frecuencias del corpus. Predicciones muy literales.\n\n"
                "**Equilibrado** (k=0.1): balance entre corpus y generalización. "
                "Recomendado para uso normal.\n\n"
                "**Formulado por el agente** (k=1.0): suavizado de Laplace clásico. "
                "Distribuye probabilidad más uniformemente, sugiriendo más variedad "
                "en el autocompletado. El agente no aprende de las interacciones."
            ),
        )
        k_valor    = _MODOS_K[_modo_sel]
        _modo_resp = _MODOS_RESP[_modo_sel]

        st.markdown("---")
        st.info("Asistente académico para Procesamiento del Lenguaje Natural y reconocimiento de voz.")
        if st.button("🗑️ Limpiar conversación"):
            st.session_state.chat = []
            st.session_state.feedback = {}
            st.session_state.ultima_respuesta = None
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
        k_valor    = 0.1          # valor por defecto fuera del chat
        _modo_resp = "equilibrado"

# =====================================================
# VISTA CHAT
# =====================================================

if vista == "💬 Chat":

    # MODELO N-GRAMAS (se recarga solo si cambia k, gracias a cache_resource)
    @st.cache_resource
    def cargar_modelo(k=0.1):
        if not os.path.exists("data/corpus.txt"):
            return None
        try:
            with open("data/corpus.txt", "r", encoding="utf-8") as f:
                corpus = [l for l in f.readlines()
                          if l.strip() and not l.strip().startswith("#")]
            modelo = ModeloNgramas(n=2, k=k)
            modelo.entrenar(corpus)
            return modelo
        except Exception:
            return None

    modelo_ng = cargar_modelo(k=k_valor)

    # HEADER
    st.markdown("""
    <h1 class="main-title">🤖 PROFEBOT</h1>
    <p class="subtitle">
    Asistente Inteligente de Procesamiento del Lenguaje Natural y Reconocimiento de Voz
    </p>
    """, unsafe_allow_html=True)

    # CONFIG — lectura única para todo el bloque Chat.
    # No se cachea para reflejar cambios hechos desde el Dashboard en el mismo rerun.
    _cfg          = cargar_config()
    _modo_entrada = _cfg.get("modo_entrada", "ambos")
    _num_res      = _cfg.get("num_resultados", 1)
    _modo_salida  = _cfg.get("modo_salida", "ambos")

    # INPUT — formulario (Enter o botón activan envío; radio NO lo hace)
    st.markdown("## 💬 Consulta")

    with st.form("consulta_form", clear_on_submit=False):
        col_inp, col_btn = st.columns([8, 2], vertical_alignment="bottom")
        with col_inp:
            texto_input = st.text_input(
                "",
                placeholder="Escribí tu pregunta y presioná Enter o Consultar...",
                label_visibility="collapsed",
                key="input_texto",
                disabled=(_modo_entrada == "audio"),
            )
        with col_btn:
            enviar_btn = st.form_submit_button(
                "Consultar →",
                use_container_width=True,
                disabled=(_modo_entrada == "audio"),
            )

    # Micrófono — visible solo si el config permite entrada de audio
    if _modo_entrada in ("audio", "ambos"):
        _col_mic, _ = st.columns([2, 8])
        with _col_mic:
            hablar_btn = st.button(
                "🎤 Grabar voz",
                use_container_width=True,
                help="Grabá tu pregunta con el micrófono",
            )
    else:
        hablar_btn = False

    # Autocompletado basado en el último texto enviado
    _texto_actual = st.session_state.get("input_texto", "")
    if _texto_actual and modelo_ng:
        _toks = _texto_actual.lower().split()
        if _toks:
            _sugg = modelo_ng.sugerir([_toks[-1]], top_n=5)
            _sugg_ok = [p for p, _ in _sugg if p not in _STOPWORDS_AUTO][:4]
            if _sugg_ok:
                st.caption("💡 **Autocompletado:** " + "  ·  ".join(f"`{p}`" for p in _sugg_ok))

    # FUNCIÓN DE PROCESAMIENTO
    # Recibe el texto a procesar. Usa k_valor/_modo_resp/modelo_ng del scope actual
    # (los que estaban seleccionados en el sidebar al momento de hacer click).
    def _procesar(texto_proc):
        hora = datetime.now().strftime("%H:%M")
        with st.status("🧠 Procesando tu consulta...", expanded=True) as status:
            try:
                inicio = time.time()

                status.update(label="🔎 Buscando información...")
                resultados = buscar(texto_proc)

                status.update(label="🎯 Detectando intención...")
                intencion = detectar_intencion(texto_proc)

                status.update(label="💡 Generando respuesta...")
                respuesta = generar_respuesta(
                    resultados, intencion=intencion,
                    num_resultados=_num_res, query=texto_proc,
                    modo=_modo_resp, modelo_ng=modelo_ng,
                )

                status.update(label="📊 Analizando texto...")
                data = procesar(texto_proc)

                status.update(label="📈 Calculando métricas...")
                pp = modelo_ng.perplejidad(texto_proc) if modelo_ng else None

                fin      = time.time()
                tiempo_ms = round((fin - inicio) * 1000, 1)
                hora     = datetime.now().strftime("%H:%M")

                tokens_list    = tokenizar(texto_proc)
                cant_tokens    = len(tokens_list)
                tokens_preview = " ".join(tokens_list[:5]) + ("..." if len(tokens_list) > 5 else "")
                score_max      = resultados[0][1] if resultados else 0.0

                tokens_ngrama  = texto_proc.lower().split()
                ctx_ng         = [tokens_ngrama[-1]] if tokens_ngrama else ["<s>"]
                sugerencias_ng = modelo_ng.sugerir(ctx_ng, top_n=10) if modelo_ng else []

                st.session_state.chat.append(("Usuario", texto_proc, hora))
                st.session_state.chat.append(("Bot", respuesta, hora))

                entidades_data = data.get("entidades", []) if isinstance(data, dict) else []
                guardar_consulta({
                    "estudiante_id":        st.session_state.estudiante,
                    "audio_path":           st.session_state.get("ultimo_audio"),
                    "texto_transcripto":    texto_proc,
                    "texto_original":       texto_proc,
                    "concepto_detectado":   ", ".join([e[0] for e in entidades_data]) if entidades_data else None,
                    "intencion":            intencion,
                    "seccion_resultado_id": None,
                    "similitud_coseno":     score_max,
                    "pp":                   pp,
                    "wer":                  None,
                    "tiempo_ms":            tiempo_ms,
                    "respuesta":            respuesta,
                    "feedback":             None,
                })

                # Top-3 fuentes relevantes para el panel de fragmentos
                fuentes = [
                    (doc.strip(), round(score, 4))
                    for doc, score in resultados[:3]
                    if score >= UMBRAL_SIMILITUD
                ]

                # Guardar resultado en session_state para que persista sin reprocesarse
                st.session_state.ultima_respuesta = {
                    "texto":          texto_proc,
                    "respuesta":      respuesta,
                    "hora":           hora,
                    "data":           data,
                    "pp":             pp,
                    "tiempo_ms":      tiempo_ms,
                    "cant_tokens":    cant_tokens,
                    "tokens_preview": tokens_preview,
                    "score_max":      score_max,
                    "k_valor":        k_valor,
                    "modo_label":     _MODOS_LABEL.get(_modo_sel, "—"),
                    "sugerencias_ng": sugerencias_ng,
                    "fuentes":        fuentes,
                }
                status.update(label="✅ ¡Listo!", state="complete", expanded=False)

            except Exception as e:
                status.update(label="❌ Error en el procesamiento", state="error")
                st.error(f"Ocurrió un error: {e}")

    # MICRÓFONO
    if hablar_btn:
        with st.spinner("🎙️ Escuchando..."):
            try:
                audio_path = grabar_audio()
                if audio_path and os.path.exists(audio_path):
                    texto_mic = transcribir(audio_path)
                    st.session_state.ultimo_audio = audio_path
                    os.remove(audio_path)
                    if texto_mic.strip():
                        st.success(f"🎙️ Texto detectado: {texto_mic}")
                        _procesar(texto_mic)
                    else:
                        st.warning("No se detectó voz en el audio. Intentá de nuevo.")
                else:
                    st.error("No se pudo grabar el audio. Verificá el micrófono.")
            except Exception as e:
                st.error(f"Error al grabar o transcribir: {e}")

    # BOTÓN CONSULTAR — único trigger para el texto escrito
    if enviar_btn:
        if not texto_input.strip():
            st.warning("⚠️ Escribí una pregunta antes de consultar.")
        else:
            _procesar(texto_input.strip())

    # MOSTRAR RESULTADO (lee de session_state → no se mueve aunque cambies el suavizado)
    ur = st.session_state.ultima_respuesta
    if ur:
        # Audio: solo si la salida lo incluye
        if _modo_salida in ("audio", "ambos"):
            try:
                audio_data = hablar(ur["respuesta"])
                if audio_data:
                    st.audio(audio_data, format="audio/mp3")
            except Exception as e:
                st.warning(f"⚠️ No se pudo generar el audio: {e}")

        # Texto y análisis: solo si la salida lo incluye
        if _modo_salida in ("texto", "ambos"):
            st.markdown("## 🤖 Respuesta")
            respuesta_html = _html.escape(ur["respuesta"]).replace("\n", "<br>")
            st.markdown(f"""
            <div class="response-card">
            <b>🤖 ProfeBot • {ur["hora"]}</b>
            <div style="margin-top:12px; line-height:1.7; font-size:17px;">
            {respuesta_html}
            </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("## 📊 Análisis")
            c1, c2, c3 = st.columns(3)

            with c1:
                entidades    = ur["data"].get("entidades", []) if isinstance(ur["data"], dict) else []
                ents_html    = ""
                if isinstance(entidades, list) and entidades:
                    for ent in entidades:
                        if isinstance(ent, (tuple, list)) and len(ent) >= 2:
                            ents_html += f'<div class="entity-badge">{ent[0]} • {ent[1]}</div>'
                        else:
                            ents_html += f'<div class="entity-badge">{str(ent)}</div>'
                elif isinstance(entidades, str) and entidades.strip():
                    ents_html = f'<div class="entity-badge">{entidades}</div>'
                else:
                    ents_html = '<div class="soft-text">No se detectaron entidades.</div>'
                st.markdown(f"""
                <div class="metric-card">
                <div class="metric-icon">🧠</div>
                <div class="metric-title">Entidades</div>
                <div>{ents_html}</div>
                </div>
                """, unsafe_allow_html=True)

            with c2:
                pp_texto = f"{round(ur['pp'], 2)}" if ur["pp"] is not None else "N/A"
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
                    ⏱️ {ur["tiempo_ms"]} ms<br>
                    🧮 {ur["cant_tokens"]} tokens<br>
                    🎯 score máx: {ur["score_max"]:.2f}<br>
                    ⚙️ k = {ur["k_valor"]} ({ur["modo_label"]})
                </div>
                <div class="soft-text" style="margin-top:15px;">Tokens: {ur["tokens_preview"]}</div>
                </div>
                """, unsafe_allow_html=True)

            # ── POS Tagging ─────────────────────────────────────────────
            pos_tags = ur["data"].get("pos_tags", []) if isinstance(ur["data"], dict) else []
            if pos_tags:
                with st.expander("🔤 Etiquetas POS (categorías gramaticales)", expanded=False):
                    _POS_ES = {
                        "NOUN": "Sustantivo", "VERB": "Verbo", "ADJ": "Adjetivo",
                        "ADV": "Adverbio", "PRON": "Pronombre", "DET": "Determinante",
                        "ADP": "Preposición", "CONJ": "Conjunción", "CCONJ": "Conjunción coord.",
                        "SCONJ": "Conjunción subord.", "AUX": "Auxiliar", "NUM": "Número",
                        "PROPN": "Nombre propio", "INTJ": "Interjección",
                        "X": "Otro", "SYM": "Símbolo", "SPACE": "Espacio",
                    }
                    df_pos = pd.DataFrame(
                        [(tok, _POS_ES.get(pos, pos)) for tok, pos in pos_tags],
                        columns=["Token", "Categoría POS"],
                    )
                    st.dataframe(df_pos, use_container_width=True, hide_index=True)

            if ur.get("sugerencias_ng"):
                st.markdown("### 📊 Top-10 continuaciones del modelo de N-gramas")
                df_ng = pd.DataFrame(
                    [(p, round(prob, 6)) for p, prob in ur["sugerencias_ng"]],
                    columns=["Palabra siguiente", "Probabilidad"],
                )
                st.dataframe(df_ng, use_container_width=True, hide_index=True)

            # ── Panel de fuentes encontradas ────────────────────────────
            fuentes = ur.get("fuentes", [])
            if fuentes:
                with st.expander(
                    f"📄 Fuentes encontradas — {len(fuentes)} fragmento(s) más relevante(s)",
                    expanded=False,
                ):
                    for i, (fragmento, score) in enumerate(fuentes, 1):
                        st.markdown(
                            f"**{i}.** `score TF-IDF: {score}`  \n{_html.escape(fragmento)}"
                        )

    # HISTORIAL
    if st.session_state.chat:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("## 💬 Historial")

        for i in range(0, len(st.session_state.chat), 2):
            if i + 1 < len(st.session_state.chat):
                usr, usr_msg, usr_hora = st.session_state.chat[i]
                bot, bot_msg, bot_hora = st.session_state.chat[i + 1]

                st.markdown(f"""
                <div class="user-message">
                <b>🧑 Usuario • {_html.escape(usr_hora)}</b>
                <div style="margin-top:8px;">{_html.escape(usr_msg)}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="bot-message">
                <b>🤖 ProfeBot • {_html.escape(bot_hora)}</b>
                <div style="margin-top:8px;">{_html.escape(bot_msg).replace(chr(10), '<br>')}</div>
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

    st.markdown("""
    <h1 class="main-title">🧩 Quiz de Repaso</h1>
    <p class="subtitle">Completá la oración con la palabra que falta</p>
    """, unsafe_allow_html=True)

    # ── Cargar corpus una sola vez por sesión ──────────────────────
    if "quiz_corpus" not in st.session_state:
        try:
            with open("data/corpus.txt", "r", encoding="utf-8") as f:
                st.session_state.quiz_corpus = [
                    l.strip() for l in f
                    if l.strip() and not l.strip().startswith("#")
                    and len(l.strip().split()) >= 7
                ]
        except Exception:
            st.session_state.quiz_corpus = []

    # Validar corpus antes de cualquier otra cosa
    if not st.session_state.quiz_corpus:
        st.error("⚠️ No se pudo cargar el corpus para el quiz. Verificá que `data/corpus.txt` exista.")
        st.stop()

    # ── Inicializar estado ─────────────────────────────────────────
    for key, val in [
        ("quiz_oracion", None), ("quiz_palabra", None),
        ("quiz_respondida", False), ("quiz_correctas", 0),
        ("quiz_total", 0), ("quiz_feedback", None),
        ("quiz_input_key", 0), ("quiz_racha", 0),
        ("quiz_racha_max", 0), ("quiz_numero", 0),
        ("quiz_voz_texto", None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = val

    def nueva_pregunta():
        corpus = st.session_state.quiz_corpus
        for _ in range(30):
            linea    = random.choice(corpus)
            palabras = linea.split()
            candidatos = [
                (i, p) for i, p in enumerate(palabras)
                if p.lower().rstrip(".,;:") not in _STOPWORDS_QUIZ and len(p) > 3
            ]
            if candidatos:
                break
        else:
            return
        idx, correcta = random.choice(candidatos)
        palabras[idx] = "___"
        st.session_state.quiz_oracion    = " ".join(palabras)
        st.session_state.quiz_palabra    = correcta.lower().rstrip(".,;:")
        st.session_state.quiz_respondida = False
        st.session_state.quiz_feedback   = None
        st.session_state.quiz_input_key += 1
        st.session_state.quiz_numero    += 1
        st.session_state.quiz_voz_texto  = None

    if st.session_state.quiz_oracion is None:
        nueva_pregunta()

    if st.session_state.quiz_oracion is None:
        st.warning("No se encontraron oraciones válidas en el corpus. Probá con un corpus más extenso.")
        st.stop()

    # ── Métricas ───────────────────────────────────────────────────
    _c     = st.session_state.quiz_correctas
    _t     = st.session_state.quiz_total
    _racha = st.session_state.quiz_racha
    _pct   = f"{_c/_t:.0%}" if _t > 0 else "—"
    _racha_str = f"{_racha} 🔥" if _racha >= 3 else (f"{_racha} ⚡" if _racha >= 1 else str(_racha))

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("✅ Correctas",   _c)
    col_m2.metric("📝 Respondidas", _t)
    col_m3.metric("🎯 Precisión",   _pct)
    col_m4.metric("🔥 Racha",       _racha_str)

    st.markdown("---")

    # ── Pregunta ───────────────────────────────────────────────────
    _num = st.session_state.quiz_numero or 1
    _oracion_html = _html.escape(st.session_state.quiz_oracion).replace(
        "___",
        '<span style="background:linear-gradient(135deg,#6366f1,#8b5cf6);'
        'color:white;padding:4px 22px;border-radius:8px;font-weight:800;'
        'letter-spacing:5px;font-size:1rem;">_ _ _</span>',
    )
    st.markdown(f"""
    <div style="
        background: rgba(15,23,42,0.85);
        border: 1.5px solid rgba(99,102,241,0.35);
        border-radius: 18px;
        padding: 36px 40px;
        margin: 18px 0 22px;
    ">
        <div style="
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            color: #6366f1;
            font-weight: 700;
            margin-bottom: 18px;
        ">✏️ Pregunta #{_num}</div>
        <div style="
            font-size: 1.55rem;
            line-height: 2.1;
            color: #e2e8f0;
            font-weight: 500;
        ">{_oracion_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Feedback (persiste hasta la siguiente pregunta) ────────────
    if st.session_state.quiz_feedback:
        fb   = st.session_state.quiz_feedback
        corr = fb["correcta"]
        tipo = fb["tipo"]
        sim  = fb.get("similitud")
        _sim_str = f" — similitud coseno: **{sim:.2f}**" if sim is not None else ""
        _oracion_marcada = st.session_state.quiz_oracion.replace("___", f"**{corr}**")
        # Mostrar transcripción de voz si se respondió por voz
        if st.session_state.get("quiz_voz_texto"):
            st.info(f"🎙️ Escuché: **{st.session_state.quiz_voz_texto}**")
        if tipo == "correcto":
            st.success(f"✅ ¡Correcto! La palabra era: **{corr}**{_sim_str}\n\n📖 {_oracion_marcada}")
        else:
            st.error(f"❌ Incorrecto. La respuesta era: **{corr}**{_sim_str}\n\n📖 {_oracion_marcada}")

    # ── Input + botones ────────────────────────────────────────────

    def _verificar_respuesta_quiz(usuario, voz_texto=None):
        """Lógica de verificación compartida entre texto y voz."""
        usuario = usuario.lower().strip().rstrip(".,;:")
        if not usuario:
            return False
        correcta = st.session_state.quiz_palabra
        oracion  = st.session_state.quiz_oracion
        similitud = similitud_respuesta_quiz(oracion, correcta, usuario)
        st.session_state.quiz_total     += 1
        st.session_state.quiz_respondida = True
        st.session_state.quiz_voz_texto  = voz_texto  # None si fue por texto
        if usuario == correcta:
            tipo = "correcto"
            st.session_state.quiz_correctas += 1
            st.session_state.quiz_racha     += 1
            st.session_state.quiz_racha_max  = max(
                st.session_state.quiz_racha_max,
                st.session_state.quiz_racha,
            )
        else:
            tipo = "incorrecto"
            st.session_state.quiz_racha = 0
        st.session_state.quiz_feedback = {
            "tipo":      tipo,
            "correcta":  correcta,
            "similitud": similitud,
        }
        guardar_resultado_quiz({
            "estudiante_id":     st.session_state.estudiante,
            "oracion":           oracion,
            "palabra_correcta":  correcta,
            "respuesta_usuario": usuario,
            "es_correcto":       1 if tipo == "correcto" else 0,
            "tipo_resultado":    tipo,
            "similitud":         similitud,
        })
        return True

    if not st.session_state.quiz_respondida:
        respuesta_quiz = st.text_input(
            "Escribí la palabra que falta",
            key=f"quiz_input_{st.session_state.quiz_input_key}",
            placeholder="Tu respuesta...",
        )

        # Botón de micrófono (ocupa columna izquierda)
        col_mic_q, col_v, col_s = st.columns([2, 4, 1])
        with col_mic_q:
            mic_quiz_btn = st.button(
                "🎤 Responder por voz",
                use_container_width=True,
                help="Grabá tu respuesta con el micrófono (5 segundos)",
            )
        with col_v:
            verificar_btn = st.button("✅  Verificar respuesta", use_container_width=True)
        with col_s:
            skip_btn = st.button("🎲", use_container_width=True, help="Saltar esta pregunta")

        # ── Manejo de micrófono ────────────────────────────────────
        if mic_quiz_btn:
            with st.spinner("🎙️ Escuchando... hablá ahora (5 segundos)"):
                try:
                    audio_path = grabar_audio()
                    if audio_path and os.path.exists(audio_path):
                        texto_voz = transcribir(audio_path)
                        os.remove(audio_path)
                        if texto_voz.strip():
                            palabra_voz = _extraer_palabra_quiz(texto_voz)
                            if _verificar_respuesta_quiz(palabra_voz, voz_texto=texto_voz.strip()):
                                st.rerun()
                        else:
                            st.warning("⚠️ No se detectó voz. Intentá de nuevo hablando más cerca del micrófono.")
                    else:
                        st.error("❌ No se pudo grabar el audio. Verificá que el micrófono esté conectado.")
                except Exception as e:
                    st.error(f"❌ Error al grabar o transcribir: {e}")

        # ── Manejo de texto ────────────────────────────────────────
        if verificar_btn:
            if not respuesta_quiz.strip():
                st.warning("⚠️ Escribí algo antes de verificar.")
            else:
                if _verificar_respuesta_quiz(respuesta_quiz, voz_texto=None):
                    st.rerun()

        if skip_btn:
            nueva_pregunta()
            st.rerun()

    else:
        if st.button("➡️  Siguiente pregunta", use_container_width=True, type="primary"):
            nueva_pregunta()
            st.rerun()

    # ── Footer ─────────────────────────────────────────────────────
    st.markdown("---")
    col_rec, col_rst = st.columns([5, 1])
    with col_rec:
        if st.session_state.quiz_racha_max > 0:
            st.info(f"🏆 Mejor racha de esta sesión: **{st.session_state.quiz_racha_max}** correctas seguidas")
    with col_rst:
        if st.button("🔄 Reiniciar", use_container_width=True):
            for _k in ("quiz_correctas", "quiz_total", "quiz_racha",
                       "quiz_racha_max", "quiz_numero"):
                st.session_state[_k] = 0
            st.session_state.quiz_feedback   = None
            st.session_state.quiz_respondida = False
            nueva_pregunta()
            st.rerun()

# =====================================================
# VISTA DASHBOARD
# =====================================================

elif vista == "📊 Dashboard":
    from dashboard import mostrar_dashboard
    mostrar_dashboard()
