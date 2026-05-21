from modules.mic import grabar_audio
from modules.asr import transcribir
from modules.nlp import procesar
from modules.search import buscar, UMBRAL_SIMILITUD
from modules.tts import hablar
from modules.db import crear_tabla, guardar
from modules.ngrams import ModeloNgramas

import os

# ===== FUNCIONES NUEVAS =====

def es_pregunta(texto):
    return "?" in texto or texto.lower().startswith(("que", "qué", "como", "cómo"))

def generar_respuesta(resultados):
    for r, score in resultados:
        if score >= UMBRAL_SIMILITUD:
            return r.strip()
    return "No encontré información sobre ese tema en el corpus. Intentá reformular la pregunta."

# ===== INICIO =====

crear_tabla()

with open("data/corpus.txt", "r", encoding="utf-8") as f:
    corpus = [l for l in f.readlines() if l.strip() and not l.strip().startswith("#")]

modelo_ng = ModeloNgramas(n=2, k=0.1)
modelo_ng.entrenar(corpus)

historial = []

print("🤖 ProfeBot")
print("Escribí 'salir' para terminar\n")

while True:
    comando = input("Presioná ENTER para hablar (o escribí 'salir'): ")

    if comando.lower() == "salir":
        break

    audio_path = grabar_audio()

    if not os.path.exists(audio_path):
        print("❌ Error con audio")
        continue

    texto = transcribir(audio_path)

    if texto.strip() == "":
        print("⚠️ No se detectó voz")
        continue

    print("\n📝 Usuario:", texto)

    if len(texto.split()) <= 1:
        print("⚠️ Decí una frase más completa")
        continue

    if not es_pregunta(texto):
        print("💬 Podés hacer una pregunta para obtener mejor respuesta")

    data = procesar(texto)
    print("🧠 Entidades:", data["entidades"])

    pp = modelo_ng.perplejidad(texto)
    print("📊 Perplejidad:", round(pp, 2))

    if pp > 120:
        print("⚠️ Posible error en la transcripción")

    tokens = texto.lower().split()
    contexto = tokens[-2:] if len(tokens) >= 2 else tokens

    sugerencias = modelo_ng.sugerir(contexto)

    stopwords = {"de", "la", "el", "en", "y", "a", "con"}

    print("💡 Sugerencias:")
    for palabra, prob in sugerencias:
        if palabra not in stopwords:
            print(f"   - {palabra} ({prob:.4f})")

    resultados = buscar(texto)

    respuesta = generar_respuesta(resultados)

    print("\n🤖 Respuesta:", respuesta)

    hablar(respuesta)
    guardar(texto, respuesta)

    historial.append(texto)
    if len(historial) > 3:
        historial.pop(0)

    print("🧠 Contexto reciente:", historial)

    print("\n" + "="*50 + "\n")