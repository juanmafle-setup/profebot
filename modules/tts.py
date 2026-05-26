from gtts import gTTS
import io
import re

# Patron compilado para quitar comillas rectas y tipograficas.
# Se usan escapes \uXXXX para evitar problemas de encoding en Windows (cp1252).
# \x60=backtick  \x27=apostrofe  \x22=comilla-doble
# “=abre-doble  ”=cierra-doble  ‘=abre-simple  ’=cierra-simple
_RE_COMILLAS = re.compile("[\x60\x27\x22“”‘’]")


def hablar(texto):
    if not texto:
        return None

    # Limpiar caracteres que molestan a gTTS
    texto_limpio = _RE_COMILLAS.sub("", texto)
    texto_limpio = re.sub(r"[-–—]+", " ", texto_limpio)  # guiones -> espacio
    texto_limpio = re.sub(r"\s+", " ", texto_limpio).strip()

    try:
        tts = gTTS(texto_limpio, lang="es")
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception:
        # Fallback: intentar con el texto original sin limpiar
        try:
            tts = gTTS(texto, lang="es")
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception:
            return None
