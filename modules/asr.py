import whisper

# Lazy-loaded: el modelo Whisper (~140 MB) solo se carga la primera vez que se
# transcribe audio. De este modo, arrancar la app no bloquea si el usuario
# nunca usa el micrófono.
_model = None


def _get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model


def transcribir(audio_path):
    result = _get_model().transcribe(
        audio_path,
        language="es",
        temperature=0,
    )
    return result["text"]