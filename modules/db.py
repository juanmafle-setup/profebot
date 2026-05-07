import sqlite3

def crear_tabla():
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS conversaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            respuesta TEXT
        )
    """)

    conn.commit()
    conn.close()

def guardar(usuario, respuesta):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()

    c.execute("INSERT INTO conversaciones (usuario, respuesta) VALUES (?, ?)",
              (usuario, respuesta))

    conn.commit()
    conn.close()