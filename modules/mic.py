import sounddevice as sd
from scipy.io.wavfile import write

def grabar_audio(nombre_archivo="audio.wav", duracion=5, samplerate=16000):
    print("🎤 Grabando...")

    audio = sd.rec(int(duracion * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()

    write(nombre_archivo, samplerate, audio)

    print("✅ Grabación terminada")
    return nombre_archivo