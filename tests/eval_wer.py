"""
eval_wer.py — Script de evaluación independiente para Word Error Rate (WER).

Ejecutar desde la raíz del proyecto:
    python tests/eval_wer.py

Lee data/frases_referencia.json, evalúa el WER de cada par (referencia, hipotesis)
y muestra un resumen por consola. También acepta argumentos para especificar otro archivo.

Formato esperado del JSON:
    [
        {"referencia": "...", "hipotesis": "..."},
        ...
    ]
"""

import sys
import os
import json
import argparse

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.evaluacion import evaluar_wer_batch


def main():
    parser = argparse.ArgumentParser(description="Evaluación WER de ProfeBot")
    parser.add_argument(
        "--archivo",
        default="data/frases_referencia.json",
        help="Ruta al archivo JSON con pares referencia/hipotesis (default: data/frases_referencia.json)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar detalle por cada frase",
    )
    args = parser.parse_args()

    # Cargar datos
    if not os.path.exists(args.archivo):
        print(f"[ERROR] No se encontró el archivo: {args.archivo}")
        print("Creá el archivo con pares {'referencia': ..., 'hipotesis': ...}")
        sys.exit(1)

    with open(args.archivo, "r", encoding="utf-8") as f:
        frases = json.load(f)

    if not frases:
        print("[ERROR] El archivo no contiene frases.")
        sys.exit(1)

    # Evaluar
    resultados, promedio = evaluar_wer_batch(frases)

    # Mostrar resultados
    print("=" * 70)
    print("  EVALUACIÓN WER — PROFEBOT")
    print("=" * 70)

    if args.verbose:
        print()
        for i, r in enumerate(resultados, 1):
            wer_pct = f"{r['wer']:.1%}"
            estado  = "✔" if r["wer"] == 0 else ("~" if r["wer"] < 0.3 else "✗")
            print(f"  [{i:2d}] {estado}  WER={wer_pct:<7}")
            print(f"        REF: {r['referencia']}")
            print(f"        HIP: {r['hipotesis']}")
            print()

    print(f"  Frases evaluadas : {len(resultados)}")
    print(f"  WER promedio     : {promedio:.1%}  ({promedio:.4f})")
    wer_0   = sum(1 for r in resultados if r["wer"] == 0)
    wer_lt3 = sum(1 for r in resultados if 0 < r["wer"] < 0.3)
    wer_ge3 = sum(1 for r in resultados if r["wer"] >= 0.3)
    print(f"  WER = 0 (exactas): {wer_0}")
    print(f"  WER < 30%        : {wer_lt3}")
    print(f"  WER >= 30%       : {wer_ge3}")
    print("=" * 70)

    # Código de salida: 0 si WER promedio < 30%, 1 si es peor
    sys.exit(0 if promedio < 0.30 else 1)


if __name__ == "__main__":
    main()
