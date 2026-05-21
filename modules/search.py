from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

UMBRAL_SIMILITUD = 0.1

_vectorizer = None
_documentos = None
_X = None

def _cargar_indice():
    global _vectorizer, _documentos, _X
    if _vectorizer is None:
        with open("data/corpus.txt", "r", encoding="utf-8") as f:
            _documentos = [l for l in f.readlines() if l.strip() and not l.strip().startswith("#")]
        _vectorizer = TfidfVectorizer()
        _X = _vectorizer.fit_transform(_documentos)

def buscar(query):
    _cargar_indice()
    q_vec = _vectorizer.transform([query])
    similitudes = cosine_similarity(q_vec, _X).flatten()
    resultados = sorted(
        zip(_documentos, similitudes),
        key=lambda x: x[1],
        reverse=True
    )
    return resultados

def hay_respuesta(resultados):
    return any(score >= UMBRAL_SIMILITUD for _, score in resultados)
