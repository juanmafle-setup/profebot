# 🤖 Guía para Presentar ProfeBot
**Instituto de Formación Docente y Técnica N°57 — Chascomús**  
Tecnicatura Superior en Ciencia de Datos e IA — Grupo 4  
Unidad 11 — Técnicas de Procesamiento del Habla

---

## Estructura sugerida (15-20 minutos)

| # | Sección | Tiempo |
|---|---------|--------|
| 1 | Introducción y problema | 2 min |
| 2 | Qué es ProfeBot | 1 min |
| 3 | Arquitectura del sistema | 3 min |
| 4 | Demo: Vista Chat | 3 min |
| 5 | Demo: Vista Quiz | 2 min |
| 6 | Demo: Vista Dashboard | 3 min |
| 7 | Métricas de evaluación | 3 min |
| 8 | Cierre y preguntas | 2 min |

---

## 1. Introducción y problema (2 min)

**Qué decir:**
> "El problema que identificamos es que los estudiantes que estudian los contenidos de esta materia —PLN y reconocimiento de voz— no tienen una herramienta interactiva para repasar los conceptos. Los manuales son extensos y no hay manera de hacer preguntas cuando el docente no está.
> 
> Por eso desarrollamos ProfeBot: un asistente académico que permite consultar el corpus de la materia por voz o por texto, recibir respuestas basadas en el material, y repasar con un quiz interactivo."

**Puntos clave a mencionar:**
- El sistema NO usa ChatGPT, Claude ni ninguna API externa.
- Todo el conocimiento viene del corpus académico de la Unidad 11.
- Es 100% local y sin conexión a internet (excepto gTTS).

---

## 2. Qué es ProfeBot (1 min)

**Qué decir:**
> "ProfeBot tiene tres vistas: Chat para hacer consultas, Quiz para repasar, y Dashboard para que el docente vea las métricas del sistema.
> 
> Técnicamente integra los cuatro bloques de la unidad: PLN con spaCy, modelos de N-gramas con suavizado Add-k, recuperación de información con TF-IDF, y reconocimiento y síntesis de voz con Whisper y gTTS."

---

## 3. Arquitectura del sistema (3 min)

Explicar el flujo de una consulta de punta a punta:

```
[Usuario habla] → Whisper (ASR) → texto
       ↓
   spaCy (NLP) → detecta entidades + POS tags
       ↓
   TF-IDF → busca en el corpus → top-3 fragmentos relevantes
       ↓
   N-gramas → genera/extiende la respuesta (modo Agente)
       ↓
   gTTS (TTS) → audio de respuesta [si está configurado]
       ↓
   SQLite → guarda consulta, métricas, resultados
```

**Qué decir sobre cada bloque:**

- **ASR (Whisper):** "Convierte el audio del micrófono en texto. Usamos el modelo `openai-whisper` que corre localmente."
- **NLP (spaCy):** "Detecta entidades nombradas (personas, conceptos del dominio, métricas) y también extrae las categorías gramaticales de cada token —sustantivos, verbos, adjetivos— con POS tagging."
- **TF-IDF:** "Es el motor de búsqueda. Indexa el corpus y calcula la similitud coseno entre la consulta y cada oración. Devuelve los fragmentos más relevantes."
- **N-gramas:** "Modelo de bigramas con suavizado Add-k. Sirve para autocompletado, calcular la perplejidad de una consulta, y en el modo Agente extiende la respuesta generando palabras nuevas."
- **TTS (gTTS):** "Convierte la respuesta en audio que se reproduce en la interfaz."

---

## 4. Demo: Vista Chat (3 min)

**Antes de la demo, tener abierta la app en `http://localhost:8501`.**

**Pasos a mostrar:**
1. Escribir: `¿Qué es la perplejidad?`
2. Hacer clic en "Consultar →"
3. Señalar:
   - La **tarjeta de respuesta** con el texto generado
   - El panel **"🧠 Entidades"** → muestra "perplejidad · CONCEPTO"
   - El panel **"🔤 Etiquetas POS"** → tabla con tokens y categoría gramatical
   - El panel **"📄 Fuentes encontradas"** → los 3 fragmentos del corpus con su score TF-IDF
   - La **tabla de N-gramas** → top-10 continuaciones posibles
4. Mostrar el **autocompletado** escribiendo solo `perplej` en el campo de texto

**Cambiar el modo de suavizado** en el sidebar y explicar:
- `Tal cual el corpus (k=0.01)`: respuesta literal, sin procesar
- `Equilibrado (k=0.1)`: re-ranking inteligente, limpieza de prefijos Q&A
- `Formulado por el agente (k=1.0)`: extiende la respuesta con N-gramas

**Si hay micrófono disponible:** mostrar también la entrada por voz.

---

## 5. Demo: Vista Quiz (2 min)

**Pasos a mostrar:**
1. Ir a la vista **🧩 Quiz**
2. Señalar la pregunta en el recuadro grande con el `_ _ _` violeta
3. Escribir la palabra correcta → presionar **"✅ Verificar respuesta"**
4. Señalar el **feedback** con la similitud coseno: `similitud coseno: 1.00`
5. Mostrar las métricas en el encabezado: Correctas / Respondidas / Precisión / Racha
6. Hacer clic en **"➡️ Siguiente pregunta"**
7. Mencionar que todos los resultados se guardan en SQLite entre sesiones

---

## 6. Demo: Vista Dashboard (3 min)

**Ir a la vista 📊 Dashboard.**

**Secciones a mostrar en orden:**

1. **Configuración del agente** — expandir el panel y explicar:
   - Modo de entrada: texto / audio / ambos
   - Modo de salida: texto / audio / ambos
   - Nivel de respuesta: breve / normal / detallada

2. **Métricas globales** — señalar las 6 métricas:
   - Total consultas, PP promedio, WER, Tiempo promedio, F1 búsqueda, Accuracy NER

3. **Evolución temporal** — gráfico de consultas por día

4. **Evaluación WER** — tabla con las 10 frases de referencia y su WER

5. **Evaluación P/R/F1** — tabla + gráfico de barras

6. **Perplejidad test set** — comparación de los 3 valores de k sobre 15 frases

7. **Accuracy NER** — tabla con los 23 ejemplos anotados → resultado: 74.2%

8. **Quiz stats** — torta verde/rojo + palabras más falladas

9. **Últimas consultas** — tabla + botón **"📥 Exportar CSV"**

---

## 7. Métricas de evaluación (3 min)

### WER — Word Error Rate
- Mide el error de transcripción de Whisper.
- Fórmula: `WER = (S + D + I) / N` (sustituciones + eliminaciones + inserciones sobre total de palabras).
- Evaluado sobre 10 frases de referencia del dominio.

### Accuracy NER
- **74.2%** sobre 23 ejemplos anotados manualmente.
- Entidades del dominio: CONCEPTO, ALGORITMO, METRICA, HERRAMIENTA, SIGLA.
- El modelo de spaCy no conoce términos como "TF-IDF" o "n-grama" por defecto; los agregamos como vocabulario del dominio.

### Precisión / Recall / F1 (motor de búsqueda)
- Evaluado sobre 10 consultas etiquetadas con palabras relevantes esperadas.
- Se recuperan los top-5 documentos y se verifica si contienen las palabras relevantes.

### Perplejidad (test set)
- 15 frases de test que el modelo NO vio en entrenamiento.
- Evaluada con los 3 valores de k:
  - `k=0.01` (Corpus): PP alta — memoriza el corpus, falla en datos nuevos.
  - `k=0.1` (Equilibrado): PP media — balance entre memorización y generalización.
  - `k=1.0` (Agente): PP baja — distribuye probabilidad más uniformemente, más estable.
- **Conclusión:** mayor k → menor perplejidad en test → mejor generalización.

---

## 8. Cierre y preguntas (2 min)

**Qué decir:**
> "ProfeBot cumple con lo pedido en la guía: integra los cuatro bloques de la unidad en un sistema real y funcional, con evaluación cuantitativa de cada componente. Todo corre localmente, sin LLMs externos, y el corpus es 100% el material de la materia.
>
> Las cosas que más nos costaron fueron el re-ranking de intención para que el agente responda mejor según el tipo de pregunta, y anotar los 23 ejemplos para la evaluación NER."

---

## Preguntas frecuentes que puede hacer el docente

**¿Por qué bigramas y no trigramas?**
> "Con trigramas el vocabulario de contextos se hace muy disperso para un corpus de 350 oraciones. El bigrama tiene mejor cobertura y la perplejidad resultante es más informativa."

**¿Por qué usaron TF-IDF en vez de embeddings?**
> "TF-IDF es interpretable, no necesita GPU, y para un corpus de dominio específico como el nuestro funciona bien. Los embeddings requieren modelos pre-entrenados en español de gran escala que no son parte de los contenidos de la unidad."

**¿El modelo aprende de las consultas de los estudiantes?**
> "No. El modelo de N-gramas se entrena una sola vez sobre el corpus fijo. Las consultas se guardan en la base de datos para análisis docente, pero no modifican el modelo."

**¿Por qué el Accuracy NER es 74.2% y no más alto?**
> "El modelo de spaCy `es_core_news_sm` está entrenado en textos de noticias, no en textos académicos de PLN. Para subirlo habría que hacer fine-tuning con más ejemplos anotados del dominio."

**¿Qué diferencia hay entre los tres modos de respuesta?**
> "Corpus muestra las frases del corpus tal cual, sin procesar. Equilibrado aplica re-ranking por intención y limpia prefijos Q&A. Agente usa el modo equilibrado como ancla y luego extiende la respuesta con el modelo de N-gramas."

**¿Para qué sirve el Dashboard si es solo para docentes?**
> "El docente puede ver qué conceptos consultan más los estudiantes, cuáles tienen peor WER (más difíciles de pronunciar), qué palabras del quiz fallan más, y ajustar la configuración del agente según el perfil del grupo."

---

## Checklist antes de la presentación

- [ ] Correr `python -m streamlit run streamlit_app.py` y verificar que abre en el navegador
- [ ] Hacer al menos 3-4 consultas de prueba para tener historial en el dashboard
- [ ] Hacer 5-6 preguntas en el quiz para que aparezcan estadísticas
- [ ] Verificar que `data/corpus.txt` existe y tiene contenido
- [ ] Verificar que los archivos de evaluación existen: `frases_referencia.json`, `consultas_evaluacion.json`, `ner_evaluacion.json`, `frases_test_pp.json`
- [ ] Tener el navegador en pantalla completa con el sidebar visible
- [ ] Si vas a mostrar audio: probar el micrófono y los parlantes antes
- [ ] Si no vas a mostrar audio: configurar el agente en "Solo texto" desde el Dashboard

---

## Comandos útiles

```bash
# Iniciar la app
python -m streamlit run streamlit_app.py

# Evaluar WER por consola
python tests/eval_wer.py --verbose

# Evaluar motor de búsqueda por consola
python tests/eval_search.py --verbose

# Ver la base de datos
# (usar cualquier cliente SQLite, o el dashboard directamente)
```
