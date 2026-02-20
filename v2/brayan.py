import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# =============================
# BASE DE DATOS
# =============================
conn = sqlite3.connect("finanzas.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transacciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    monto REAL NOT NULL,
    fecha TEXT NOT NULL
)
""")
conn.commit()

# =============================
# FUNCIONES LÓGICAS
# =============================
def fecha_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def obtener_saldo():
    cursor.execute("""
        SELECT IFNULL(SUM(
            CASE WHEN tipo='Ingreso' THEN monto ELSE -monto END
        ),0)
        FROM transacciones
    """)
    return cursor.fetchone()[0]

def actualizar_saldo():
    saldo = obtener_saldo()
    lbl_saldo.config(
        text=f"Saldo actual: ${saldo:,.2f}",
        fg="green" if saldo >= 0 else "red"
    )

def agregar():
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
        messagebox.showerror("Error", "Monto inválido")
        return

    if tipo == "Gasto" and monto > obtener_saldo():
        messagebox.showerror("Saldo insuficiente", "No hay saldo suficiente")
        return

    cursor.execute(
        "INSERT INTO transacciones VALUES (NULL, ?, ?, ?, ?)",
        (tipo, desc, monto, fecha_actual())
    )
    conn.commit()

    limpiar()
    mostrar()
    actualizar_saldo()
    actualizar_grafica()

def limpiar():
    entry_desc.delete(0, tk.END)
    entry_monto.delete(0, tk.END)
    combo_tipo.set("")

def mostrar():
    tree.delete(*tree.get_children())
    cursor.execute("SELECT * FROM transacciones ORDER BY fecha")
    saldo = 0

    for fila in cursor.fetchall():
        saldo += fila[3] if fila[1] == "Ingreso" else -fila[3]
        tag = "positivo" if saldo >= 0 else "negativo"
        tree.insert("", tk.END, values=(*fila, f"{saldo:,.2f}"), tags=(tag,))

def eliminar():
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Atención", "Selecciona un registro")
        return

    id_trans = tree.item(sel)["values"][0]
    if messagebox.askyesno("Confirmar", "¿Eliminar esta transacción?"):
        cursor.execute("DELETE FROM transacciones WHERE id=?", (id_trans,))
        conn.commit()
        mostrar()
        actualizar_saldo()
        actualizar_grafica()

# =============================
# GRÁFICA
# =============================
def actualizar_grafica():
    cursor.execute("SELECT tipo, SUM(monto) FROM transacciones GROUP BY tipo")
    datos = cursor.fetchall()

    fig.clear()
    ax = fig.add_subplot(111)

    if datos:
        tipos = [d[0] for d in datos]
        montos = [d[1] for d in datos]
        colores = ["green" if t == "Ingreso" else "red" for t in tipos]
        ax.bar(tipos, montos, color=colores)

    ax.set_title("Ingresos vs Gastos")
    ax.set_ylabel("Monto")
    canvas.draw()

# =============================
# INTERFAZ
# =============================
root = tk.Tk()
root.title("EL BRAYAN CASH")
root.geometry("1100x750")

# ---------- HEADER PROFESIONAL ----------
header = tk.Frame(root, bg="#1f4fd8", height=80)
header.pack(fill="x")
header.pack_propagate(False)

logo_canvas = tk.Canvas(header, width=60, height=60, bg="#1f4fd8", highlightthickness=0)
logo_canvas.pack(side="left", padx=20)

logo_canvas.create_oval(5, 5, 55, 55, fill="white", outline="")
logo_canvas.create_text(
    30, 30,
    text="BC",
    font=("Arial", 20, "bold"),
    fill="#1f4fd8"
)

texto_banco = tk.Frame(header, bg="#1f4fd8")
texto_banco.pack(side="left")

tk.Label(
    texto_banco,
    text="EL BRAYAN CASH",
    bg="#1f4fd8",
    fg="white",
    font=("Arial", 20, "bold")
).pack(anchor="w")

tk.Label(
    texto_banco,
    text="Sistema de Gestión Financiera",
    bg="#1f4fd8",
    fg="#dbe3ff",
    font=("Arial", 11)
).pack(anchor="w")

# ---------- SALDO ----------
lbl_saldo = tk.Label(root, font=("Arial", 14, "bold"))
lbl_saldo.pack(pady=10)

# ---------- FORMULARIO (TARJETA) ----------
card = tk.Frame(root, bg="white", bd=1, relief="solid")
card.pack(pady=15, padx=30)

form = tk.Frame(card, bg="white")
form.pack(padx=20, pady=15)

tk.Label(form, text="Tipo", bg="white").grid(row=0, column=0, sticky="w")
combo_tipo = ttk.Combobox(form, values=["Ingreso", "Gasto"], state="readonly")
combo_tipo.grid(row=0, column=1)

tk.Label(form, text="Descripción", bg="white").grid(row=1, column=0, sticky="w")
entry_desc = tk.Entry(form, width=30)
entry_desc.grid(row=1, column=1)

tk.Label(form, text="Monto", bg="white").grid(row=2, column=0, sticky="w")
entry_monto = tk.Entry(form)
entry_monto.grid(row=2, column=1)

tk.Button(form, text="Agregar", command=agregar).grid(row=3, columnspan=2, pady=8)

# ---------- TABLA ----------
style = ttk.Style()
style.theme_use("default")

style.configure(
    "Treeview",
    rowheight=28,
    font=("Arial", 10)
)

style.configure(
    "Treeview.Heading",
    background="#1f4fd8",
    foreground="white",
    font=("Arial", 10, "bold")
)

tree = ttk.Treeview(
    root,
    columns=("ID", "Tipo", "Descripción", "Monto", "Fecha", "Saldo"),
    show="headings"
)
tree.pack(fill="both", expand=True, padx=20, pady=10)

for col in tree["columns"]:
    tree.heading(col, text=col)

tree.tag_configure("positivo", foreground="green")
tree.tag_configure("negativo", foreground="red")

# ---------- BOTÓN ELIMINAR ----------
tk.Button(root, text="Eliminar Transacción", bg="red", fg="white", command=eliminar).pack(pady=5)

# ---------- GRÁFICA ----------
fig = plt.Figure(figsize=(6, 4))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(pady=10)

mostrar()
actualizar_saldo()
actualizar_grafica()

root.mainloop()