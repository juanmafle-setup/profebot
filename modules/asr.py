import whisper

model = whisper.load_model("base")

def transcribir(audio_path):
    result = model.transcribe(
        audio_path,
        language="es",
        temperature=0
    )
    return result["text"]