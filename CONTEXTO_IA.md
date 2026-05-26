# CONTEXTO_IA.md — ProfeBot: Guía completa para IAs

> **Propósito de este archivo**: proporcionar a cualquier IA (o desarrollador nuevo)
> todo el contexto necesario para entender, mantener y extender el proyecto sin
> conversación previa. Incluye arquitectura, flujo de datos, decisiones de diseño,
> bugs conocidos y restricciones duras.

---

## 1. Descripción del proyecto

**ProfeBot** es un asistente educativo de voz para la materia
*Técnicas de Procesamiento del Habla* (Tecnicatura Superior en Ciencia de Datos e IA,
Unidad 11, Instituto N° 57 – Chascomús).

- **Dominio**: Procesamiento del Lenguaje Natural (PLN/NLP) y Reconocimiento de Voz.
- **Stack principal**: Python 3.14 · Streamlit 1.57 · scikit-learn · spaCy · Whisper · gTTS.
- **Modalidades**: texto escrito ↔ voz (ASR → respuesta → TTS).

### Restricción crítica — NO aprendizaje en línea

> **El agente NO aprende de las interacciones del usuario.**  
> El corpus es estático (`data/corpus.txt`). El modelo de N-gramas se entrena una sola
> vez sobre ese corpus. TF-IDF se construye una vez al arrancar. Ningún parámetro
> cambia durante la sesión ni entre sesiones. Esta restricción es impuesta por el
> profesor y es **no negociable**.

---

## 2. Estructura de archivos

```
profebot/
├── streamlit_app.py          # Aplicación principal (UI + lógica de chat + quiz)
├── dashboard.py              # Vista Dashboard con métricas y config docente
├── app.py                    # Entry point alternativo (redirige a streamlit_app)
├── styles.css                # Estilos CSS para la interfaz dark-mode
├── requirements.txt          # Dependencias Python
│
├── data/
│   ├── corpus.txt            # Base de conocimiento (~400 líneas, categorías con #)
│   ├── config.json           # Configuración persistente del agente
│   ├── consultas_evaluacion.json   # Casos de prueba P/R/F1
│   └── frases_referencia.json      # Pares ref/hipotesis para WER
│
└── modules/
    ├── search.py             # Motor TF-IDF (índice, búsqueda, threshold)
    ├── ngrams.py             # Modelo de N-gramas con Add-k smoothing
    ├── evaluacion.py         # WER, detección de intención, P/R/F1
    ├── nlp.py                # spaCy NER + detección de entidades del dominio
    ├── asr.py                # ASR con Whisper (lazy-loaded)
    ├── tts.py                # TTS con gTTS
    ├── mic.py                # Grabación de audio con sounddevice
    ├── db.py                 # SQLite: consultas, secciones, métricas
    └── config.py             # Lectura/escritura de data/config.json
```

---

## 3. Diagrama de arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PROFEBOT (Streamlit)                         │
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌─────────────────────────────┐  │
│  │  💬 Chat  │    │ 🧩 Quiz  │    │      📊 Dashboard           │  │
│  └────┬─────┘    └────┬─────┘    └─────────────┬───────────────┘  │
│       │               │                         │                   │
│       │ texto/audio   │ corpus.txt              │ config.json       │
│       ▼               ▼                         ▼                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    PIPELINE DE CONSULTA                     │   │
│  │                                                             │   │
│  │  [Entrada]──►[ASR]──►[Texto]──►[NLP/NER]                  │   │
│  │                                    │                        │   │
│  │                              [Detección de                  │   │
│  │                               Intención]                   │   │
│  │                                    │                        │   │
│  │                              [TF-IDF Search]               │   │
│  │                                    │                        │   │
│  │                           [generar_respuesta]              │   │
│  │                          ┌─────────┴──────────┐            │   │
│  │                     [modo=corpus] [modo=equil.] [modo=agente]  │   │
│  │                          │           │            │         │   │
│  │                      [top-3 raw] [intent+clean] [clean+   │   │
│  │                                                 ngrams]    │   │
│  │                                    │                        │   │
│  │                              [Perplejidad]                 │   │
│  │                                    │                        │   │
│  │  [Respuesta]──►[TTS]──►[Audio]    │                        │   │
│  │       │                           │                        │   │
│  │       └──────────────────►[SQLite DB]                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Flujo detallado de una consulta (vista Chat)

```
USUARIO escribe o habla
        │
        ▼
[1] ENTRADA
  ├── Texto → texto_input (directo)
  └── Audio → grabar_audio() → .wav → transcribir() [Whisper base, lazy-loaded]
                                                   → texto_input

        │
        ▼
[2] DETECCIÓN DE INTENCIÓN  (modules/evaluacion.py → detectar_intencion)
  Clasifica el texto en 6 categorías por palabras clave:
  - DEFINICION   → "que es", "qué es", "que significa", "que mide", "que indica"
  - CALCULO      → "como se calcula", "formula", "como se obtiene"
  - APLICACION   → "para que sirve", "para que se usa", "aplicaciones"
  - COMPARACION  → "diferencia entre", "vs", "versus", "comparar"
  - EJEMPLO      → "ejemplo", "dame un", "muestra un"
  - CONSULTA_GENERAL (default)

        │
        ▼
[3] BÚSQUEDA TF-IDF  (modules/search.py → buscar)
  - corpus.txt → TfidfVectorizer (sklearn) → matriz TF-IDF
  - cosine_similarity(query_vector, corpus_matrix)
  - Retorna lista [(línea, score)] ordenada por score desc
  - Umbral: UMBRAL_SIMILITUD = 0.1 (líneas con score < 0.1 se descartan)
  - El índice se construye UNA SOLA VEZ (threading.Lock, double-checked locking)

        │
        ▼
[4] GENERACIÓN DE RESPUESTA  (streamlit_app.py → generar_respuesta)
  
  Según el modo seleccionado en sidebar (suavizado N-gramas):
  
  ┌─ MODO "corpus" (📄 k=0.01) ──────────────────────────────────────┐
  │  → Top-3 resultados TF-IDF verbatim, numerados 1/2/3              │
  │  → Sin ningún procesamiento (con prefijos Q&A si los hay)         │
  └───────────────────────────────────────────────────────────────────┘
  
  ┌─ MODO "equilibrado" (⚖️ k=0.1) ─────────────────────────────────┐
  │  CAPA 1: TF-IDF score (base, dominante)                           │
  │  CAPA 2: bonus_directo (+0.4 o +0.5):                             │
  │    - +0.5 si el fragmento antes de ':' empieza con interrogativa   │
  │           Y contiene el término clave (formato Q&A del corpus)     │
  │    - +0.4 si doc contiene "{término} {verbo_intención}"            │
  │           (ej: "la perplejidad mide...")                           │
  │  CAPA 3: bonus_intención (+0.08 × patrones):                      │
  │    - Cuenta patrones léxicos de la intención en el doc             │
  │    - Peso pequeño: solo desempata, no domina                       │
  │                                                                   │
  │  score_total = tfidf + bonus_directo + bonus_intención × 0.08     │
  │                                                                   │
  │  → Re-ranking por score_total                                      │
  │  → Filtro coherencia: oración N solo si tfidf ≥ top_tfidf × 0.55 │
  │  → Stripping del prefijo Q&A ("Que es X: ..." → "...")             │
  │  → Une hasta num_resultados oraciones coherentes                  │
  └───────────────────────────────────────────────────────────────────┘
  
  ┌─ MODO "agente" (🤖 k=1.0) ──────────────────────────────────────┐
  │  → Igual que "equilibrado" para obtener 1 oración ancla           │
  │  → _continuar_ngramas(ancla, modelo_ng, max_palabras=8):          │
  │      - Limpia el texto (quita puntuación) para matchear vocab      │
  │      - Toma la última palabra como contexto inicial                │
  │      - Genera greedy: elige la palabra más probable que no         │
  │        esté en las últimas 3 palabras (anti-ciclo)                 │
  │      - Máximo 8 palabras (más → incoherencia con bigrams)          │
  │  → Si no hay extensión disponible (última palabra sin              │
  │    continuaciones en corpus):                                      │
  │    → _generar_desde_concepto(termino, modelo_ng, max_palabras=15) │
  │      Genera desde el concepto clave extraído de la query           │
  └───────────────────────────────────────────────────────────────────┘

        │
        ▼
[5] ANÁLISIS NLP  (modules/nlp.py → procesar)
  - spaCy es_core_news_sm → NER standard
  - Detección adicional de: CONCEPTO, ALGORITMO, METRICA, HERRAMIENTA, SIGLA
    (diccionarios propios del dominio NLP/speech)

        │
        ▼
[6] MÉTRICAS
  - Perplejidad: modelo_ng.perplejidad(texto_input)
    → math.exp(-log_prob / N) — mide qué tan "esperado" es el texto según el modelo
  - Tiempo de respuesta (ms)
  - Score TF-IDF máximo (resultados[0][1])
  - Cantidad de tokens (tokenizar: regex r'\w+|[^\w\s]')

        │
        ▼
[7] PERSISTENCIA  (modules/db.py → guardar_consulta)
  SQLite → tabla consultas:
  timestamp, estudiante_id, texto_original, concepto_detectado, intencion,
  similitud_coseno, pp, tiempo_ms, respuesta, feedback

        │
        ▼
[8] SALIDA
  ├── TTS: hablar(respuesta) → gTTS → BytesIO → st.audio()
  └── Texto: response-card HTML + tabla N-gramas + métricas visuales
```

---

## 5. Módulos — referencia detallada

### `modules/search.py`
| Item | Detalle |
|---|---|
| Motor | `TfidfVectorizer` + `cosine_similarity` (sklearn) |
| Índice | `_vectorizer`, `_documentos`, `_X` — globales de módulo |
| Thread-safety | `threading.Lock()` con double-checked locking en `_cargar_indice()` |
| Umbral | `UMBRAL_SIMILITUD = 0.1` — resultados con score < 0.1 se descartan |
| Corpus | Lee `data/corpus.txt`, ignora líneas vacías y comentarios (`#`) |
| Función pública | `buscar(query) → list[(doc, score)]` ordenado desc |

### `modules/ngrams.py`
| Item | Detalle |
|---|---|
| Modelo | Bigrama (n=2) con Add-k smoothing |
| k configurables | 0.01 (corpus literal), 0.1 (equilibrado), 1.0 (Laplace/agente) |
| Índice inverso | `_idx_contexto: {contexto: {palabra: conteo}}` — O(palabras_vistas) |
| `sugerir()` | O(palabras_vistas_en_contexto · log) — no O(V·log V) |
| `perplejidad()` | `math.exp(-sum(log_prob) / N)` |
| `_vocab_list` | Cacheada post-entrenamiento |
| Cache Streamlit | `@st.cache_resource` por valor de `k` → 3 modelos máx en memoria |

### `modules/evaluacion.py`
| Función | Descripción |
|---|---|
| `calcular_wer(ref, hip)` | Levenshtein a nivel palabra / len(referencia) |
| `evaluar_wer_batch(frases)` | Procesa lista `[{referencia, hipotesis}]` |
| `detectar_intencion(texto)` | Regex de palabras clave → 6 categorías |
| `evaluar_busqueda(consultas, top_k)` | Precisión/Recall/F1 sobre `consultas_evaluacion.json` |

**Intenciones y palabras clave:**
```python
DEFINICION:   "que es", "qué es", "defini", "que significa", "que mide",
              "que hace", "que representa", "que indica", "que son"
CALCULO:      "como se calcula", "como funciona", "como se mide", "formula"
APLICACION:   "para que sirve", "cual es el uso", "aplicaciones"
COMPARACION:  "diferencia entre", " vs ", " versus ", "comparar", "ventaja"
EJEMPLO:      "ejemplo", "ejemplos", "dame un", "muestra un"
```

### `modules/nlp.py`
- Carga `spacy.load("es_core_news_sm")` al importar
- Detecta entidades estándar (spaCy) + 4 listas del dominio:
  - `CONCEPTOS`: perplejidad, tf-idf, n-grama, wer, etc.
  - `ALGORITMOS`: k-means, naive bayes, transformer, bert, etc.
  - `METRICAS`: accuracy, precisión, f1, rmse, etc.
  - `HERRAMIENTAS`: sklearn, spacy, streamlit, gtts, whisper, etc.
- También detecta siglas en mayúsculas (`[A-Z]{2,6}`)

### `modules/asr.py`
- Whisper `base` model — **lazy-loaded** (solo se carga la primera vez que se transcribe)
- `transcribir(audio_path)` → `str` en español (`language="es"`, `temperature=0`)

### `modules/tts.py`
- `hablar(texto)` → `bytes` (MP3) o `None` si falla
- Limpieza previa: quita comillas, guiones → espacio, espacios múltiples
- Fallback: si falla con limpieza, intenta con texto original
- Retorna `BytesIO.read()` — compatible con `st.audio()`

### `modules/mic.py`
- `grabar_audio(nombre="audio.wav", duracion=5, samplerate=16000)`
- Usa `sounddevice` + `scipy.io.wavfile.write`
- Graba a archivo; el llamador es responsable de borrarlo (`os.remove`)

### `modules/db.py`
**Tablas SQLite (`profebot.db`):**

| Tabla | Propósito |
|---|---|
| `consultas` | Historial completo: timestamp, texto, intención, respuesta, métricas |
| `secciones` | Fragmentos del corpus categorizados (pendiente de poblar) |
| `metricas` | Métricas diarias agregadas (pendiente de poblar) |

**Funciones principales:**
```python
crear_tablas()                          # DDL — seguro de llamar múltiples veces
guardar_consulta(datos: dict)           # INSERT en consultas
obtener_historial(limite=10, desde, hasta)  # SELECT con filtro de fecha
limpiar_historial()                     # DELETE consultas
obtener_estadisticas_dashboard()        # Promedios, top-10, distribución de intenciones
obtener_terminos_frecuentes(limite=20)  # Word frequency sin stopwords
```

### `modules/config.py`
```python
CONFIG_PATH = "data/config.json"
DEFAULTS = {
    "nivel_respuesta": "normal",   # "breve" | "normal" | "detallada" (label UI)
    "num_resultados":  1,          # 1 | 2 | 3 — usado en generar_respuesta()
    "modo_entrada":    "ambos",    # "texto" | "audio" | "ambos"
    "modo_salida":     "ambos",    # "texto" | "audio" | "ambos"
}
```
- `cargar_config()` → mergea con DEFAULTS (claves faltantes → valor por defecto)
- `guardar_config(cfg)` → sobreescribe el JSON con merge sobre DEFAULTS

---

## 6. Formato del corpus (`data/corpus.txt`)

```
# TITULO_SECCION                   ← línea de comentario, ignorada por search.py
Oración descriptiva normal.         ← texto libre, incluido en TF-IDF
Otra oración del mismo tema.

Que es X: respuesta directa.        ← formato Q&A (bonus_directo +0.5)
Como se calcula X: fórmula.         ← ídem
Para que sirve X: uso.              ← ídem
```

**Reglas del corpus:**
- Las líneas `#` son separadores de sección — **no se indexan**
- Las líneas vacías se ignoran
- Las entradas Q&A deben empezar con palabra interrogativa (`que`, `como`, `para`, etc.)
- El prefijo Q&A se muestra en modo "corpus" y se oculta en modo "equilibrado"/"agente"
- Sin acentos en el corpus para evitar problemas de encoding

---

## 7. Configuración (`data/config.json`)

```json
{
  "nivel_respuesta": "detallada",
  "num_resultados":  3,
  "modo_entrada":    "ambos",
  "modo_salida":     "ambos"
}
```

| Clave | Valores | Efecto |
|---|---|---|
| `nivel_respuesta` | `"breve"` / `"normal"` / `"detallada"` | Label UI en Dashboard |
| `num_resultados` | `1` / `2` / `3` | Cuántas oraciones une `generar_respuesta` (modo equilibrado) |
| `modo_entrada` | `"texto"` / `"audio"` / `"ambos"` | Habilita/deshabilita widget de texto y botón de mic |
| `modo_salida` | `"texto"` / `"audio"` / `"ambos"` | Reproduce TTS si incluye `"audio"` |

---

## 8. Los tres modos de respuesta (suavizado N-gramas)

El selector de suavizado en el sidebar controla **tanto el modelo N-gramas** (k afecta las probabilidades del autocompletado y la tabla) **como el modo de generación de respuesta**:

| Opción UI | k | modo interno | Comportamiento de respuesta |
|---|---|---|---|
| 📄 Tal cual el corpus | 0.01 | `"corpus"` | Top-3 líneas TF-IDF verbatim, numeradas, sin procesar |
| ⚖️ Equilibrado | 0.1 | `"equilibrado"` | 1-3 oraciones limpias, intent re-ranking, prefijo Q&A removido |
| 🤖 Formulado por el agente | 1.0 | `"agente"` | Igual que equilibrado + extensión de 8 palabras con N-gramas |

**Diferencia visible garantizada:**
- Modo 1 vs 2: modo 1 siempre muestra 3 resultados (incluso líneas Q&A con prefijo)
- Modo 2 vs 3: modo 3 siempre agrega texto generado o falla-sobre al concepto

---

## 9. Función `generar_respuesta` — firma completa

```python
def generar_respuesta(
    resultados,                         # list[(str, float)] de buscar()
    intencion="CONSULTA_GENERAL",       # str de detectar_intencion()
    num_resultados=1,                   # int — oraciones a unir (modo equilibrado)
    query="",                           # str — pregunta original del usuario
    modo="equilibrado",                 # "corpus" | "equilibrado" | "agente"
    modelo_ng=None,                     # ModeloNgramas | None
) -> str
```

**Sub-funciones relacionadas (nivel módulo):**

| Función | Descripción |
|---|---|
| `_extraer_termino(query)` | Quita stopwords de intención, retorna ≤3 palabras clave |
| `_bonus_directo(termino, doc, intencion, term_n)` | +0.5 Q&A, +0.4 sujeto-verbo |
| `_quitar_prefijo(doc)` | Remueve "Que es X:" antes de mostrar |
| `_continuar_ngramas(base, modelo_ng, max_palabras=8)` | Extensión greedy con anti-ciclo |
| `_generar_desde_concepto(termino, modelo_ng, max_palabras=15)` | Fallback: genera desde el concepto |

---

## 10. Vista Quiz

- Corpus cargado **una vez** en `st.session_state.quiz_corpus` (líneas ≥7 palabras)
- `nueva_pregunta()` usa `for _ in range(20)` (máximo 20 intentos, sin recursión)
- Oculta 1 palabra no-stopword de más de 3 caracteres
- Scoring: exacto → correcto, prefijo/sufijo → "muy cerca"
- Estado en session_state: `quiz_oracion`, `quiz_palabra`, `quiz_correctas`, `quiz_total`

---

## 11. Vista Dashboard

- Gráficos con `plotly.express`
- Evaluación WER: lee `data/frases_referencia.json` → `evaluar_wer_batch()`
- Evaluación P/R/F1: lee `data/consultas_evaluacion.json` → `evaluar_busqueda()`
- Ambas evaluaciones cacheadas con `@st.cache_data(ttl=300)`
- Panel de configuración del agente: guarda en `data/config.json`
- `nivel_respuesta` → `num_resultados` mapping: `{breve:1, normal:2, detallada:3}`

---

## 12. Constantes de nivel módulo en `streamlit_app.py`

```python
_MODOS_K       # dict: label → k_valor
_MODOS_LABEL   # dict: label → label_corto (para panel de análisis)
_MODOS_RESP    # dict: label → modo_interno ("corpus"/"equilibrado"/"agente")
_SW_EXTRACCION # set: stopwords para extraer término clave de la query
_QA_INICIO     # set: palabras que marcan inicio de pregunta Q&A
_VERBOS_DIRECTOS    # dict: intencion → [verbos] para bonus_directo +0.4
_PATRONES_INTENCION # dict: intencion → [patrones] para bonus_intencion ×0.08
_BONUS_INTENCION_PESO = 0.08
_STOPWORDS_AUTO     # set: filtro de stopwords para sugerencias de autocompletado
_STOPWORDS_QUIZ     # set: filtro de stopwords para el quiz
```

Estas constantes se crean **una sola vez al cargar el módulo** — no se recrean en cada rerun de Streamlit. Mismo principio para las funciones `_extraer_termino`, `_bonus_directo`, `_quitar_prefijo`, `_continuar_ngramas`, `_generar_desde_concepto`, `generar_respuesta`.

---

## 13. Gestión del estado de sesión (Streamlit)

| Clave | Tipo | Descripción |
|---|---|---|
| `chat` | `list[(rol, msg, hora)]` | Historial de la conversación visible |
| `feedback` | `dict` | Feedback por mensaje (no implementado aún) |
| `estudiante` | `str` | ID del estudiante (fijo: "Estudiante1") |
| `ultimo_audio` | `str\|None` | Path al último archivo WAV grabado |
| `historial_cargado` | `bool` | Flag para cargar el historial DB solo una vez |
| `ultimo_texto_procesado` | `str` | Evita reprocesar la misma query (anti-loop) |
| `procesando` | `bool` | Flag mutex para evitar procesamiento concurrente |
| `quiz_corpus` | `list[str]` | Corpus del quiz cacheado (se carga una vez) |
| `quiz_oracion` | `str\|None` | Oración actual con la palabra oculta |
| `quiz_palabra` | `str\|None` | Palabra correcta del quiz |
| `quiz_mostrar` | `bool` | Si se mostró la respuesta del quiz |
| `quiz_correctas` | `int` | Contador de respuestas correctas |
| `quiz_total` | `int` | Contador de intentos totales |

---

## 14. Dependencias (`requirements.txt`)

```
streamlit==1.57.0
scikit-learn>=1.3.0
pandas>=2.0.0
plotly>=5.18.0
spacy>=3.7.0            # + python -m spacy download es_core_news_sm
openai-whisper>=20231117
gtts>=2.5.0
sounddevice>=0.4.6
scipy>=1.11.0
```

---

## 15. Cómo ejecutar

```bash
# 1. Instalar dependencias
pip install -r requirements.txt
python -m spacy download es_core_news_sm

# 2. Lanzar la aplicación
streamlit run streamlit_app.py

# O con el entry point alternativo:
streamlit run app.py
```

---

## 16. Branch activo y estado del repositorio

- **Branch principal de desarrollo**: `mejoras-corpus-y-busqueda`
- **Branch estable**: `main` / `v2`
- Todos los cambios de esta sesión están en `mejoras-corpus-y-busqueda` y pusheados.

### Commits recientes relevantes:
| Hash | Descripción |
|---|---|
| `f974984` | Diferenciar los tres modos de respuesta de forma visible y coherente |
| `3bb0939` | Implementar tres modos de respuesta funcionales según suavizado N-gramas |
| `cbbeb6d` | Refactorizar: índice inverso N-gramas, lock TF-IDF, constantes a nivel módulo |
| `b67e0be` | Reemplazar slider Add-k por radio de 3 modos (fix freeze) |
| `ad2483e` | Quitar prefijo Q&A en respuesta + entradas "Que mide X" |
| `cf97c19` | Sistema de respuesta directa por extracción de término clave |

---

## 17. Limitaciones conocidas y TODOs

| Problema | Estado | Notas |
|---|---|---|
| Modo agente puede mezclar palabras en inglés | Esperado | El corpus tiene términos en inglés; el N-grama los sigue estadísticamente |
| WER siempre `None` en DB | Bug conocido | Se guarda `wer=None` porque no hay hipótesis automática; solo se calcula en Dashboard con archivo estático |
| `feedback` en DB siempre `None` | Pendiente | Campo guardado pero UI de feedback no implementada |
| `secciones` table vacía | Pendiente | No se popula desde la app; diseñada para futura indexación estructurada |
| `estudiante_id` fijo | Pendiente | Siempre "Estudiante1"; podría ser configurable |
| Audio mic: duración fija 5 seg | Limitación | `mic.py` graba exactamente 5 segundos sin detección de silencio |
| Corpus sin acentos | Diseño | Para evitar errores de encoding; TF-IDF funciona igual |

---

## 18. Patrones de código importantes

### CSS cacheado
```python
@st.cache_data
def _leer_css():
    with open("styles.css", "r", encoding="utf-8") as f:
        return f.read()
st.markdown(f"<style>{_leer_css()}</style>", unsafe_allow_html=True)
```

### N-gramas cacheados por k
```python
@st.cache_resource
def cargar_modelo(k=0.1):
    modelo = ModeloNgramas(n=2, k=k)
    modelo.entrenar(corpus)
    return modelo
modelo_ng = cargar_modelo(k=k_valor)  # 3 modelos máx en cache (k=0.01/0.1/1.0)
```

### Config sin cachear (refleja cambios del Dashboard)
```python
_cfg = cargar_config()   # una llamada al inicio del bloque Chat, por rerun
```

### Saltos de línea en modo corpus
```python
# La respuesta se almacena con \n para DB y TTS
# Solo se convierte a <br> en el HTML del chat:
respuesta_html = respuesta.replace('\n', '<br>')
```

### Anti-doble-procesamiento
```python
if texto_input == st.session_state.ultimo_texto_procesado:
    st.stop()
```
