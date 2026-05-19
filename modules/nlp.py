import spacy
import re

nlp = spacy.load("es_core_news_sm")

# ============================================================
# DICCIONARIOS DEL DOMINIO (podés ampliarlos cuando quieras)
# ============================================================

CONCEPTOS = [
    # Ya tenías estos
    "perplejidad", "tf-idf", "tf", "idf", "n-grama",
    "bigrama", "trigrama", "tokenización", "token", "wer",
    "word error rate", "modelo de lenguaje", "similitud del coseno",
    "índice invertido", "recuperación de información",
    "reconocimiento de voz", "síntesis de voz", "asr", "tts",
    "procesamiento del lenguaje natural", "nlp", "pln",
    "distancia de levenshtein", "lematización", "stemming",
    "bolsa de palabras", "word embedding", "one-hot encoding",
    "suavizado add-k", "add-one", "probabilidad condicional",
    "entropía", "entropía cruzada", "clustering", "clasificación",
]

ALGORITMOS = [
    "k-means", "k-nn", "k nearest neighbors", "naive bayes",
    "regresión logística", "árbol de decisión", "random forest",
    "svm", "máquinas de soporte vectorial", "gradient boosting",
    "xgboost", "q-learning", "redes neuronales", "lstm", "transformer",
    "bert", "gpt", "whisper",
]

METRICAS = [
    "accuracy", "precisión", "recall", "f1", "f1-score",
    "matriz de confusión", "rmse", "mae", "r2", "auc", "roc",
    "curva roc", "log loss", "perplejidad", "word error rate",
    "error cuadrático medio", "coeficiente de silueta",
]

HERRAMIENTAS = [
    "scikit-learn", "sklearn", "spacy", "nltk", "tensorflow",
    "pytorch", "keras", "matplotlib", "seaborn", "plotly",
    "pandas", "numpy", "jupyter", "streamlit", "gradio",
    "speechrecognition", "gtts", "pyttsx3", "librosa", "pyaudio",
]

# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def procesar(texto):
    """
    Procesa el texto y devuelve un diccionario con:
        - entidades: lista de (texto, etiqueta)
    """
    doc = nlp(texto)
    entidades = [(ent.text, ent.label_) for ent in doc.ents]

    texto_lower = texto.lower()

    # 1. Buscar conceptos del dominio
    for concepto in CONCEPTOS:
        if concepto in texto_lower:
            if not any(ent[0].lower() == concepto for ent in entidades):
                entidades.append((concepto, "CONCEPTO"))

    # 2. Buscar algoritmos
    for algoritmo in ALGORITMOS:
        if algoritmo in texto_lower:
            if not any(ent[0].lower() == algoritmo for ent in entidades):
                entidades.append((algoritmo, "ALGORITMO"))

    # 3. Buscar métricas
    for metrica in METRICAS:
        if metrica in texto_lower:
            if not any(ent[0].lower() == metrica for ent in entidades):
                entidades.append((metrica, "METRICA"))

    # 4. Buscar herramientas
    for herramienta in HERRAMIENTAS:
        if herramienta in texto_lower:
            if not any(ent[0].lower() == herramienta for ent in entidades):
                entidades.append((herramienta, "HERRAMIENTA"))

    # 5. Extraer siglas en mayúsculas (ej: "PLN", "IA", "API")
    siglas = re.findall(r'\b[A-Z]{2,6}\b', texto)
    for sigla in siglas:
        if sigla.lower() not in [e[0].lower() for e in entidades]:
            entidades.append((sigla, "SIGLA"))

    return {"entidades": entidades}