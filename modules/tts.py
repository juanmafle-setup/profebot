from gtts import gTTS
import io
import re

def hablar(texto):
    
    if not texto:
        return None

    # Limpiar caracteres que molestan a gTTS
    texto_limpio = re.sub(r"[`\'\"“”‘’]", "", texto)       # quitar comillas
    texto_limpio = re.sub(r"[-–—]+", " ", texto_limpio)    # guiones → espacio
    texto_limpio = re.sub(r"\s+", " ", texto_limpio)       # espacios múltiples

    try:
        tts = gTTS(texto_limpio, lang="es")
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception:
        # Si igual falla, probamos sin limpieza extrema
        try:
            tts = gTTS(texto, lang="es")
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception:
            return None
        
        