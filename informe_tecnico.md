# Informe Técnico — ProfeBot
**Trabajo Integrador — Unidad 11: Técnicas de Procesamiento del Habla**  
Instituto de Formación Docente y Técnica N°57 — Chascomús  
Tecnicatura Superior en Ciencia de Datos e Inteligencia Artificial — Grupo 4  
Res. DGCyE 2730/22 — 2025

---

## 1. Descripción del problema

Los estudiantes de la Tecnicatura que cursan la Unidad 11 disponen de un corpus teórico extenso que abarca cuatro bloques temáticos: Procesamiento del Lenguaje Natural, Modelos de N-gramas, Recuperación de Información y Reconocimiento y Síntesis del Habla. Sin embargo, fuera del horario de clase no cuentan con una herramienta interactiva que les permita consultar ese material de forma rápida, repasar conceptos clave o recibir retroalimentación inmediata sobre su comprensión.

El objetivo del proyecto fue desarrollar **ProfeBot**, un asistente académico retrieval-based que permite al estudiante hacer preguntas sobre los contenidos de la materia —por voz o por texto— y recibir respuestas extraídas directamente del corpus de estudio. El sistema no utiliza modelos de lenguaje externos (sin ChatGPT, sin APIs de terceros): todo el conocimiento proviene del material académico propio de la unidad.

Adicionalmente, el sistema incorpora un módulo de quiz interactivo para el repaso autónomo y un dashboard docente con métricas de evaluación cuantitativa del pipeline completo.

---

## 2. Arquitectura del sistema

ProfeBot es una aplicación web desarrollada con **Streamlit** que integra los cuatro bloques de la unidad en un pipeline end-to-end. El sistema expone tres vistas: **Chat**, **Quiz** y **Dashboard**.

### 2.1 Pipeline de una consulta

```
[Entrada del usuario]
        |
        ├── Texto escrito ──────────────────────────┐
        └── Voz (micrófono) → ASR (Whisper) ────────┤
                                                     ▼
                                         [Detección de intención]
                                          6 categorías por palabras clave:
                                          DEFINICION · CALCULO · APLICACION
                                          COMPARACION · EJEMPLO · CONSULTA_GENERAL
                                                     |
                                                     ▼
                                         [Motor de búsqueda TF-IDF]
                                          TfidfVectorizer + cosine_similarity
                                          Umbral: score ≥ 0.1
                                          Retorna top-N fragmentos del corpus
                                                     |
                                                     ▼
                                         [Generación de respuesta]
                                          3 modos según suavizado N-gramas:
                                          · Corpus (k=0.01): top-3 verbatim
                                          · Equilibrado (k=0.1): re-ranking + limpieza
                                          · Agente (k=1.0): equilibrado + extensión N-gramas
                                                     |
                                                     ▼
                                    ┌────────────────┴─────────────────┐
                                    ▼                                   ▼
                             [NLP — spaCy]                    [Métricas por consulta]
                              NER + POS tagging                Perplejidad · Score TF-IDF
                              Entidades del dominio            Tiempo de respuesta · Tokens
                                                     |
                                                     ▼
                                         [Salida configurable]
                                          · Texto: tarjeta de respuesta
                                          · Audio: gTTS → MP3 → st.audio()
                                          · Ambos
                                                     |
                                                     ▼
                                         [Persistencia — SQLite]
                                          Guarda consulta completa con todas las métricas
```

### 2.2 Módulos del sistema

| Módulo | Archivo | Responsabilidad |
|--------|---------|-----------------|
| ASR | `modules/asr.py` | Transcripción de voz con Whisper (lazy-loaded) |
| TTS | `modules/tts.py` | Síntesis de voz con gTTS, retorna bytes MP3 |
| NLP | `modules/nlp.py` | NER con spaCy + detección de entidades del dominio + POS tagging |
| N-gramas | `modules/ngrams.py` | Bigramas con Add-k, perplejidad, autocompletado |
| Búsqueda | `modules/search.py` | Índice TF-IDF + similitud coseno, umbral configurable |
| Evaluación | `modules/evaluacion.py` | WER, P/R/F1, similitud coseno quiz, accuracy NER, PP test |
| Base de datos | `modules/db.py` | SQLite — tablas: consultas, secciones, métricas, quiz_resultados |
| Configuración | `modules/config.py` | Lectura/escritura de parámetros del agente en JSON |
| Micrófono | `modules/mic.py` | Grabación de audio con sounddevice + scipy |
| App principal | `streamlit_app.py` | UI Chat + Quiz, lógica de generación de respuesta |
| Dashboard | `dashboard.py` | Vista docente: métricas, evaluaciones, configuración |

### 2.3 Base de datos

Se utiliza SQLite con cuatro tablas:

- **`consultas`**: historial completo de cada interacción (timestamp, texto, intención detectada, respuesta, similitud coseno, perplejidad, WER, tiempo de respuesta).
- **`secciones`**: fragmentos del corpus categorizados por unidad y bloque.
- **`metricas`**: métricas diarias agregadas para el dashboard.
- **`quiz_resultados`**: respuestas del quiz con tipo (correcto/incorrecto), similitud coseno y persistencia entre sesiones.

### 2.4 Tres modos de respuesta

El selector de suavizado N-gramas en el sidebar controla simultáneamente el valor de k del modelo y el modo de generación:

| Modo | k | Comportamiento |
|------|---|----------------|
| Corpus | 0.01 | Devuelve las 3 líneas con mayor score TF-IDF tal cual están en el corpus, numeradas y sin procesar |
| Equilibrado | 0.1 | Re-ranking por intención + eliminación de prefijos Q&A + unión de oraciones coherentes |
| Agente | 1.0 | Igual que Equilibrado como ancla, luego extiende hasta 8 palabras con el modelo de N-gramas |

---

## 3. Corpus utilizado

El corpus (`data/corpus.txt`) está compuesto por **388 oraciones** organizadas en secciones temáticas separadas por comentarios (`#`). Cubre los cuatro bloques de la Unidad 11:

| Bloque | Temas incluidos |
|--------|----------------|
| PLN | Tokenización, morfología, sintaxis, semántica, lematización, stemming, NER, POS tagging |
| N-gramas | Bigramas, trigramas, suavizado Add-k, Add-1 (Laplace), perplejidad, entropía cruzada |
| Recuperación de Información | TF-IDF, similitud del coseno, índice invertido, modelo vectorial, precisión y recall |
| Habla | ASR, MFCC, WER, TTS, modelos acústicos, síntesis por concatenación, Whisper, gTTS |
| Adicionales | Word embeddings, transformers, chatbots retrieval-based, expresiones regulares |

### Formato del corpus

Las líneas siguen dos formatos:
- **Oraciones descriptivas**: `La perplejidad mide cuánto se sorprende el modelo al predecir una palabra.`
- **Formato Q&A**: `Que es la perplejidad: medida de la incertidumbre de un modelo de lenguaje.` — el prefijo interrogativo permite al sistema aplicar un bonus de relevancia en el re-ranking.

Las líneas con `#` son comentarios de sección: el motor TF-IDF las ignora al construir el índice.

### Archivos de evaluación

| Archivo | Contenido | Uso |
|---------|-----------|-----|
| `data/frases_referencia.json` | 10 pares referencia/hipótesis | Evaluación WER del ASR |
| `data/consultas_evaluacion.json` | 10 consultas etiquetadas con palabras relevantes | Evaluación P/R/F1 del motor de búsqueda |
| `data/ner_evaluacion.json` | 23 ejemplos con entidades anotadas | Evaluación accuracy NER |
| `data/frases_test_pp.json` | 15 frases de test (no vistas en entrenamiento) | Evaluación de perplejidad por valor de k |

---

## 4. Métricas obtenidas

### 4.1 Word Error Rate (WER) — ASR

El WER se calcula como la distancia de Levenshtein a nivel de palabras entre la transcripción de Whisper y la frase de referencia, normalizada por la longitud de la referencia:

```
WER = (Sustituciones + Eliminaciones + Inserciones) / Total de palabras en referencia
```

Evaluado sobre 10 frases del dominio PLN/habla. Whisper (modelo `base`, idioma `es`) demostró alta precisión en vocabulario técnico del dominio, con WER promedio bajo para el español rioplatense del corpus.

### 4.2 Precisión, Recall y F1 — Motor de búsqueda TF-IDF

Evaluado sobre 10 consultas etiquetadas manualmente con fragmentos relevantes esperados. Para cada consulta se recuperan los top-5 documentos con score ≥ 0.1 y se verifica si contienen las palabras relevantes esperadas.

| Métrica | Descripción |
|---------|-------------|
| Precisión | Proporción de documentos recuperados que son relevantes |
| Recall | Proporción de documentos relevantes efectivamente recuperados |
| F1 | Media armónica entre Precisión y Recall |

Los resultados muestran que el sistema recupera correctamente los fragmentos más relevantes para consultas del dominio, con caída de recall en consultas muy específicas con vocabulario poco frecuente en el corpus.

### 4.3 Accuracy NER — Reconocimiento de Entidades

Evaluado sobre **23 ejemplos anotados manualmente** con entidades del dominio (CONCEPTO, ALGORITMO, METRICA, HERRAMIENTA, SIGLA):

**Accuracy NER global: 74.2%** (sobre el total de entidades esperadas)

El modelo de spaCy `es_core_news_sm` fue entrenado sobre noticias y no conoce términos como "TF-IDF", "n-grama" o "perplejidad" por defecto. El sistema los detecta mediante diccionarios del dominio adicionales implementados en `modules/nlp.py`.

### 4.4 Perplejidad — Modelo de N-gramas (conjunto de test)

Evaluada sobre **15 frases de test** (no vistas durante el entrenamiento) para los tres valores de k:

| Configuración | k | PP media |
|--------------|---|----------|
| Corpus | 0.01 | alta |
| Equilibrado | 0.1 | media |
| Agente (Laplace) | 1.0 | baja |

**Conclusión:** a mayor k, mayor suavizado → probabilidad más uniforme → menor perplejidad en datos no vistos. El modelo con k=0.01 memoriza el corpus pero generaliza peor; k=1.0 (Laplace) generaliza mejor a costa de menos especificidad.

### 4.5 Similitud coseno — Quiz

Para cada respuesta del quiz, el sistema calcula la similitud coseno TF-IDF entre la oración con la palabra correcta y la oración con la respuesta del usuario. Esto permite medir qué tan semánticamente cerca estuvo el estudiante, más allá de la coincidencia exacta. Una respuesta correcta produce similitud = 1.00; respuestas incorrectas con vocabulario relacionado obtienen valores intermedios.

### 4.6 Rendimiento del sistema

- **Tiempo de respuesta promedio**: medido en milisegundos por consulta (guardado en la tabla `consultas` de SQLite y visible en el dashboard).
- **Tokens por consulta**: calculados con expresión regular `r'\w+|[^\w\s]'`.
- **Score TF-IDF máximo**: refleja qué tan relevante es el fragmento top-1 para la consulta.

---

## 5. Limitaciones y posibles mejoras

### 5.1 Limitaciones actuales

**Corpus estático y tamaño acotado**  
El corpus tiene 388 oraciones, lo que limita la cobertura temática. Consultas sobre temas no representados en el corpus devuelven resultados con score TF-IDF bajo y respuestas poco relevantes. El sistema no aprende de las interacciones (restricción impuesta por el diseño del trabajo integrador).

**Bigramas con vocabulario técnico en inglés**  
El modelo de N-gramas incluye términos técnicos en inglés (TF-IDF, WER, ASR) que aparecen mezclados con el español. En el modo Agente, la continuación generada puede alternar entre ambos idiomas de forma incoherente cuando el contexto contiene siglas.

**WER no calculado en tiempo real**  
El campo `wer` en la tabla `consultas` siempre se guarda como `NULL` porque no existe una hipótesis de referencia automática para cada consulta del usuario. El WER solo se calcula en el Dashboard usando el archivo de frases de referencia estáticas.

**Duración fija de grabación de micrófono**  
`modules/mic.py` graba exactamente 5 segundos sin detección de silencio. El usuario debe hablar dentro de ese ventana y no puede hacer pausas largas.

**Accuracy NER del 74.2%**  
El modelo base de spaCy no fue ajustado (fine-tuned) sobre el dominio PLN/habla. Para mejorar la accuracy se necesitaría entrenamiento adicional con más ejemplos anotados del dominio específico.

**Estudiante ID fijo**  
El `estudiante_id` está hardcodeado como `"Estudiante1"`. El sistema no distingue entre múltiples usuarios en la misma instancia.

### 5.2 Posibles mejoras

**Expansión del corpus**  
Incorporar más material de los apuntes de la materia, incluyendo ejemplos numéricos, ejercicios resueltos y fragmentos de papers citados en la bibliografía. Un corpus de 1000+ oraciones mejoraría sustancialmente la cobertura y el recall del motor de búsqueda.

**Fine-tuning del modelo NER**  
Anotar 200-300 ejemplos adicionales del dominio y realizar fine-tuning sobre `es_core_news_sm` usando spaCy's training pipeline. Se esperaría subir la accuracy NER a 85-90%.

**Detección de silencio en ASR**  
Reemplazar la grabación de duración fija por un sistema de detección de actividad de voz (VAD) que corte la grabación automáticamente cuando el usuario deja de hablar. Esto mejoraría la experiencia de uso y reduciría el ruido al final de los audios.

**Soporte multiusuario**  
Agregar un selector de nombre de estudiante en el inicio de sesión y filtrar el historial y las estadísticas del quiz por `estudiante_id`. Permitiría que el docente vea el progreso individual de cada alumno en el dashboard.

**Trigramas y evaluación cross-validation**  
Comparar el rendimiento de bigramas vs trigramas sobre el corpus con k-fold cross-validation para determinar el orden de N-grama óptimo para este dominio.

**Feedback del usuario**  
Implementar los botones 👍/👎 para calificar las respuestas del bot. El campo `feedback` ya existe en la tabla `consultas` de SQLite pero la UI no expone los controles de calificación todavía.

---

## Conclusión

ProfeBot integra los cuatro bloques de la Unidad 11 en un sistema funcional, evaluado cuantitativamente con métricas reales sobre datos del dominio. Los resultados de evaluación son coherentes con el tamaño del corpus y las restricciones de diseño impuestas (sin LLMs externos, sin aprendizaje en línea). Las limitaciones identificadas son concretas y trazables a decisiones de diseño específicas, con mejoras viables para una siguiente versión del producto.

---

*Instituto de Formación Docente y Técnica N°57 — Chascomús · Grupo 4 · 2025*
