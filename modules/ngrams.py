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
        self.ngramas        = defaultdict(int)
        self.contextos      = defaultdict(int)
        self.vocabulario    = set()
        # Índice inverso: {contexto: {palabra: conteo}}
        # Construido durante entrenar() para que sugerir() sea O(palabras_vistas)
        # en lugar de O(V·log V).
        self._idx_contexto  = defaultdict(lambda: defaultdict(int))
        self._vocab_list    = None   # lista cacheada tras el entrenamiento

    def entrenar(self, corpus):
        for linea in corpus:
            tokens = limpiar(linea).split()
            self.vocabulario.update(tokens)
            tokens = ["<s>"] + tokens + ["</s>"]
            for i in range(len(tokens) - self.n + 1):
                ngrama   = tuple(tokens[i:i + self.n])
                contexto = tuple(tokens[i:i + self.n - 1])
                palabra  = tokens[i + self.n - 1]
                self.ngramas[ngrama]             += 1
                self.contextos[contexto]         += 1
                self._idx_contexto[contexto][palabra] += 1
        self._vocab_list = list(self.vocabulario)

    def probabilidad(self, palabra, contexto):
        contexto   = tuple(contexto)
        ngrama     = contexto + (palabra,)
        conteo_ng  = self.ngramas[ngrama]
        conteo_ctx = self.contextos[contexto]
        V          = len(self.vocabulario)
        return (conteo_ng + self.k) / (conteo_ctx + self.k * V)

    def perplejidad(self, texto):
        texto  = limpiar(texto)
        tokens = ["<s>"] + texto.split() + ["</s>"]
        N      = len(tokens)
        if N <= 1:          # texto vacío tras limpiar → perplejidad indefinida
            return float("inf")
        log_prob = 0.0
        for i in range(len(tokens) - self.n + 1):
            contexto = tokens[i:i + self.n - 1]
            palabra  = tokens[i + self.n - 1]
            prob = self.probabilidad(palabra, contexto)
            # Guard: log(0) lanzaría ValueError; con Add-k y vocab>0 no debería
            # ocurrir, pero se protege por si el vocabulario está vacío.
            log_prob += math.log(prob) if prob > 0 else math.log(1e-10)
        return math.exp(-log_prob / N)

    def sugerir(self, contexto, top_n=5):
        """
        Devuelve las `top_n` palabras más probables dado el contexto.

        Si el contexto fue visto durante el entrenamiento, solo puntúa las
        palabras que realmente lo siguieron (típicamente < 20) — O(seen·log seen).
        Si el contexto es nuevo, devuelve lista vacía (todas las palabras tienen
        probabilidad idéntica k/V y no aportan información útil).
        """
        contexto   = tuple(contexto)
        candidatos = self._idx_contexto.get(contexto)
        if not candidatos:
            return []

        V          = len(self.vocabulario)
        conteo_ctx = self.contextos[contexto]
        scored = [
            (word, (count + self.k) / (conteo_ctx + self.k * V))
            for word, count in candidatos.items()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]
