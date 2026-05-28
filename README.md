# 🤖 ProfeBot

Asistente de estudio por voz para la Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial.  
**Unidad 11 — Técnicas de Procesamiento del Habla** | Grupo 4 | DGCyE Provincia de Buenos Aires

---

## Descripción

ProfeBot es un chatbot académico **retrieval-based** (sin generación de texto, sin LLMs externos) que permite a los estudiantes consultar contenidos de la materia por voz o texto. El sistema integra los cuatro bloques de la unidad:

| Bloque | Tecnología |
|--------|------------|
| Procesamiento del Lenguaje Natural | spaCy — tokenización, NER, POS tagging |
| Modelos de N-gramas | Bigramas con suavizado Add-k configurable (k = 0.01 / 0.1 / 1.0) |
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
├── streamlit_app.py              # App principal (Streamlit)
├── dashboard.py                  # Vista dashboard docente
├── app.py                        # Versión CLI (consola)
├── requirements.txt
├── README.md
├── styles.css                    # Estilos globales de la UI
├── data/
│   ├── corpus.txt                # Corpus del dominio (350+ oraciones)
│   ├── frases_referencia.json    # 10 frases para evaluación WER
│   ├── consultas_evaluacion.json # 10 consultas etiquetadas para P/R/F1
│   ├── ner_evaluacion.json       # 23 ejemplos anotados para accuracy NER
│   └── frases_test_pp.json       # 15 frases de test para evaluación de perplejidad
├── modules/
│   ├── asr.py        # Reconocimiento de voz (Whisper)
│   ├── tts.py        # Síntesis de voz (gTTS)
│   ├── nlp.py        # NER + POS tagging con spaCy
│   ├── ngrams.py     # Modelo de N-gramas con suavizado Add-k
│   ├── search.py     # Motor TF-IDF + similitud del coseno
│   ├── evaluacion.py # WER, intención, P/R/F1, similitud coseno quiz, NER accuracy, PP test
│   ├── db.py         # Persistencia SQLite (consultas, quiz, métricas)
│   ├── mic.py        # Grabación de audio por micrófono
│   └── config.py     # Gestión de configuración del agente
├── tests/
│   ├── eval_wer.py      # Script CLI para evaluar WER
│   └── eval_search.py   # Script CLI para evaluar P/R/F1 del motor de búsqueda
└── profebot.db           # Base de datos SQLite (generada automáticamente)
```

---

## Vistas de la aplicación

### 💬 Chat
- Campo de texto (con Enter o botón) y micrófono para consultas
- Modo de entrada configurable: texto, audio o ambos
- Respuesta en texto y/o audio (TTS), configurable desde el Dashboard
- Métricas por consulta: perplejidad, score TF-IDF, cantidad de tokens, tiempo de respuesta
- **Etiquetas POS**: categorías gramaticales de los tokens detectadas por spaCy
- **Panel de fuentes**: los 3 fragmentos del corpus más relevantes con su score TF-IDF
- Sugerencias de autocompletado por modelo de N-gramas
- Historial de la sesión descargable en TXT

### 🧩 Quiz
- Generador de preguntas de repaso tipo fill-in-the-blank a partir del corpus
- Validación de respuestas: correcto / incorrecto
- Similitud coseno (TF-IDF) entre la respuesta del usuario y la respuesta correcta
- Puntaje acumulado, racha de respuestas correctas y récord de racha por sesión
- **Persistencia entre sesiones**: todos los resultados se guardan en SQLite

### 📊 Dashboard (docente)
- **Configuración del agente**: nivel de respuesta, modo de entrada/salida, guardado persistente
- Métricas globales: total consultas, PP promedio, WER promedio, tiempo promedio, F1 búsqueda, Accuracy NER
- Evolución temporal de consultas por día (últimos 30 días)
- Top 10 consultas más frecuentes y top conceptos detectados
- Distribución de intenciones detectadas y términos más buscados
- **Evaluación ASR**: tabla WER para 10 frases de referencia
- **Evaluación del motor de búsqueda**: Precisión, Recall y F1 por consulta con gráfico de barras
- **Evaluación de Perplejidad**: comparación de PP media entre los tres valores de k (0.01, 0.1, 1.0) sobre 15 frases de test
- **Evaluación NER**: accuracy por ejemplo (23 casos anotados)
- **Estadísticas del Quiz**: total, correctas, incorrectas, accuracy, distribución en torta (verde/rojo), palabras más falladas
- **Últimas consultas**: tabla con las 10 más recientes, exportable a CSV

---

## Métricas de evaluación

| Métrica | Descripción |
|---------|-------------|
| WER | Word Error Rate — errores del ASR sobre 10 frases de referencia |
| Perplejidad | Medida de sorpresa del modelo de N-gramas (evaluada sobre 15 frases de test) |
| Precisión | Proporción de resultados recuperados que son relevantes |
| Recall | Proporción de documentos relevantes efectivamente recuperados |
| F1 | Media armónica de Precisión y Recall |
| Accuracy NER | Proporción de entidades esperadas correctamente detectadas (23 ejemplos) |
| Similitud coseno quiz | Similitud TF-IDF entre la respuesta del usuario y la respuesta correcta |

---

## Scripts de evaluación independientes

Podés ejecutar las evaluaciones directamente desde la consola:

```bash
# Evaluar WER
python tests/eval_wer.py --verbose

# Evaluar motor de búsqueda (P/R/F1)
python tests/eval_search.py --verbose --top_k 5
```

Ambos scripts retornan código 0 si la métrica supera el umbral mínimo (WER < 30%, F1 >= 0.50).

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
- **Modularidad**: cada componente (ASR, TTS, NLP, búsqueda, N-gramas, DB) es independiente y testeable.

---

## Instituto

**Instituto de Formación Docente y Técnica N°57 — Chascomús**  
Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial  
Trayecto F — Unidad 11 | Res. 2730/22
