# 🤖 ProfeBot

Asistente de estudio por voz para la Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial.  
**Unidad 11 — Técnicas de Procesamiento del Habla** | Grupo 4 | DGCyE Provincia de Buenos Aires

---

## Descripción

ProfeBot es un chatbot académico **retrieval-based** (sin generación de texto, sin LLMs externos) que permite a los estudiantes consultar contenidos de la materia por voz o texto. El sistema integra los cuatro bloques de la unidad:

| Bloque | Tecnología |
|--------|------------|
| Procesamiento del Lenguaje Natural | spaCy — tokenización, NER, POS tagging |
| Modelos de N-gramas | Bigramas con suavizado Add-k configurable |
| Recuperación de Información | TF-IDF + similitud del coseno |
| Reconocimiento y Síntesis del Habla | Whisper (ASR) + gTTS (TTS) |

---

## Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/profebot.git
cd profebot
```

### 2. Crear entorno virtual (recomendado)
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Descargar el modelo de spaCy en español
```bash
python -m spacy download es_core_news_sm
```

---

## Ejecución

```bash
python -m streamlit run streamlit_app.py
```

La aplicación se abre automáticamente en `http://localhost:8501`.

---

## Estructura del proyecto

```
profebot/
├── streamlit_app.py          # App principal (Streamlit)
├── dashboard.py              # Vista dashboard docente
├── app.py                    # Versión CLI (consola)
├── requirements.txt
├── README.md
├── data/
│   ├── corpus.txt            # Corpus del dominio (350+ oraciones)
│   ├── frases_referencia.json   # 10 frases para evaluación WER
│   └── consultas_evaluacion.json  # 10 consultas etiquetadas para P/R/F1
├── modules/
│   ├── asr.py        # Reconocimiento de voz (Whisper)
│   ├── tts.py        # Síntesis de voz (gTTS)
│   ├── nlp.py        # NER con spaCy
│   ├── ngrams.py     # Modelo de N-gramas con suavizado Add-k
│   ├── search.py     # Motor TF-IDF + similitud del coseno
│   ├── evaluacion.py # WER, detección de intención, P/R/F1
│   └── db.py         # Persistencia SQLite
└── profebot.db       # Base de datos SQLite (generada automáticamente)
```

---

## Vistas de la aplicación

### 💬 Chat
- Campo de texto y botón de micrófono para hacer preguntas
- Respuesta en texto y audio (TTS)
- Métricas por consulta: perplejidad, score TF-IDF, tokens, tiempo
- Sugerencias de autocompletado por N-gramas
- Historial de la sesión descargable en TXT

### 🧩 Quiz
- Generador de preguntas de repaso tipo fill-in-the-blank
- Validación de respuestas por similitud y coincidencia exacta
- Puntaje acumulado por sesión

### 📊 Dashboard (docente)
- Métricas globales: total consultas, PP promedio, WER promedio, F1
- Evolución temporal de consultas por día
- Top 10 consultas más frecuentes
- Distribución de intenciones detectadas
- Términos más buscados
- Evaluación ASR: tabla WER sobre 10 frases de referencia
- Evaluación del motor de búsqueda: Precisión, Recall y F1 por consulta

---

## Métricas de evaluación

| Métrica | Descripción |
|---------|-------------|
| WER | Word Error Rate — errores del ASR sobre 10 frases de referencia |
| Perplejidad | Medida de sorpresa del modelo de N-gramas |
| Precisión | Proporción de resultados recuperados que son relevantes |
| Recall | Proporción de documentos relevantes efectivamente recuperados |
| F1 | Media armónica de Precisión y Recall |

---

## Corpus

El corpus (`data/corpus.txt`) contiene **350+ oraciones** organizadas en 19 temas:
PLN · Morfología · Sintaxis · Semántica/NER · N-gramas · Suavizado · Perplejidad · TF-IDF · Similitud del coseno · VSM · Recuperación de información · Precisión y Recall · ASR · MFCC · TTS · WER · Modelos de lenguaje · Chatbots · Embeddings · Transformers · Segmentación · Expresiones regulares

Fuente: apuntes de la Unidad 11 de la Tecnicatura (DGCyE Res. 2730/22).

---

## Criterios de diseño

- **Sin aprendizaje en línea**: el modelo no se actualiza con las interacciones del usuario.
- **Sin LLMs externos**: no se usan APIs de ChatGPT, Claude ni similares.
- **Persistencia total**: toda interacción queda guardada en SQLite entre sesiones.
- **Retrieval-based**: las respuestas se recuperan del corpus mediante TF-IDF + coseno.

---

## Instituto

**Instituto de Formación Docente y Técnica N°57 — Chascomús**  
Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial  
Trayecto F — Unidad 11 | Res. 2730/22
