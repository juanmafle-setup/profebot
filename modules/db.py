import sqlite3
import json
from datetime import datetime

DB_PATH = "profebot.db"

def conectar():
    """Abre conexión a la base SQLite (un solo archivo)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def crear_tablas():
    """Crea las 3 tablas obligatorias si no existen."""
    conn = conectar()
    c = conn.cursor()

    # 1. Secciones del corpus (apuntes)
    c.execute("""
        CREATE TABLE IF NOT EXISTS secciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidad TEXT,
            bloque TEXT,
            seccion TEXT,
            titulo TEXT,
            texto TEXT NOT NULL,
            n_tokens INTEGER
        )
    """)

    # 2. Historial completo de consultas
    c.execute("""
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            estudiante_id TEXT,
            audio_path TEXT,
            texto_transcripto TEXT,
            texto_original TEXT,
            concepto_detectado TEXT,
            intencion TEXT,
            seccion_resultado_id INTEGER,
            similitud_coseno REAL,
            pp REAL,
            wer REAL,
            tiempo_ms REAL,
            respuesta TEXT,
            feedback TEXT,
            FOREIGN KEY (seccion_resultado_id) REFERENCES secciones(id)
        )
    """)

    # 3. Métricas diarias para el dashboard
    c.execute("""
        CREATE TABLE IF NOT EXISTS metricas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE UNIQUE,
            total_consultas INTEGER,
            wer_promedio REAL,
            pp_promedio REAL,
            precision_busqueda REAL,
            recall_busqueda REAL,
            f1_busqueda REAL,
            consultas_por_categoria TEXT,
            tiempo_promedio_ms REAL
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
    """
    Guarda una consulta completa.
    `datos` es un diccionario con las claves de la tabla consultas.
    """
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
        datos.get("feedback")
    ))
    conn.commit()
    conn.close()

def obtener_historial(limite=10, desde=None, hasta=None):
    """Recupera últimas consultas, opcional filtra por fecha."""
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

def obtener_estadisticas(fecha=None):
    """
    Devuelve un diccionario con métricas para el dashboard.
    Si no se especifica fecha, toma la fecha actual.
    """
    if fecha is None:
        fecha = datetime.now().strftime("%Y-%m-%d")
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM metricas WHERE fecha = ?", (fecha,))
    fila = c.fetchone()
    conn.close()
    return dict(fila) if fila else None

def actualizar_metricas_dia(fecha=None):
    """Calcula y guarda (o actualiza) las métricas del día."""
    # Esta función puede calcular promedios, contar consultas, etc.
    # Para simplificar, la llenaremos cuando integremos el dashboard.
    pass  

def limpiar_historial():
    """Borra todas las consultas almacenadas en la base de datos."""
    import sqlite3
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM consultas")
        conn.commit()

    def obtener_estadisticas_dashboard():
     conn = conectar()
    c = conn.cursor()
    
    # Total de consultas
    c.execute("SELECT COUNT(*) FROM consultas")
    total = c.fetchone()[0]
    
    # Promedios de perplejidad, tiempo y score
    c.execute("SELECT AVG(pp), AVG(tiempo_ms), AVG(similitud_coseno) FROM consultas")
    promedios = c.fetchone()
    pp_prom = promedios[0] if promedios[0] else 0.0
    tiempo_prom = promedios[1] if promedios[1] else 0.0
    score_prom = promedios[2] if promedios[2] else 0.0
    
    # Consultas por día (últimos 30 días)
    c.execute("""
        SELECT DATE(timestamp) as fecha, COUNT(*) as cantidad
        FROM consultas
        WHERE timestamp >= DATE('now', '-30 days')
        GROUP BY fecha
        ORDER BY fecha
    """)
    consultas_por_dia = [{"fecha": row["fecha"], "cantidad": row["cantidad"]} for row in c.fetchall()]
    
    # Top 10 conceptos más preguntados
    c.execute("""
        SELECT concepto_detectado, COUNT(*) as freq
        FROM consultas
        WHERE concepto_detectado IS NOT NULL
        GROUP BY concepto_detectado
        ORDER BY freq DESC
        LIMIT 10
    """)
    top_conceptos = [{"concepto": row["concepto_detectado"], "frecuencia": row["freq"]} for row in c.fetchall()]
    
    # Distribución de intenciones (si existieran)
    # Por ahora dejamos vacío
    
    conn.close()
    
    return {
        "total_consultas": total,
        "pp_promedio": pp_prom,
        "tiempo_promedio_ms": tiempo_prom,
        "score_promedio": score_prom,
        "consultas_por_dia": consultas_por_dia,
        "top_conceptos": top_conceptos
    }

def obtener_estadisticas_dashboard():
    """Devuelve métricas para el dashboard."""
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM consultas")
    total = c.fetchone()[0]
    if total == 0:
        conn.close()
        return None
    c.execute("SELECT AVG(pp), AVG(tiempo_ms), AVG(similitud_coseno) FROM consultas")
    promedios = c.fetchone()
    pp_prom = promedios[0] if promedios[0] else 0.0
    tiempo_prom = promedios[1] if promedios[1] else 0.0
    score_prom = promedios[2] if promedios[2] else 0.0
    c.execute("""
        SELECT DATE(timestamp) as fecha, COUNT(*) as cantidad
        FROM consultas
        WHERE timestamp >= DATE('now', '-30 days')
        GROUP BY fecha
        ORDER BY fecha
    """)
    consultas_por_dia = [{"fecha": row["fecha"], "cantidad": row["cantidad"]} for row in c.fetchall()]
    c.execute("""
        SELECT concepto_detectado, COUNT(*) as freq
        FROM consultas
        WHERE concepto_detectado IS NOT NULL AND concepto_detectado != ''
        GROUP BY concepto_detectado
        ORDER BY freq DESC
        LIMIT 10
    """)
    top_conceptos = [{"concepto": row["concepto_detectado"], "frecuencia": row["freq"]} for row in c.fetchall()]
    conn.close()
    return {
        "total_consultas": total,
        "pp_promedio": pp_prom,
        "tiempo_promedio_ms": tiempo_prom,
        "score_promedio": score_prom,
        "consultas_por_dia": consultas_por_dia,
        "top_conceptos": top_conceptos
    }

def obtener_top_consultas(limite=10):
    """Devuelve las consultas textuales más frecuentes."""
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        SELECT texto_original, COUNT(*) as freq
        FROM consultas
        WHERE texto_original IS NOT NULL AND texto_original != ''
        GROUP BY texto_original
        ORDER BY freq DESC
        LIMIT ?
    """, (limite,))
    resultados = c.fetchall()
    conn.close()
    return [{"texto": row["texto_original"], "frecuencia": row["freq"]} for row in resultados]


def obtener_distribucion_categorias():
    """Devuelve la distribución de conceptos detectados como categorías."""
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        SELECT concepto_detectado, COUNT(*) as freq
        FROM consultas
        WHERE concepto_detectado IS NOT NULL AND concepto_detectado != ''
        GROUP BY concepto_detectado
        ORDER BY freq DESC
    """)
    resultados = c.fetchall()
    conn.close()
    return [{"categoria": row["concepto_detectado"], "frecuencia": row["freq"]} for row in resultados]


def obtener_terminos_frecuentes(limite=30):
    """Devuelve los términos más frecuentes de todas las consultas (para nube de palabras)."""
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT texto_original FROM consultas WHERE texto_original IS NOT NULL AND texto_original != ''")
    textos = [row["texto_original"] for row in c.fetchall()]
    conn.close()
    
    # Tokenizamos y contamos palabras
    from collections import Counter
    import re
    palabras = []
    for texto in textos:
        tokens = re.findall(r'\w+', texto.lower())
        palabras.extend(tokens)
    
    # Filtramos stopwords básicas
    stopwords = {'de', 'la', 'el', 'en', 'y', 'a', 'que', 'los', 'las', 'un', 'una', 'es', 'por', 'se', 'con', 'para', 'como', 'del', 'lo', 'al', 'su', 'o'}
    palabras_filtradas = [p for p in palabras if p not in stopwords and len(p) > 2]
    
    contador = Counter(palabras_filtradas)
    mas_comunes = contador.most_common(limite)
    return [{"termino": termino, "frecuencia": freq} for termino, freq in mas_comunes]