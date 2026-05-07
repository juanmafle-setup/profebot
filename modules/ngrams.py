import math
import re
from collections import defaultdict

def limpiar(texto):
    texto = texto.lower()
    texto = re.sub(r'[^\w\sáéíóúñü]', '', texto)
    return texto

class ModeloNgramas:
    def __init__(self, n=2, k=0.1):
        self.n = n
        self.k = k
        self.ngramas = defaultdict(int)
        self.contextos = defaultdict(int)
        self.vocabulario = set()

    def entrenar(self, corpus):
        for linea in corpus:
            tokens = limpiar(linea).split()
            self.vocabulario.update(tokens)

            tokens = ["<s>"] + tokens + ["</s>"]

            for i in range(len(tokens) - self.n + 1):
                ngrama = tuple(tokens[i:i+self.n])
                contexto = tuple(tokens[i:i+self.n-1])

                self.ngramas[ngrama] += 1
                self.contextos[contexto] += 1

    def probabilidad(self, palabra, contexto):
        contexto = tuple(contexto)
        ngrama = contexto + (palabra,)

        conteo_ng = self.ngramas[ngrama]
        conteo_ctx = self.contextos[contexto]

        V = len(self.vocabulario)

        return (conteo_ng + self.k) / (conteo_ctx + self.k * V)

    def perplejidad(self, texto):
        texto = limpiar(texto)
        tokens = texto.split()
        tokens = ["<s>"] + tokens + ["</s>"]

        N = len(tokens)
        log_prob = 0

        for i in range(len(tokens) - self.n + 1):
            contexto = tokens[i:i+self.n-1]
            palabra = tokens[i+self.n-1]

            prob = self.probabilidad(palabra, contexto)
            log_prob += math.log(prob)

        return math.exp(-log_prob / N)

    def sugerir(self, contexto, top_n=5):
        contexto = tuple(contexto)
        palabras = list(self.vocabulario)

        resultados = []

        for palabra in palabras:
            prob = self.probabilidad(palabra, contexto)
            resultados.append((palabra, prob))

        resultados.sort(key=lambda x: x[1], reverse=True)
        return resultados[:top_n]