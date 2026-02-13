import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

import matplotlib.pyplot as plt
#pip install matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


conn = sqlite3.connect("finanzas.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transacciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT,
    descripcion TEXT,
    monto REAL,
    fecha TEXT
)
""")
conn.commit()

# ------------------------------
# FUNCIONES
# ------------------------------

def agregar_transaccion():
    tipo = combo_tipo.get()
    desc = entry_desc.get()
    monto = entry_monto.get()

    if tipo == "" or desc == "" or monto == "":
        messagebox.showwarning("¡Error!", "Todos los campos son obligatorios.")
        return

    try:
        monto = float(monto)
    except ValueError:
        messagebox.showerror("¡Error!", "El monto debe ser un número.")
        return

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO transacciones (tipo, descripcion, monto, fecha)
    VALUES (?, ?, ?, ?)
    """, (tipo, desc, monto, fecha))
    conn.commit()

    messagebox.showinfo("¡Hecho!", "Transacción registrada con éxito.")
    limpiar_campos()
    mostrar_transacciones()
    actualizar_grafica()

def limpiar_campos():
    entry_desc.delete(0, tk.END)
    entry_monto.delete(0, tk.END)
    combo_tipo.set("")

def mostrar_transacciones():
    for row in tree.get_children():
        tree.delete(row)

    cursor.execute("SELECT id, tipo, descripcion, monto, fecha FROM transacciones")
    for fila in cursor.fetchall():
        tree.insert("", tk.END, values=fila)

def actualizar_grafica():
    cursor.execute("SELECT tipo, SUM(monto) FROM transacciones GROUP BY tipo")
    datos = cursor.fetchall()

    tipos = [x[0] for x in datos]
    montos = [x[1] for x in datos]

    fig.clear()
    ax = fig.add_subplot(111)

    colores = []
    for t in tipos:
        if t == "Ingreso":
            colores.append("green")
        elif t == "Gasto":
            colores.append("red")
        else:
            colores.append("gray")

    ax.bar(tipos, montos, color=colores)
    ax.set_title("Total Ingresos vs Gastos")
    ax.set_ylabel("Monto")
    ax.set_xlabel("Tipo")

    canvas.draw()

# ------------------------------
# INTERFAZ GRAFICA
# ------------------------------

root = tk.Tk()
root.title("Registro de Ingresos y Gastos con Gráfica")
root.geometry("800x600")

frame_entrada = tk.Frame(root)
frame_entrada.pack(pady=10)

tk.Label(frame_entrada, text="Tipo (Ingreso/Gasto)").grid(row=0, column=0, padx=5, pady=5)
combo_tipo = ttk.Combobox(frame_entrada, values=["Ingreso", "Gasto"])
combo_tipo.grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame_entrada, text="Descripción").grid(row=1, column=0, padx=5, pady=5)
entry_desc = tk.Entry(frame_entrada, width=30)
entry_desc.grid(row=1, column=1, padx=5, pady=5)

tk.Label(frame_entrada, text="Monto").grid(row=2, column=0, padx=5, pady=5)
entry_monto = tk.Entry(frame_entrada)
entry_monto.grid(row=2, column=1, padx=5, pady=5)

btn_agregar = tk.Button(frame_entrada, text="Agregar Transacción", command=agregar_transaccion)
btn_agregar.grid(row=3, column=0, columnspan=2, pady=10)

tree = ttk.Treeview(root, columns=("ID", "Tipo", "Descripción", "Monto", "Fecha"), show="headings")
tree.heading("ID", text="ID")
tree.heading("Tipo", text="Tipo")
tree.heading("Descripción", text="Descripción")
tree.heading("Monto", text="Monto")
tree.heading("Fecha", text="Fecha")
tree.pack(pady=20)

fig = plt.Figure(figsize=(6,4))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(pady=10)

mostrar_transacciones()
actualizar_grafica()

root.mainloop()