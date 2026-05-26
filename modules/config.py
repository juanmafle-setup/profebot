"""
config.py — Módulo de configuración persistente del agente.
Lee y escribe data/config.json. No toca el modelo ni el corpus.
"""
import json
import os

CONFIG_PATH = "data/config.json"

DEFAULTS = {
    "nivel_respuesta": "normal",      # "breve" | "normal" | "detallada"
    "num_resultados": 1,              # cuántas oraciones concatenar en la respuesta
    "modo_entrada": "ambos",          # "texto" | "audio" | "ambos"
    "modo_salida": "ambos",           # "texto" | "audio" | "ambos"
}


def cargar_config() -> dict:
    """Devuelve la configuración actual. Si no existe el archivo, devuelve defaults."""
    if not os.path.exists(CONFIG_PATH):
        return DEFAULTS.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Combinar con defaults para garantizar todas las claves
        cfg = DEFAULTS.copy()
        cfg.update(data)
        return cfg
    except Exception:
        return DEFAULTS.copy()


def guardar_config(cfg: dict) -> None:
    """Persiste la configuración en data/config.json."""
    os.makedirs("data", exist_ok=True)
    full = DEFAULTS.copy()
    full.update(cfg)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(full, f, ensure_ascii=False, indent=2)
