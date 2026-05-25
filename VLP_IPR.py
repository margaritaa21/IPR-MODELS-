import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
from PIL import Image, ImageTk

# ===================== SPLASH SCREEN =====================
def mostrar_splash():
    # el splash va a ser la PRIMERA ventana (Tk)
    splash = tk.Tk()
    splash.overrideredirect(True)  # sin marco ni título
    splash.config(bg="#000000")    # fondo negro (como tu sello)

    # tamaño del logo
    logo_size = (300, 300)

    # cargar logo del splash
    try:
        logo = Image.open("logo_splash.png")  # <-- tu sello de entrada
        logo = logo.resize(logo_size)
        logo_tk = ImageTk.PhotoImage(logo)
        lbl_logo = tk.Label(splash, image=logo_tk, bg="#000000")
        lbl_logo.image = logo_tk  # para que no lo libere
        lbl_logo.pack()
    except Exception:
        tk.Label(
            splash,
            text="(Logo no encontrado)",
            bg="#000000",
            fg="white",
            font=("Century Gothic", 12, "bold")
        ).pack(pady=80)

    # centrar splash
    w, h = logo_size
    ws = splash.winfo_screenwidth()
    hs = splash.winfo_screenheight()
    x = (ws // 2) - (w // 2)
    y = (hs // 2) - (h // 2)
    splash.geometry(f"{w}x{h}+{x}+{y}")

    # después de 2.5 s cerramos splash y abrimos la app
    splash.after(2500, lambda: (splash.destroy(), abrir_ventana_principal()))
    splash.mainloop()

# ===================== PROGRAMA PRINCIPAL =====================
def abrir_ventana_principal():
    root = tk.Tk()
    root.title("VIOLET")
    root.geometry("750x500")
    root.configure(bg="#E8D8F1")  # lavanda claro

    # ---- FUENTES ----
    title_font = tkfont.Font(family="Century Gothic", size=14, weight="bold")
    section_font = tkfont.Font(family="Century Gothic", size=11, weight="bold")
    body_font = tkfont.Font(family="Century Gothic", size=10)

    # hacer que ttk también use Century Gothic
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(".", font=("Century Gothic", 10))  # todo ttk con Century Gothic

    # ---- HEADER ----
    header = tk.Frame(root, bg="#5D3A7A", height=60)
    header.pack(fill="x")
    tk.Label(
        header,
        text="🛢️ SISTEMAS DE PRODUCCIÓN",
        bg="#5D3A7A",
        fg="#F9F9F9",
        font=title_font,
        anchor="center"
    ).pack(fill="both", expand=True)

    # ---- Estilos TTK de colores ----
    style.configure("TNotebook", background="#E8D8F1", borderwidth=0)
    style.configure("TNotebook.Tab", background="#8A56AC", foreground="#F9F9F9", padding=(10, 5))
    style.map("TNotebook.Tab",
              background=[("selected", "#5D3A7A")],
              foreground=[("selected", "#FFFFFF")])
    style.configure("TFrame", background="#DCC7E1")
    style.configure("TLabel", background="#DCC7E1", foreground="#2E2133")
    style.configure("TButton", padding=5)

    # ---- NOTEBOOK ----
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # ===================== PESTAÑA 1: INICIO =====================
    inicio_tab = ttk.Frame(notebook)
    notebook.add(inicio_tab, text="Inicio")

    inicio_container = tk.Frame(inicio_tab, bg="#DCC7E1")
    inicio_container.pack(expand=True, fill="both")

    tk.Label(
        inicio_container,
        text="¿Qué deseas calcular?",
        bg="#DCC7E1",
        fg="#2E2133",
        font=section_font
    ).pack(pady=15)

    ttk.Button(
        inicio_container,
        text="IPR",
        command=lambda: ir_a_tab("ipr", notebook)
    ).pack(pady=5, ipadx=10)

    ttk.Button(
        inicio_container,
        text="VLP",
        command=lambda: ir_a_tab("vlp", notebook)
    ).pack(pady=5, ipadx=10)

    tk.Label(
        inicio_container,
        text="Selecciona un módulo para continuar.",
        bg="#DCC7E1",
        fg="#5D3A7A",
        font=body_font
    ).pack(pady=10)

    # -------- IMAGEN DE INICIO --------
    img_frame = tk.Frame(inicio_container, bg="#DCC7E1")
    img_frame.pack(pady=15)

    try:
        img = Image.open("IMG.png")   # <-- aquí va la de la pantalla principal
        img = img.resize((160, 160))
        img_tk = ImageTk.PhotoImage(img)
        lbl_img = tk.Label(img_frame, image=img_tk, bg="#DCC7E1")
        lbl_img.image = img_tk
        lbl_img.pack()
    except Exception:
        tk.Label(
            img_frame,
            text="(Agrega IMG.png en la carpeta)",
            bg="#DCC7E1",
            fg="#8A56AC",
            font=body_font
        ).pack(pady=10)

    # ===================== PESTAÑA 2: IPR =====================
    ipr_tab = ttk.Frame(notebook)
    notebook.add(ipr_tab, text="IPR")
    notebook.tab(ipr_tab, state="disabled")

    tk.Label(
        ipr_tab,
        text="IPR",
        font=section_font,
        bg="#DCC7E1",
        fg="#2E2133"
    ).pack(pady=10, anchor="w", padx=10)

    ipr_frame = tk.Frame(ipr_tab, bg="#DCC7E1")
    ipr_frame.pack(pady=10, padx=10, fill="x")

    tk.Label(ipr_frame, text="Modelo:", bg="#DCC7E1").grid(row=0, column=0, sticky="w", pady=5)
    modelo_cb = ttk.Combobox(ipr_frame, values=["Vogel", "Lineal", "Joshi Horizontal"], state="readonly", width=20)
    modelo_cb.current(0)
    modelo_cb.grid(row=0, column=1, pady=5, padx=5, sticky="w")

    tk.Label(ipr_frame, text="P_res (psia):", bg="#DCC7E1").grid(row=1, column=0, sticky="w", pady=5)
    pres_entry = ttk.Entry(ipr_frame, width=22)
    pres_entry.insert(0, "3000")
    pres_entry.grid(row=1, column=1, pady=5, padx=5, sticky="w")

    qmax_label = tk.Label(ipr_frame, text="AOF / q_max (bpd):", bg="#DCC7E1")
    qmax_label.grid(row=2, column=0, sticky="w", pady=5)
    qmax_entry = ttk.Entry(ipr_frame, width=22)
    qmax_entry.insert(0, "1500")
    qmax_entry.grid(row=2, column=1, pady=5, padx=5, sticky="w")

    joshi_frame = tk.Frame(ipr_frame, bg="#DCC7E1")
    joshi_entries = {}
    
    j_fields = [
        ("P_wf (psia):", "pwf", "1500"), ("kH (mD):", "kh", "50"),
        ("h (ft):", "h", "100"), ("mu_o (cp):", "mu_o", "2.0"),
        ("Bo (rb/STB):", "bo", "1.2"), ("a (ft):", "a", "1500"),
        ("L (ft):", "L", "2000"), ("I_ani:", "iani", "1.0"),
        ("rw (ft):", "rw", "0.328"), ("S (Skin):", "S", "0")
    ]
    
    for i, (label_text, key, default_val) in enumerate(j_fields):
        r = i // 2
        c = (i % 2) * 2
        tk.Label(joshi_frame, text=label_text, bg="#DCC7E1").grid(row=r, column=c, sticky="w", pady=2, padx=5)
        ent = ttk.Entry(joshi_frame, width=10)
        ent.insert(0, default_val)
        ent.grid(row=r, column=c+1, pady=2, padx=5)
        joshi_entries[key] = ent

    def update_ipr_ui(event):
        if modelo_cb.get() == "Joshi Horizontal":
            qmax_label.grid_remove()
            qmax_entry.grid_remove()
            joshi_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)
        else:
            joshi_frame.grid_remove()
            qmax_label.grid()
            qmax_entry.grid()

    modelo_cb.bind("<<ComboboxSelected>>", update_ipr_ui)

    ttk.Button(
        ipr_tab,
        text="Calcular IPR",
        command=lambda: calcular_ipr(modelo_cb, pres_entry, qmax_entry, joshi_entries)
    ).pack(pady=15, padx=10, anchor="w")

    # ===================== PESTAÑA 3: VLP =====================
    vlp_tab = ttk.Frame(notebook)
    notebook.add(vlp_tab, text="VLP")
    notebook.tab(vlp_tab, state="disabled")

    tk.Label(
        vlp_tab,
        text="Módulo VLP",
        font=section_font,
        bg="#DCC7E1",
        fg="#2E2133"
    ).pack(pady=10, anchor="w", padx=10)

    tk.Label(
        vlp_tab,
        text="Aquí irían los datos de tubería, profundidad, correlación de gradiente, etc.",
        bg="#DCC7E1",
        fg="#5D3A7A",
        font=body_font
    ).pack(pady=5, padx=10, anchor="w")

    root.mainloop()

# ===================== FUNCIONES AUX =====================
def calcular_ipr(modelo_cb, pres_entry, qmax_entry, joshi_entries=None):
    import math
    modelo = modelo_cb.get()
    try:
        pres = float(pres_entry.get())
        if modelo != "Joshi Horizontal":
            qmax = float(qmax_entry.get())
    except ValueError:
        messagebox.showerror("Error", "Ingresa números válidos.")
        return
        
    if modelo == "Vogel":
        messagebox.showinfo("IPR", f"Modelo Vogel con Pres={pres} psia y qmax={qmax} bpd")
    elif modelo == "Lineal":
        j = qmax / pres if pres != 0 else 0
        messagebox.showinfo("IPR", f"Modelo lineal con Pres={pres} psia y J≈{j:.2f} bpd/psi")
    elif modelo == "Joshi Horizontal":
        if joshi_entries:
            try:
                pwf = float(joshi_entries['pwf'].get())
                kh = float(joshi_entries['kh'].get())
                h = float(joshi_entries['h'].get())
                mu_o = float(joshi_entries['mu_o'].get())
                bo = float(joshi_entries['bo'].get())
                a = float(joshi_entries['a'].get())
                L = float(joshi_entries['L'].get())
                iani = float(joshi_entries['iani'].get())
                rw = float(joshi_entries['rw'].get())
                S = float(joshi_entries['S'].get())
            except ValueError:
                messagebox.showerror("Error", "Ingresa números válidos en Joshi.")
                return
            
            try:
                num = 7.08e-3 * kh * h * (pres - pwf)
                term1 = math.log((a + math.sqrt(a**2 - (L/2)**2)) / (L/2))
                term2 = (iani * h / L) * math.log((iani * h) / (rw * (iani + 1)))
                den = mu_o * bo * (term1 + term2 + S)
                
                qo = num / den
                
                messagebox.showinfo("IPR", f"Modelo Joshi Horizontal\nCaudal estimado qo = {qo:.2f} STB/d")
            except Exception as e:
                messagebox.showerror("Error", f"Error en cálculo: {e}")

def ir_a_tab(tab, notebook):
    if tab == "ipr":
        notebook.tab(1, state="normal")
        notebook.select(1)
    else:
        notebook.tab(2, state="normal")
        notebook.select(2)

# ===================== INICIO =====================
if __name__ == "__main__":
    mostrar_splash()
