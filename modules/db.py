import sqlite3
from datetime import datetime

DB_PATH = "profebot.db"


def conectar():
    """Abre conexión a la base SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def crear_tablas():
    """Crea las 3 tablas obligatorias si no existen."""
    conn = conectar()
    c = conn.cursor()

    # 1. Secciones del corpus
    c.execute("""
        CREATE TABLE IF NOT EXISTS secciones (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            unidad     TEXT,
            bloque     TEXT,
            seccion    TEXT,
            titulo     TEXT,
            texto      TEXT NOT NULL,
            n_tokens   INTEGER
        )
    """)

    # 2. Historial de consultas
    c.execute("""
        CREATE TABLE IF NOT EXISTS consultas (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp           DATETIME DEFAULT CURRENT_TIMESTAMP,
            estudiante_id       TEXT,
            audio_path          TEXT,
            texto_transcripto   TEXT,
            texto_original      TEXT,
            concepto_detectado  TEXT,
            intencion           TEXT,
            seccion_resultado_id INTEGER,
            similitud_coseno    REAL,
            pp                  REAL,
            wer                 REAL,
            tiempo_ms           REAL,
            respuesta           TEXT,
            feedback            TEXT,
            FOREIGN KEY (seccion_resultado_id) REFERENCES secciones(id)
        )
    """)

    # 3. Métricas diarias para el dashboard
    c.execute("""
        CREATE TABLE IF NOT EXISTS metricas (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha                 DATE UNIQUE,
            total_consultas       INTEGER,
            wer_promedio          REAL,
            pp_promedio           REAL,
            precision_busqueda    REAL,
            recall_busqueda       REAL,
            f1_busqueda           REAL,
            consultas_por_categoria TEXT,
            tiempo_promedio_ms    REAL
        )
    """)

    conn.commit()
    conn.close()


def insertar_seccion(unidad, bloque, seccion, titulo, texto, n_tokens=None):
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        INSERT INTO secciones (unidad, bloque, seccion, titulo, texto, n_tokens)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (unidad, bloque, seccion, titulo, texto, n_tokens))
    conn.commit()
    conn.close()


def guardar_consulta(datos):
    """Guarda una consulta completa en la base de datos."""
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        INSERT INTO consultas (
            estudiante_id, audio_path, texto_transcripto, texto_original,
            concepto_detectado, intencion, seccion_resultado_id,
            similitud_coseno, pp, wer, tiempo_ms, respuesta, feedback
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos.get("estudiante_id"),
        datos.get("audio_path"),
        datos.get("texto_transcripto"),
        datos.get("texto_original"),
        datos.get("concepto_detectado"),
        datos.get("intencion"),
        datos.get("seccion_resultado_id"),
        datos.get("similitud_coseno"),
        datos.get("pp"),
        datos.get("wer"),
        datos.get("tiempo_ms"),
        datos.get("respuesta"),
        datos.get("feedback"),
    ))
    conn.commit()
    conn.close()


def obtener_historial(limite=10, desde=None, hasta=None):
    """Recupera las últimas consultas, con filtro opcional por fecha."""
    conn = conectar()
    query = "SELECT * FROM consultas WHERE 1=1"
    params = []
    if desde:
        query += " AND timestamp >= ?"
        params.append(desde)
    if hasta:
        query += " AND timestamp <= ?"
        params.append(hasta)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limite)
    c = conn.cursor()
    c.execute(query, params)
    resultados = c.fetchall()
    conn.close()
    return [dict(r) for r in resultados]


def limpiar_historial():
    """Borra todas las consultas almacenadas."""
    conn = conectar()
    conn.execute("DELETE FROM consultas")
    conn.commit()
    conn.close()


# =============================================================
# FUNCIONES PARA EL DASHBOARD
# =============================================================

def obtener_estadisticas_dashboard():
    """Devuelve todas las métricas necesarias para el dashboard."""
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM consultas")
    total = c.fetchone()[0]
    if total == 0:
        conn.close()
        return None

    # Promedios globales
    c.execute("SELECT AVG(pp), AVG(tiempo_ms), AVG(similitud_coseno), AVG(wer) FROM consultas")
    promedios = c.fetchone()
    pp_prom     = promedios[0] or 0.0
    tiempo_prom = promedios[1] or 0.0
    score_prom  = promedios[2] or 0.0
    wer_prom    = promedios[3]          # puede ser None si nunca se guardó WER

    # Consultas por día (últimos 30 días)
    c.execute("""
        SELECT DATE(timestamp) as fecha, COUNT(*) as cantidad
        FROM consultas
        WHERE timestamp >= DATE('now', '-30 days')
        GROUP BY fecha
        ORDER BY fecha
    """)
    consultas_por_dia = [{"fecha": r["fecha"], "cantidad": r["cantidad"]} for r in c.fetchall()]

    # Top 10 conceptos detectados
    c.execute("""
        SELECT concepto_detectado, COUNT(*) as freq
        FROM consultas
        WHERE concepto_detectado IS NOT NULL AND concepto_detectado != ''
        GROUP BY concepto_detectado
        ORDER BY freq DESC
        LIMIT 10
    """)
    top_conceptos = [{"concepto": r["concepto_detectado"], "frecuencia": r["freq"]} for r in c.fetchall()]

    # Top 10 consultas más frecuentes
    c.execute("""
        SELECT texto_original, COUNT(*) as freq
        FROM consultas
        WHERE texto_original IS NOT NULL AND texto_original != ''
        GROUP BY LOWER(texto_original)
        ORDER BY freq DESC
        LIMIT 10
    """)
    top_consultas = [{"consulta": r["texto_original"], "frecuencia": r["freq"]} for r in c.fetchall()]

    # Distribución de intenciones
    c.execute("""
        SELECT intencion, COUNT(*) as freq
        FROM consultas
        WHERE intencion IS NOT NULL AND intencion != ''
        GROUP BY intencion
        ORDER BY freq DESC
    """)
    dist_intenciones = [{"intencion": r["intencion"], "frecuencia": r["freq"]} for r in c.fetchall()]

    conn.close()

    return {
        "total_consultas":   total,
        "pp_promedio":       round(pp_prom, 2),
        "tiempo_promedio_ms": round(tiempo_prom, 1),
        "score_promedio":    round(score_prom, 3),
        "wer_promedio":      round(wer_prom, 4) if wer_prom is not None else None,
        "consultas_por_dia": consultas_por_dia,
        "top_conceptos":     top_conceptos,
        "top_consultas":     top_consultas,
        "dist_intenciones":  dist_intenciones,
    }


def obtener_terminos_frecuentes(limite=20):
    """Devuelve las palabras más frecuentes en las consultas (sin stopwords)."""
    stopwords = {"de", "la", "el", "en", "y", "a", "con", "que", "es", "un",
                 "una", "los", "las", "por", "para", "se", "del", "al", "su",
                 "como", "más", "mas", "qué", "si", "no", "o"}
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT texto_original FROM consultas WHERE texto_original IS NOT NULL")
    filas = c.fetchall()
    conn.close()

    conteo = {}
    for fila in filas:
        for palabra in fila["texto_original"].lower().split():
            palabra = palabra.strip("¿?.,!()\"'")
            if palabra and palabra not in stopwords and len(palabra) > 2:
                conteo[palabra] = conteo.get(palabra, 0) + 1

    ordenado = sorted(conteo.items(), key=lambda x: x[1], reverse=True)
    return [{"termino": t, "frecuencia": f} for t, f in ordenado[:limite]]
