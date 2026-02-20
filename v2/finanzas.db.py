import sqlite3

conn = sqlite3.connect("finanzas.db")
conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
conn.commit()
conn.close()

print("Base de datos creada")