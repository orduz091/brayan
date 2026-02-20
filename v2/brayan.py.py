import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet

# ------------------------------
# BASE DE DATOS
# ------------------------------
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
# FUNCIONES DE SALDO
# ------------------------------

def fecha_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def obtener_saldo():
    cursor.execute("""
        SELECT 
        SUM(CASE WHEN tipo='Ingreso' THEN monto ELSE -monto END)
        FROM transacciones
    """)
    saldo = cursor.fetchone()[0]
    return saldo if saldo else 0.0

def actualizar_saldo():
    saldo = obtener_saldo()
    color = "green" if saldo >= 0 else "red"
    lbl_saldo.config(text=f"Saldo actual: ${saldo:,.2f}", fg=color)

def actualizar_reloj():
    lbl_fecha.config(text="Fecha y hora: " + fecha_actual())
    root.after(1000, actualizar_reloj)

# ------------------------------
# CRUD
# ------------------------------

def agregar_transaccion():
    tipo = combo_tipo.get()
    desc = entry_desc.get().strip()
    monto = entry_monto.get().strip()

    if not tipo or not desc or not monto:
        messagebox.showwarning("Error", "Todos los campos son obligatorios")
        return

    try:
        monto = float(monto)
        if monto <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Error", "El monto debe ser un número positivo")
        return

    saldo_actual = obtener_saldo()

    if tipo == "Gasto" and monto > saldo_actual:
        messagebox.showerror(
            "Saldo insuficiente",
            f"No tienes saldo suficiente.\nSaldo actual: ${saldo_actual:,.2f}"
        )
        return

    cursor.execute("""
        INSERT INTO transacciones (tipo, descripcion, monto, fecha)
        VALUES (?, ?, ?, ?)
    """, (tipo, desc, monto, fecha_actual()))
    conn.commit()

    limpiar_campos()
    mostrar_transacciones()
    actualizar_saldo()
    actualizar_grafica()

def limpiar_campos():
    entry_desc.delete(0, tk.END)
    entry_monto.delete(0, tk.END)
    combo_tipo.set("")

def mostrar_transacciones():
    tree.delete(*tree.get_children())
    cursor.execute("SELECT * FROM transacciones ORDER BY fecha DESC")

    saldo = 0
    for fila in cursor.fetchall():
        tipo, monto = fila[1], fila[3]
        saldo += monto if tipo == "Ingreso" else -monto

        tag = "positivo" if saldo >= 0 else "negativo"
        tree.insert("", tk.END, values=(*fila, f"{saldo:,.2f}"), tags=(tag,))

def eliminar_transaccion():
    seleccionado = tree.selection()
    if not seleccionado:
        messagebox.showwarning("Atención", "Selecciona un registro")
        return

    valores = tree.item(seleccionado)["values"]
    id_transaccion = valores[0]

    if messagebox.askyesno("Confirmar", "¿Eliminar este registro?"):
        cursor.execute("DELETE FROM transacciones WHERE id = ?", (id_transaccion,))
        conn.commit()
        mostrar_transacciones()
        actualizar_saldo()
        actualizar_grafica()

# ------------------------------
# GRÁFICA
# ------------------------------

def actualizar_grafica():
    cursor.execute("SELECT tipo, SUM(monto) FROM transacciones GROUP BY tipo")
    datos = cursor.fetchall()

    tipos = [d[0] for d in datos]
    montos = [d[1] for d in datos]

    fig.clear()
    ax = fig.add_subplot(111)
    colores = ["green" if t == "Ingreso" else "red" for t in tipos]

    ax.bar(tipos, montos, color=colores)
    ax.set_title("Ingresos vs Gastos")
    ax.set_ylabel("Monto")

    canvas.draw()

# ------------------------------
# EXPORTAR EXCEL
# ------------------------------

def exportar_excel():
    ruta = filedialog.asksaveasfilename(defaultextension=".xlsx")
    if not ruta:
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Finanzas"

    ws.append(["ID", "Tipo", "Descripción", "Monto", "Fecha"])
    cursor.execute("SELECT * FROM transacciones")
    for fila in cursor.fetchall():
        ws.append(fila)

    wb.save(ruta)
    messagebox.showinfo("Éxito", "Excel exportado correctamente")

# ------------------------------
# EXPORTAR PDF
# ------------------------------

def exportar_pdf():
    ruta = filedialog.asksaveasfilename(defaultextension=".pdf")
    if not ruta:
        return

    fig.savefig("grafica_temp.png")

    doc = SimpleDocTemplate(ruta)
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph("Reporte Financiero", estilos["Title"]),
        Spacer(1, 12)
    ]

    cursor.execute("SELECT * FROM transacciones")
    tabla = [["ID", "Tipo", "Descripción", "Monto", "Fecha"]]
    tabla.extend(cursor.fetchall())

    elementos.append(Table(tabla))
    elementos.append(Spacer(1, 20))
    elementos.append(Image("grafica_temp.png", 400, 300))

    doc.build(elementos)
    messagebox.showinfo("Éxito", "PDF exportado correctamente")

# ------------------------------
# INTERFAZ
# ------------------------------

root = tk.Tk()
root.title("Sistema de Finanzas Profesional")
root.geometry("1100x750")

lbl_fecha = tk.Label(root, font=("Arial", 10, "bold"))
lbl_fecha.pack()
actualizar_reloj()

lbl_saldo = tk.Label(root, font=("Arial", 12, "bold"))
lbl_saldo.pack(pady=5)

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="Tipo").grid(row=0, column=0)
combo_tipo = ttk.Combobox(frame, values=["Ingreso", "Gasto"], state="readonly")
combo_tipo.grid(row=0, column=1)

tk.Label(frame, text="Descripción").grid(row=1, column=0)
entry_desc = tk.Entry(frame, width=30)
entry_desc.grid(row=1, column=1)

tk.Label(frame, text="Monto").grid(row=2, column=0)
entry_monto = tk.Entry(frame)
entry_monto.grid(row=2, column=1)

tk.Button(frame, text="Agregar", command=agregar_transaccion).grid(row=3, columnspan=2, pady=5)

tree = ttk.Treeview(
    root,
    columns=("ID", "Tipo", "Descripción", "Monto", "Fecha", "Saldo"),
    show="headings"
)

for col in tree["columns"]:
    tree.heading(col, text=col)

tree.tag_configure("positivo", foreground="green")
tree.tag_configure("negativo", foreground="red")
tree.pack(pady=10)

fig = plt.Figure(figsize=(6, 4))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

botones = tk.Frame(root)
botones.pack(pady=10)

tk.Button(botones, text="Exportar Excel", command=exportar_excel).grid(row=0, column=0, padx=5)
tk.Button(botones, text="Exportar PDF", command=exportar_pdf).grid(row=0, column=1, padx=5)
tk.Button(botones, text="Eliminar Registro", command=eliminar_transaccion,
          bg="#c0392b", fg="white").grid(row=0, column=2, padx=5)

mostrar_transacciones()
actualizar_saldo()
actualizar_grafica()

root.mainloop()