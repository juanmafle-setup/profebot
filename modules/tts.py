from gtts import gTTS
import os

def hablar(texto):
    archivo = "respuesta.mp3"

    tts = gTTS(texto, lang="es")
    tts.save(archivo)

    os.system(f'start /wait {archivo}')