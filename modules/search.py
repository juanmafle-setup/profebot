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