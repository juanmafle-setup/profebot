import os
import threading

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

UMBRAL_SIMILITUD = 0.1

_vectorizer = None
_documentos = None
_X          = None
_lock       = threading.Lock()


def _cargar_indice():
    global _vectorizer, _documentos, _X
    if _vectorizer is not None:
        return
    with _lock:
        if _vectorizer is None:
            corpus_path = "data/corpus.txt"
            if not os.path.exists(corpus_path):
                raise FileNotFoundError(
                    f"No se encontró el corpus en '{corpus_path}'. "
                    "Verificá que el archivo exista antes de iniciar la app."
                )
            with open(corpus_path, "r", encoding="utf-8") as f:
                _documentos = [l for l in f
                               if l.strip() and not l.strip().startswith("#")]
            if not _documentos:
                raise ValueError("El corpus está vacío o solo contiene comentarios.")
            _vectorizer = TfidfVectorizer()
            _X          = _vectorizer.fit_transform(_documentos)


def buscar(query):
    _cargar_indice()
    q_vec       = _vectorizer.transform([query])
    similitudes = cosine_similarity(q_vec, _X).flatten()
    return sorted(
        zip(_documentos, similitudes),
        key=lambda x: x[1],
        reverse=True,
    )


def hay_respuesta(resultados):
    return any(score >= UMBRAL_SIMILITUD for _, score in resultados)
