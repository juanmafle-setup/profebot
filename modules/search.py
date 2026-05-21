from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def buscar(query):
    with open("data/corpus.txt", "r", encoding="utf-8") as f:
        documentos = f.readlines()

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(documentos)

    q_vec = vectorizer.transform([query])

    similitudes = cosine_similarity(q_vec, X).flatten()

    resultados = sorted(
        zip(documentos, similitudes),
        key=lambda x: x[1],
        reverse=True
    )

    return resultados

def evaluar_busqueda():
    """
    Evalúa el motor de búsqueda con un conjunto pequeño de consultas de prueba
    y devuelve Precisión, Recall y F1 promedios.
    """
    # Pequeño conjunto de consultas de prueba etiquetadas manualmente
    consultas_prueba = {
        "qué es la perplejidad": ["# PERPLEJIDAD", "# MODELOS DE LENGUAJE"],
        "cómo funciona tf idf": ["# TF-IDF"],
        "explicar n-gramas": ["# N-GRAMAS", "# MODELOS DE LENGUAJE"],
        "para qué sirve el asr": ["# ASR (RECONOCIMIENTO DE VOZ)"],
        "qué mide el wer": ["# WER"],
        "cómo se tokeniza un texto": ["# TOKENIZACIÓN", "# NLP"],
        "qué es la similitud del coseno": ["# SIMILITUD", "# BÚSQUEDA"],
        "modelos de lenguaje": ["# MODELOS DE LENGUAJE", "# N-GRAMAS"],
        "búsqueda de información": ["# BÚSQUEDA", "# TF-IDF"],
        "reconocimiento de voz": ["# ASR (RECONOCIMIENTO DE VOZ)", "# WER"]
    }

    with open("data/corpus.txt", "r", encoding="utf-8") as f:
        documentos = [linea.strip() for linea in f if linea.strip()]

    precision_total = 0
    recall_total = 0
    f1_total = 0
    num_consultas = 0

    for consulta, relevantes_esperados in consultas_prueba.items():
        # Obtener los 5 documentos más relevantes según el motor
        resultados = buscar(consulta)[:5]
        docs_recuperados = [r[0].strip() for r in resultados]

        # Determinar cuáles de los recuperados son relevantes
        verdaderos_positivos = 0
        for doc in docs_recuperados:
            for esperado in relevantes_esperados:
                if esperado in doc:
                    verdaderos_positivos += 1
                    break

        total_relevantes = len(relevantes_esperados)
        total_recuperados = len(docs_recuperados)

        precision = verdaderos_positivos / total_recuperados if total_recuperados > 0 else 0
        recall = verdaderos_positivos / total_relevantes if total_relevantes > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        precision_total += precision
        recall_total += recall
        f1_total += f1
        num_consultas += 1

    if num_consultas == 0:
        return {"precision": 0, "recall": 0, "f1": 0}

    return {
        "precision": precision_total / num_consultas,
        "recall": recall_total / num_consultas,
        "f1": f1_total / num_consultas
    }