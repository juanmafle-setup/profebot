import streamlit as st
import os
from modules.asr import transcribir
from modules.search import buscar
from modules.tts import hablar
from modules.ngrams import ModeloNgramas
from modules.nlp import procesar
from modules.mic import grabar_audio

# ===== CONFIG =====
st.set_page_config(page_title="ProfeBot", layout="centered")

st.title("🤖 ProfeBot")
st.write("Asistente de Procesamiento del Lenguaje Natural")

# ===== CARGA MODELO =====
@st.cache_resource
def cargar_modelo():
    with open("data/corpus.txt", "r", encoding="utf-8") as f:
        corpus = f.readlines()

    modelo = ModeloNgramas(n=2, k=0.1)
    modelo.entrenar(corpus)
    return modelo

modelo_ng = cargar_modelo()

# ===== HISTORIAL =====
if "chat" not in st.session_state:
    st.session_state.chat = []

# ===== FUNCIONES =====
def generar_respuesta(texto, resultados):
    texto = texto.lower()

    if "tf idf" in texto or "tf-idf" in texto:
        return "TF-IDF mide la importancia de una palabra en un documento en relación con otros documentos."

    if "tf" in texto:
        return "TF mide la frecuencia de una palabra en un documento."

    if "perplejidad" in texto:
        return "La perplejidad mide qué tan bien un modelo de lenguaje predice una secuencia de palabras."

    if "n-grama" in texto:
        return "Un N-grama es una secuencia de palabras utilizada para modelar lenguaje."

    for r, score in resultados:
        if not r.strip().startswith("#"):
            return r.strip()

    return "No encontré una respuesta clara."

# ===== INPUT TEXTO =====
texto_input = st.text_input("💬 Escribí tu pregunta:")

# ===== BOTÓN MICRO =====
if st.button("🎤 Hablar"):
    audio_path = grabar_audio()

    if os.path.exists(audio_path):
        texto_input = transcribir(audio_path)
        st.success(f"📝 Detectado: {texto_input}")

# ===== PROCESAMIENTO =====
if texto_input:
    resultados = buscar(texto_input)
    respuesta = generar_respuesta(texto_input, resultados)

    # guardar historial
    st.session_state.chat.append(("Usuario", texto_input))
    st.session_state.chat.append(("Bot", respuesta))

    # mostrar
    st.write("### 🤖 Respuesta:")
    st.success(respuesta)

    # audio
    hablar(respuesta)

    # métricas
    data = procesar(texto_input)
    st.write("🧠 Entidades:", data["entidades"])

    pp = modelo_ng.perplejidad(texto_input)
    st.write("📊 Perplejidad:", round(pp, 2))

# ===== HISTORIAL =====
st.write("## 💬 Historial")

for rol, msg in st.session_state.chat:
    if rol == "Usuario":
        st.markdown(f"**🧑 {msg}**")
    else:
        st.markdown(f"**🤖 {msg}**")