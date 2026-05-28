"""
eval_search.py — Script de evaluación independiente para el motor de búsqueda TF-IDF.

Ejecutar desde la raíz del proyecto:
    python tests/eval_search.py

Lee data/consultas_evaluacion.json, calcula Precisión, Recall y F1 para cada consulta
y muestra un resumen por consola. También acepta --top_k y --verbose como argumentos.

Formato esperado del JSON:
    [
        {
            "query": "...",
            "palabras_relevantes": ["...", "..."],
            "total_relevantes": N
        },
        ...
    ]
"""

import sys
import os
import json
import argparse

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.evaluacion import evaluar_busqueda


def main():
    parser = argparse.ArgumentParser(description="Evaluación P/R/F1 del motor de búsqueda de ProfeBot")
    parser.add_argument(
        "--archivo",
        default="data/consultas_evaluacion.json",
        help="Ruta al JSON con consultas etiquetadas (default: data/consultas_evaluacion.json)",
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=5,
        help="Número de documentos a recuperar por consulta (default: 5)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar detalle por cada consulta",
    )
    args = parser.parse_args()

    # Cargar datos
    if not os.path.exists(args.archivo):
        print(f"[ERROR] No se encontró el archivo: {args.archivo}")
        print("Creá el archivo con consultas etiquetadas.")
        sys.exit(1)

    with open(args.archivo, "r", encoding="utf-8") as f:
        consultas = json.load(f)

    if not consultas:
        print("[ERROR] El archivo no contiene consultas.")
        sys.exit(1)

    # Evaluar
    resultados, globales = evaluar_busqueda(consultas, top_k=args.top_k)

    # Mostrar resultados
    print("=" * 70)
    print("  EVALUACIÓN MOTOR DE BÚSQUEDA (TF-IDF) — PROFEBOT")
    print(f"  top_k = {args.top_k}")
    print("=" * 70)

    if args.verbose:
        print()
        for i, r in enumerate(resultados, 1):
            f1_str = f"{r['f1']:.3f}"
            estado = "✔" if r["f1"] >= 0.7 else ("~" if r["f1"] >= 0.4 else "✗")
            print(f"  [{i:2d}] {estado}  P={r['precision']:.3f}  R={r['recall']:.3f}  F1={f1_str}")
            print(f"        QUERY: {r['query']}")
            print(f"        Recuperados: {r['recuperados']} | Relevantes hallados: {r['relevantes_encontrados']}")
            print()

    print(f"  Consultas evaluadas     : {len(resultados)}")
    print(f"  Precisión promedio      : {globales['precision']:.3f}")
    print(f"  Recall promedio         : {globales['recall']:.3f}")
    print(f"  F1 promedio             : {globales['f1']:.3f}")
    n_ok   = sum(1 for r in resultados if r["f1"] >= 0.7)
    n_med  = sum(1 for r in resultados if 0.4 <= r["f1"] < 0.7)
    n_mal  = sum(1 for r in resultados if r["f1"] < 0.4)
    print(f"  Consultas F1 >= 0.7     : {n_ok}")
    print(f"  Consultas F1 0.4–0.69   : {n_med}")
    print(f"  Consultas F1 < 0.4      : {n_mal}")
    print("=" * 70)

    # Código de salida: 0 si F1 promedio >= 0.5, 1 si es peor
    sys.exit(0 if globales["f1"] >= 0.50 else 1)


if __name__ == "__main__":
    main()
