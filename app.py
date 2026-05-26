"""
app.py — versión CLI de ProfeBot (modo consola, sin Streamlit).
Útil para pruebas rápidas sin levantar el servidor web.

Ejecutar con:  python app.py
"""
from modules.mic import grabar_audio
from modules.asr import transcribir
from modules.nlp import procesar
from modules.search import buscar, UMBRAL_SIMILITUD
from modules.tts import hablar
from modules.db import crear_tablas, guardar_consulta
from modules.ngrams import ModeloNgramas

import os


def es_pregunta(texto):
    return "?" in texto or texto.lower().startswith(
        ("que", "qué", "como", "cómo", "para", "cual", "cuál")
    )


def generar_respuesta(resultados):
    for r, score in resultados:
        if score >= UMBRAL_SIMILITUD:
            return r.strip()
    return "No encontré información sobre ese tema en el corpus. Intentá reformular la pregunta."


# ===== INICIO =====

crear_tablas()

with open("data/corpus.txt", "r", encoding="utf-8") as f:
    corpus = [l for l in f.readlines() if l.strip() and not l.strip().startswith("#")]

modelo_ng = ModeloNgramas(n=2, k=0.1)
modelo_ng.entrenar(corpus)

historial = []

print("🤖 ProfeBot — modo CLI")
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

    if not texto.strip():
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

    # Sugerir: para bigrama el contexto es la ÚLTIMA palabra (1 token)
    tokens = texto.lower().split()
    contexto_ng = [tokens[-1]] if tokens else ["<s>"]
    sugerencias = modelo_ng.sugerir(contexto_ng)

    stopwords = {"de", "la", "el", "en", "y", "a", "con"}
    print("💡 Sugerencias:")
    for palabra, prob in sugerencias:
        if palabra not in stopwords:
            print(f"   - {palabra} ({prob:.4f})")

    resultados = buscar(texto)
    respuesta = generar_respuesta(resultados)
    print("\n🤖 Respuesta:", respuesta)

    # TTS: hablar() retorna bytes MP3; en CLI no hay reproductor integrado
    audio_bytes = hablar(respuesta)
    if audio_bytes:
        out_path = "respuesta_cli.mp3"
        with open(out_path, "wb") as f_out:
            f_out.write(audio_bytes)
        print(f"🔊 Audio guardado en {out_path}")

    guardar_consulta({
        "estudiante_id":      "CLI",
        "audio_path":         audio_path,
        "texto_transcripto":  texto,
        "texto_original":     texto,
        "concepto_detectado": None,
        "intencion":          None,
        "seccion_resultado_id": None,
        "similitud_coseno":   resultados[0][1] if resultados else 0,
        "pp":                 pp,
        "wer":                None,
        "tiempo_ms":          None,
        "respuesta":          respuesta,
        "feedback":           None,
    })

    historial.append(texto)
    if len(historial) > 3:
        historial.pop(0)

    print("🧠 Contexto reciente:", historial)
    print("\n" + "=" * 50 + "\n")
