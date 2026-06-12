import tkinter as tk
from tkinter import ttk, messagebox
from logic.ipr_models import IPRModels
from ui.graph_widget import GraphWidget

class IPRTab(ttk.Frame):
    def __init__(self, parent, well_type_var=None):
        super().__init__(parent)
        self.well_type_var = well_type_var
        self.entries = {}  # Diccionario para guardar referencias a los inputs dinámicos
        self.setup_ui()

    def setup_ui(self):
        from ui.styles import VioletTheme
        c = VioletTheme.get_colors()
        
        # --- DISEÑO GENERAL ---
        # Panel Izquierdo: Configuración y Datos (Scrollable si hay muchos datos)
        left_panel = tk.Frame(self, bg=c["BG_COLOR"], width=320)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_panel.pack_propagate(False) # Forzar ancho fijo

        # --- PANEL DERECHO (PanedWindow) ---
        right_panel = ttk.PanedWindow(self, orient=tk.VERTICAL)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- PANEL IZQUIERDO: SELECCIÓN DE MODELO ---
        lbl_frame_model = ttk.LabelFrame(left_panel, text="Selección de Modelo", padding=10)
        lbl_frame_model.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(lbl_frame_model, text="Modelo IPR:").pack(anchor="w")
        self.modelo_cb = ttk.Combobox(
            lbl_frame_model, 
            state="readonly"
        )
        self.modelo_cb.pack(fill=tk.X, pady=5)
        self.modelo_cb.bind("<<ComboboxSelected>>", self.update_input_fields)
        
        # --- PANEL IZQUIERDO: INPUTS DINÁMICOS ---
        self.input_frame = ttk.LabelFrame(left_panel, text="Parámetros de Entrada", padding=10)
        self.input_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Botón Calcular
        btn_calc = ttk.Button(left_panel, text="Calcular Curva IPR", command=self.calculate)
        btn_calc.pack(fill=tk.X, padx=10, pady=20)

        # Panel Superior: Gráfica
        graph_frame = tk.Frame(right_panel, bg=c["BG_COLOR"])
        self.graph = GraphWidget(graph_frame, title="Curva IPR")
        self.graph.pack(fill=tk.BOTH, expand=True)
        right_panel.add(graph_frame, weight=3)

        # Panel Inferior: Tabla de Resultados
        table_frame = ttk.LabelFrame(right_panel, text="Tabla de Resultados (Pwf vs Q)", padding=5)

        # Scrollbar para la tabla
        tree_scroll = ttk.Scrollbar(table_frame, style="Vertical.TScrollbar")
        self.tree = ttk.Treeview(table_frame, columns=("pwf", "q"), show="headings", yscrollcommand=tree_scroll.set, height=6)
        
        self.tree.heading("pwf", text="Presión de Fondo (psi)")
        self.tree.heading("q", text="Caudal (STB/d)")
        self.tree.column("pwf", anchor="center", width=100)
        self.tree.column("q", anchor="center", width=100)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        tree_scroll.config(command=self.tree.yview)
        
        right_panel.add(table_frame, weight=1)

        # Inicializar modelos basados en la variable global
        self.on_well_type_changed()

    def on_well_type_changed(self):
        if not self.well_type_var: return
        wt = self.well_type_var.get()
        if wt == "Vertical":
            models = ["Vogel (Subsaturado)", "Fetkovich-gas", "Wiggins", "Darcy (Semi-Estacionario)", "Brown"]
        else:
            models = ["Joshi Horizontal", "Babu y Odeh", "Vogel Modificado (Kabir)", "Economides y Retnanto", "Bendakhlia y Aziz", "Cheng"]
        
        self.modelo_cb['values'] = models
        if models:
            self.modelo_cb.current(0)
        self.update_input_fields()

    def update_input_fields(self, event=None):
        """Limpia y regenera los campos de entrada según el modelo seleccionado."""
        # Limpiar campos anteriores
        for widget in self.input_frame.winfo_children():
            widget.destroy()
        self.entries.clear()

        model = self.modelo_cb.get()

        # Generar campos según selección
        if model == "Fetkovich-gas":
            self.create_entry("Presión Yac. (psi):", "pres", "3000")
            self.create_entry("Coeficiente C (Mscf/d/psi²ⁿ):", "c_fet", "0.5")
            self.create_entry("Exponente n:", "n_fet", "1.0")
        elif model == "Wiggins":
            self.create_entry("Presión Yac. (psi):", "pres", "4000")
            self.create_entry("P Burbuja Pb (psi):", "pb", "3000")
            self.create_entry("Índice Prod J:", "j_index", "1.5")
        elif "Darcy" in model:
            self.create_entry("Presión Yac. (psi):", "pres", "3000")
            self.create_entry("Permeabilidad k (md):", "k", "50")
            self.create_entry("Espesor h (ft):", "h", "30")
            self.create_entry("Viscosidad μ (cp):", "mu", "1.5")
            self.create_entry("Factor Vol. Bo:", "bo", "1.2")
            self.create_entry("Radio Drenaje re (ft):", "re", "1000")
            self.create_entry("Radio Pozo rw (ft):", "rw", "0.328")
            self.create_entry("Skin (s):", "skin", "0")
        elif model == "Vogel (Subsaturado)":
            self.create_entry("Presión Yac. (psi):", "pres", "4000")
            self.create_entry("P Burbuja Pb (psi):", "pb", "3000")
            self.create_entry("Índice Prod J:", "j_index", "1.5")
        elif model == "Brown":
            self.create_entry("Presión Yac. (psi):", "pres", "3000")
            self.create_entry("P Burbuja Pb (psi):", "pb", "1500")
            self.create_entry("Índice Prod J:", "j_index", "1.5")
            self.create_entry("Water Cut %:", "w_cut", "20")
        elif model == "Cheng":
            self.create_entry("Presión Yac. (psi):", "pres", "3000")
            self.create_entry("P Burbuja Pb (psi):", "pb", "3000")
            self.create_entry("Ángulo (°):", "angle", "90")
            self.create_entry("Permeabilidad kH (md):", "kh", "100")
            self.create_entry("Permeabilidad kV (md):", "kv", "10")
            self.create_entry("Espesor h (ft):", "h", "100")
            self.create_entry("Viscosidad μ (cp):", "mu", "2.0")
            self.create_entry("Factor Vol. Bo:", "bo", "1.2")
            self.create_entry("Longitud Pozo L (ft):", "L", "2000")
            self.create_entry("Radio Drenaje reH (ft):", "reh", "1500")
            self.create_entry("Radio Pozo rw (ft):", "rw", "0.328")
            self.create_entry("Skin (s):", "skin", "0")
        elif model == "Economides y Retnanto":
            self.create_entry("Presión Yac. (psi):", "pres", "4000")
            self.create_entry("P Burbuja Pb (psi):", "pb", "3000")
            self.create_entry("Permeabilidad kH (md):", "kh", "100")
            self.create_entry("Permeabilidad kV (md):", "kv", "10")
            self.create_entry("Espesor h (ft):", "h", "100")
            self.create_entry("Viscosidad μ (cp):", "mu", "2.0")
            self.create_entry("Factor Vol. Bo:", "bo", "1.2")
            self.create_entry("Longitud Pozo L (ft):", "L", "2000")
            self.create_entry("Radio Drenaje reH (ft):", "reh", "1500")
            self.create_entry("Radio Pozo rw (ft):", "rw", "0.328")
            self.create_entry("Skin (s):", "skin", "0")
        elif model == "Joshi Horizontal":
            self.create_entry("Presión Yac. (psi):", "pres", "3000")
            self.create_entry("Permeabilidad kH (md):", "kh", "100")
            self.create_entry("Permeabilidad kV (md):", "kv", "10")
            self.create_entry("Espesor h (ft):", "h", "100")
            self.create_entry("Viscosidad μ (cp):", "mu", "2.0")
            self.create_entry("Factor Vol. Bo:", "bo", "1.2")
            self.create_entry("Longitud Pozo L (ft):", "L", "2000")
            self.create_entry("Radio Drenaje reH (ft):", "reh", "1500")
            self.create_entry("Radio Pozo rw (ft):", "rw", "0.328")
            self.create_entry("Skin (s):", "skin", "0")
        elif model == "Babu y Odeh":
            self.create_entry("Presión Yac. (psi):", "pres", "3000")
            self.create_entry("Permeabilidad kx (md):", "kx", "100")
            self.create_entry("Permeabilidad ky (md):", "ky", "100")
            self.create_entry("Permeabilidad kz (md):", "kz", "10")
            self.create_entry("Espesor Yac. h (ft):", "h", "100")
            self.create_entry("Dimensión X 'a' (ft):", "a_res", "2000")
            self.create_entry("Dimensión Y 'b' (ft):", "b_res", "1500")
            self.create_entry("Viscosidad μ (cp):", "mu", "2.0")
            self.create_entry("Factor Vol. Bo:", "bo", "1.2")
            self.create_entry("Longitud Pozo L (ft):", "L", "1000")
            self.create_entry("Radio Pozo rw (ft):", "rw", "0.328")
            self.create_entry("Posición x_mid (ft):", "x_mid", "1000")
            self.create_entry("Posición y_0 (ft):", "y_0", "750")
            self.create_entry("Posición z_0 (ft):", "z_0", "50")
            self.create_entry("Daño de Formación (s):", "s_res", "0")
        elif model == "Vogel Modificado (Kabir)":
            self.create_entry("Presión Yac. (psi):", "pres", "4000")
            self.create_entry("Presión Burbuja Pb (psi):", "pb", "3000")
            self.create_entry("Permeabilidad kH (md):", "kh", "100")
            self.create_entry("Permeabilidad kV (md):", "kv", "10")
            self.create_entry("Espesor h (ft):", "h", "100")
            self.create_entry("Viscosidad μ (cp):", "mu", "2.0")
            self.create_entry("Factor Vol. Bo:", "bo", "1.2")
            self.create_entry("Longitud Pozo L (ft):", "L", "2000")
            self.create_entry("Radio Drenaje reH (ft):", "reh", "1500")
            self.create_entry("Radio rw (ft):", "rw", "0.328")
            self.create_entry("Skin (s):", "skin", "0")
        elif model == "Bendakhlia y Aziz":
            self.create_entry("Presión Yac. (psi):", "pres", "3000")
            self.create_entry("P Burbuja Pb (psi):", "pb", "3000")
            self.create_entry("Factor de Recobro (Frac):", "rec_factor", "0.05")
            self.create_entry("Permeabilidad kH (md):", "kh", "100")
            self.create_entry("Permeabilidad kV (md):", "kv", "10")
            self.create_entry("Espesor h (ft):", "h", "100")
            self.create_entry("Viscosidad μ (cp):", "mu", "2.0")
            self.create_entry("Factor Vol. Bo:", "bo", "1.2")
            self.create_entry("Longitud Pozo L (ft):", "L", "2000")
            self.create_entry("Radio Drenaje reH (ft):", "reh", "1500")
            self.create_entry("Radio Pozo rw (ft):", "rw", "0.328")
            self.create_entry("Skin (s):", "skin", "0")
            
            # Botón para mostrar la regresión
            ttk.Button(self.input_frame, text="Ver Regresión (n y V)", command=self.show_nv_regression).pack(pady=10)

        # Notify VLP tab to update its fields and adjust headers based on fluid/language
        from ui.i18n import I18N
        self.tree.heading("pwf", text="Presión de Fondo (psi)" if I18N._lang == "es" else "Bottomhole Pressure (psi)")
        if model == "Fetkovich-gas":
            self.tree.heading("q", text="Caudal (Mscf/d)" if I18N._lang == "es" else "Flow Rate (Mscf/d)")
        else:
            self.tree.heading("q", text="Caudal (STB/d)" if I18N._lang == "es" else "Flow Rate (STB/d)")
            
        try:
            if hasattr(self.master, "master") and hasattr(self.master.master, "tab_vlp"):
                vlp_tab = self.master.master.tab_vlp
                if hasattr(vlp_tab, "update_fields_for_fluid_type"):
                    vlp_tab.update_fields_for_fluid_type()
        except Exception:
            pass

    def show_nv_regression(self):
        import tkinter as tk
        import numpy as np
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        from ui.styles import VioletTheme
        
        try:
            current_x = self.get_float("rec_factor")
        except:
            current_x = 0.05
            
        c = VioletTheme.get_colors()
        win = tk.Toplevel(self)
        win.title("Regresiones Bendakhlia y Aziz")
        win.geometry("600x550")
        win.configure(bg=c["BG_COLOR"])
        
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor(c["BG_COLOR"])
        ax.set_facecolor(c["FRAME_BG"])
        ax.tick_params(colors=c["TEXT_COLOR"])
        for spine in ax.spines.values(): spine.set_color(c["TEXT_COLOR"])
        
        # Generar curva estrictamente en el rango de los datos (0 a 0.14)
        x_vals = np.linspace(0.0, 0.14, 100)
        n_vals = 98.395 * (x_vals**2) - 13.587 * x_vals + 1.35
        # Coeficientes precisos para evitar distorsión visual
        v_vals = 355651 * (x_vals**6) - 297459 * (x_vals**5) + 91175 * (x_vals**4) - 12584 * (x_vals**3) + 837.55 * (x_vals**2) - 25.12 * x_vals + 0.378
        v_vals = np.clip(v_vals, 0.01, None)
        
        ax.plot(x_vals, n_vals, label="n (Exponente)", color="#3498DB", linewidth=2, linestyle='dotted')
        ax.plot(x_vals, v_vals, label="V (Factor)", color="#E67E22", linewidth=2, linestyle='dotted')
        
        # Marcar punto actual
        if current_x > 0.14: current_x = 0.14
        if current_x < 0: current_x = 0
            
        curr_n = 98.395 * (current_x**2) - 13.587 * current_x + 1.35
        curr_v = 355651 * (current_x**6) - 297459 * (current_x**5) + 91175 * (current_x**4) - 12584 * (current_x**3) + 837.55 * (current_x**2) - 25.12 * current_x + 0.378
        curr_v = max(0.01, curr_v)
        ax.axvline(x=current_x, color='#E74C3C', linestyle='-', alpha=0.5)
        ax.plot(current_x, curr_n, marker='o', markersize=8, color="#3498DB")
        ax.plot(current_x, curr_v, marker='o', markersize=8, color="#E67E22")
        
        ax.set_title(f"Parámetros con Factor Recobro = {current_x:.3f}\nn={curr_n:.3f}, V={curr_v:.3f}", color=c["TEXT_COLOR"])
        ax.set_xlabel("Factor de Recobro (fracción)", color=c["TEXT_COLOR"])
        ax.set_ylabel("Valor del Parámetro", color=c["TEXT_COLOR"])
        ax.set_xlim(-0.01, 0.15)
        ax.set_ylim(0, 1.6)
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.legend(facecolor=c["BG_COLOR"], edgecolor=c["TEXT_COLOR"], labelcolor=c["TEXT_COLOR"])
        
        # Add Toolbar for Zooming in Popup as well
        canvas = FigureCanvasTkAgg(fig, win)
        toolbar_frame = tk.Frame(win, bg=c["BG_COLOR"])
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_entry(self, label_text, key, default_val):
        """Helper para crear filas de inputs."""
        from ui.styles import VioletTheme
        c = VioletTheme.get_colors()
        
        frame = tk.Frame(self.input_frame, bg=c["BG_COLOR"])
        frame.pack(fill=tk.X, pady=2)
        
        lbl = tk.Label(frame, text=label_text, width=20, anchor="w", bg=c["BG_COLOR"], fg=c["TEXT_COLOR"])
        lbl.pack(side=tk.LEFT)
        
        entry = ttk.Entry(frame)
        entry.insert(0, default_val)
        entry.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        
        self.entries[key] = entry

    def get_float(self, key):
        """Obtiene valor float de un entry, maneja errores."""
        try:
            val = self.entries[key].get()
            return float(val)
        except (ValueError, KeyError):
            return 0.0

    def calculate(self):
        try:
            # Limpiar gráfica y tabla previa
            self.tree.delete(*self.tree.get_children())
            
            model = self.modelo_cb.get()
            q_res, p_res = [], []

            # Lógica de cálculo según modelo
            if model == "Fetkovich-gas":
                q_res, p_res = IPRModels.fetkovich(self.get_float("c_fet"), self.get_float("n_fet"), self.get_float("pres"))
            elif model == "Wiggins":
                q_res, p_res = IPRModels.wiggins(self.get_float("pres"), self.get_float("pb"), self.get_float("j_index"))
            elif "Darcy" in model:
                q_res, p_res = IPRModels.darcy(self.get_float("k"), self.get_float("h"), self.get_float("mu"), self.get_float("bo"), self.get_float("re"), self.get_float("rw"), self.get_float("skin"), self.get_float("pres"))
            elif model == "Economides y Retnanto":
                import warnings as _warnings
                with _warnings.catch_warnings(record=True) as caught:
                    _warnings.simplefilter("always", UserWarning)
                    q_res, p_res = IPRModels.economides_retnanto(
                        self.get_float("kh"), self.get_float("kv"), self.get_float("h"),
                        self.get_float("mu"), self.get_float("bo"), self.get_float("L"),
                        self.get_float("reh"), self.get_float("rw"), self.get_float("skin"),
                        self.get_float("pres"), self.get_float("pb")
                    )
                for w in caught:
                    if issubclass(w.category, UserWarning):
                        messagebox.showwarning("Economides–Retnanto — fuera de rango", str(w.message))
            elif model == "Vogel (Subsaturado)":
                q_res, p_res = IPRModels.vogel_subsaturado(self.get_float("pres"), self.get_float("pb"), self.get_float("j_index"))
            elif model == "Brown":
                q_res, p_res = IPRModels.brown(
                    self.get_float("pres"), self.get_float("pb"),
                    self.get_float("j_index"), self.get_float("w_cut")
                )
            elif model == "Cheng":
                q_res, p_res = IPRModels.cheng(
                    self.get_float("kh"), self.get_float("kv"), self.get_float("h"),
                    self.get_float("mu"), self.get_float("bo"), self.get_float("L"),
                    self.get_float("reh"), self.get_float("rw"), self.get_float("skin"),
                    self.get_float("pres"), self.get_float("pb"), self.get_float("angle")
                )
            elif model == "Joshi Horizontal":
                q_res, p_res = IPRModels.joshi(self.get_float("kh"), self.get_float("kv"), self.get_float("h"), self.get_float("mu"), self.get_float("bo"), self.get_float("L"), self.get_float("reh"), self.get_float("rw"), self.get_float("skin"), self.get_float("pres"))
            elif model == "Babu y Odeh":
                q_res, p_res = IPRModels.babu_odeh(self.get_float("kx"), self.get_float("ky"), self.get_float("kz"), self.get_float("h"), self.get_float("a_res"), self.get_float("b_res"), self.get_float("mu"), self.get_float("bo"), self.get_float("L"), self.get_float("rw"), self.get_float("x_mid"), self.get_float("y_0"), self.get_float("z_0"), self.get_float("s_res"), self.get_float("pres"))
            elif model == "Vogel Modificado (Kabir)":
                q_res, p_res = IPRModels.vogel_kabir(self.get_float("kh"), self.get_float("kv"), self.get_float("h"), self.get_float("mu"), self.get_float("bo"), self.get_float("L"), self.get_float("reh"), self.get_float("rw"), self.get_float("skin"), self.get_float("pres"), self.get_float("pb"))
            elif model == "Bendakhlia y Aziz":
                q_res, p_res = IPRModels.bendakhlia_aziz(
                    self.get_float("kh"), self.get_float("kv"), self.get_float("h"),
                    self.get_float("mu"), self.get_float("bo"), self.get_float("L"),
                    self.get_float("reh"), self.get_float("rw"), self.get_float("skin"),
                    self.get_float("pres"), self.get_float("pb"), self.get_float("rec_factor")
                )

            # Graficar — paleta unificada de la HU-006 (pasteles morados).
            from ui.styles import IPR_MODEL_COLORS, IPR_PALETTE
            from ui.i18n import I18N
            color = IPR_MODEL_COLORS.get(model, IPR_PALETTE[0])
            
            xlabel = I18N.get("q_label_gas") if model == "Fetkovich-gas" else I18N.get("q_label")
            self.graph.plot_curve(q_res, p_res, f"IPR - {model}", color, clear=True, xlabel=xlabel, ylabel="Pwf [psi]", title="Curva IPR")

            # Llenar Tabla (Invertimos el orden para mostrar desde Pwf alta a baja o viceversa)
            # Normalmente se muestra de Pwf alta (Q=0) a Pwf baja (Qmax)
            # Los arrays vienen de 0 psi a Pres. Vamos a invertirlos para la tabla visualmente
            
            p_display = p_res[::-1]
            q_display = q_res[::-1]

            for q, p in zip(q_display, p_display):
                self.tree.insert("", "end", values=(f"{p:.2f}", f"{q:.2f}"))

        except ValueError as ve:
            messagebox.showwarning("Error en Datos", f"Verifique los valores numéricos.\n{str(ve)}")
        except Exception as e:
            messagebox.showerror("Error Crítico", f"Ocurrió un error en el cálculo:\n{str(e)}")