from gtts import gTTS
import io

def hablar(texto):
    """Genera audio MP3 en memoria y devuelve los bytes para st.audio"""
    if not texto:
        return None
    tts = gTTS(texto, lang="es")
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp.read()