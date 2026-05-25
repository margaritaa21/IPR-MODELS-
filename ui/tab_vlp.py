import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from logic.vlp_models import VLPModels
from logic.ipr_models import IPRModels
from ui.graph_widget import GraphWidget

class VLPTab(ttk.Frame):
    def __init__(self, parent, well_type_var=None, ipr_tab=None):
        super().__init__(parent)
        self.well_type_var = well_type_var
        self.ipr_tab = ipr_tab
        self.entries = {}
        self.setup_ui()

    def setup_ui(self):
        from ui.styles import VioletTheme
        c = VioletTheme.get_colors()
        
        # --- LAYOUT PRINCIPAL ---
        # Panel Izquierdo: Inputs de VLP
        # Panel Derecho: Gráfica (Arriba) y Tabla (Abajo)
        
        left_panel = tk.Frame(self, bg=c["BG_COLOR"], width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Canvas para scroll en inputs
        canvas = tk.Canvas(left_panel, bg=c["BG_COLOR"], width=280, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
        self.scroll_frame = ttk.Frame(canvas)
        
        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- SECCIONES DE INPUTS ---
        self.add_section("Geometría Pozo", [
            ("Profundidad (ft)", "8000"),
            ("Tubing ID (in)", "2.441"),
            ("Temp. Cabeza (°F)", "100"),
            ("Temp. Fondo (°F)", "200")
        ])

        self.add_section("Datos Producción", [
            ("P Cabeza (psi)", "150"),
            ("API Petróleo", "30"),
            ("Gravedad Gas", "0.75"),
            ("Gravedad Agua", "1.02"),
            ("Bw (rb/stb)", "1.0"),
            ("GOR (scf/stb)", "800"),
            ("Corte de Agua %", "10")
        ])
        
        # Nota informativa
        info_frame = ttk.LabelFrame(self.scroll_frame, text="Datos IPR", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(info_frame, text="Nota: El modelo IPR y sus datos se\ntomarán automáticamente de la\npestaña 'Curvas IPR'.").pack()

        ttk.Button(self.scroll_frame, text="Calcular Análisis Nodal (31 Pasos)", command=self.calculate_nodal).pack(pady=15, fill=tk.X, padx=10)

        # --- PANEL DERECHO (PanedWindow) ---
        right_panel = ttk.PanedWindow(self, orient=tk.VERTICAL)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Panel Superior: Gráfica
        graph_frame = tk.Frame(right_panel, bg=c["BG_COLOR"])
        self.graph = GraphWidget(graph_frame, title="Análisis Nodal (VLP vs IPR)")
        self.graph.pack(fill=tk.BOTH, expand=True)
        right_panel.add(graph_frame, weight=3) # Dale más peso inicial a la gráfica
        
        # Panel Inferior: Tabla de Variables
        table_labelframe = ttk.LabelFrame(right_panel, text="Variables calculadas (Último Punto VLP)", padding=5)
        
        self.tree = ttk.Treeview(table_labelframe, columns=("Variable", "Valor"), show="headings", height=8)
        self.tree.heading("Variable", text="Paso / Variable")
        self.tree.heading("Valor", text="Valor Calculado")
        self.tree.column("Variable", width=200)
        self.tree.column("Valor", width=150)
        
        vsb = ttk.Scrollbar(table_labelframe, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        right_panel.add(table_labelframe, weight=1)

    def add_section(self, title, fields):
        frame = ttk.LabelFrame(self.scroll_frame, text=title, padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)
        for i, (lbl, default) in enumerate(fields):
            ttk.Label(frame, text=lbl).grid(row=i, column=0, sticky="w")
            entry = ttk.Entry(frame, width=10)
            entry.insert(0, default)
            entry.grid(row=i, column=1, padx=5)
            self.entries[lbl] = entry

    def get_val(self, key_fragment):
        for k, v in self.entries.items():
            if key_fragment in k:
                try:
                    return float(v.get())
                except ValueError:
                    return 0.0
        return 0.0

    def calculate_nodal(self):
        if not self.ipr_tab:
            messagebox.showerror("Error", "Referencia a pestaña IPR no encontrada.")
            return

        try:
            # Limpiar tabla
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # Extraer Datos IPR de la pestaña IPRTab
            model = self.ipr_tab.modelo_cb.get()
            pres_res = self.ipr_tab.get_float("pres")
            
            if pres_res <= 0:
                 messagebox.showwarning("Datos IPR", "Ve a la pestaña IPR y configura una Presión de Yacimiento > 0.")
                 return

            if model == "Vogel (Subsaturado)":
                q_ipr, p_ipr = IPRModels.vogel_subsaturado(pres_res, self.ipr_tab.get_float("pb"), self.ipr_tab.get_float("j_index"))
            elif model == "Fetkovich-gas":
                q_ipr, p_ipr = IPRModels.fetkovich(self.ipr_tab.get_float("c_fet"), self.ipr_tab.get_float("n_fet"), pres_res)
            elif model == "Wiggins":
                q_ipr, p_ipr = IPRModels.wiggins(pres_res, self.ipr_tab.get_float("pb"), self.ipr_tab.get_float("j_index"))
            elif "Darcy" in model:
                q_ipr, p_ipr = IPRModels.darcy(self.ipr_tab.get_float("k"), self.ipr_tab.get_float("h"), self.ipr_tab.get_float("mu"), self.ipr_tab.get_float("bo"), self.ipr_tab.get_float("re"), self.ipr_tab.get_float("rw"), self.ipr_tab.get_float("skin"), pres_res)
            elif model == "Economides y Retnanto":
                q_ipr, p_ipr = IPRModels.economides_retnanto(self.ipr_tab.get_float("qmax"), pres_res, self.ipr_tab.get_float("pb"))
            elif model == "Brown":
                q_ipr, p_ipr = IPRModels.brown(self.ipr_tab.get_float("qmax_o"), pres_res, self.ipr_tab.get_float("w_cut"))
            elif model == "Cheng":
                q_ipr, p_ipr = IPRModels.cheng(self.ipr_tab.get_float("qmax"), pres_res, self.ipr_tab.get_float("angle"))
            elif model == "Joshi Horizontal":
                q_ipr, p_ipr = IPRModels.joshi(self.ipr_tab.get_float("kh"), self.ipr_tab.get_float("kv"), self.ipr_tab.get_float("h"), self.ipr_tab.get_float("mu"), self.ipr_tab.get_float("bo"), self.ipr_tab.get_float("L"), self.ipr_tab.get_float("reh"), self.ipr_tab.get_float("rw"), self.ipr_tab.get_float("skin"), pres_res)
            elif model == "Babu y Odeh":
                q_ipr, p_ipr = IPRModels.babu_odeh(self.ipr_tab.get_float("kx"), self.ipr_tab.get_float("ky"), self.ipr_tab.get_float("kz"), self.ipr_tab.get_float("h"), self.ipr_tab.get_float("a_res"), self.ipr_tab.get_float("b_res"), self.ipr_tab.get_float("mu"), self.ipr_tab.get_float("bo"), self.ipr_tab.get_float("L"), self.ipr_tab.get_float("rw"), self.ipr_tab.get_float("x_mid"), self.ipr_tab.get_float("y_0"), self.ipr_tab.get_float("z_0"), self.ipr_tab.get_float("s_res"), pres_res)
            elif model == "Vogel Modificado (Kabir)":
                q_ipr, p_ipr = IPRModels.vogel_kabir(self.ipr_tab.get_float("kh"), self.ipr_tab.get_float("kv"), self.ipr_tab.get_float("h"), self.ipr_tab.get_float("mu"), self.ipr_tab.get_float("bo"), self.ipr_tab.get_float("L"), self.ipr_tab.get_float("reh"), self.ipr_tab.get_float("rw"), self.ipr_tab.get_float("skin"), pres_res, self.ipr_tab.get_float("pb"))
            elif model == "Bendakhlia y Aziz":
                q_max = self.ipr_tab.get_float("qmax")
                q_ipr, p_ipr = IPRModels.bendakhlia_aziz(q_max, pres_res, self.ipr_tab.get_float("rec_factor"))
                q_max_ipr = q_max

            if 'q_max_ipr' not in locals():
                q_max_ipr = max(q_ipr) if len(q_ipr) > 0 else 1000
            
            # Calcular VLP (Barrido de caudales)
            # Generamos menos puntos para que sea rápido, pero suficiente para la curva
            q_vlp = np.linspace(100, max(100, q_max_ipr), 15)
            p_vlp = []
            last_details = {}
            
            # Inputs VLP
            depth = self.get_val("Profundidad")
            tid = self.get_val("Tubing")
            pwh = self.get_val("P Cabeza")
            twh = self.get_val("Temp. Cabeza")
            tbh = self.get_val("Temp. Fondo")
            gor = self.get_val("GOR")
            bsw = self.get_val("Corte")
            api = self.get_val("API")
            gsg = self.get_val("Gravedad Gas")
            wsg = self.get_val("Gravedad Agua")
            bw  = self.get_val("Bw")

            for q in q_vlp:
                pwf_calc, details = VLPModels.calculate_pwf_31_steps(
                    depth, tid, pwh, twh, tbh, q, gor, bsw, api, gsg, wsg, bw
                )
                p_vlp.append(pwf_calc)
                last_details = details # Guardamos el último para mostrar en tabla
            
            # Graficar
            self.graph.plot_curve(q_ipr, p_ipr, f"IPR ({model})", "#E67E22", clear=True)
            self.graph.plot_curve(q_vlp, p_vlp, "VLP (Calculada)", "#3498DB", clear=False)
            
            # Encontrar intersección (Punto de Operación)
            try:
                # q_ipr está en orden descendente (de q_max a 0), numpy.interp requiere orden ascendente
                q_ipr_asc = q_ipr[::-1]
                p_ipr_asc = p_ipr[::-1]
                
                # Rango de evaluación
                min_q = max(np.min(q_ipr), np.min(q_vlp))
                max_q = min(np.max(q_ipr), np.max(q_vlp))
                
                if max_q > min_q:
                    q_eval = np.linspace(min_q, max_q, 1000)
                    p_ipr_eval = np.interp(q_eval, q_ipr_asc, p_ipr_asc)
                    p_vlp_eval = np.interp(q_eval, q_vlp, p_vlp)
                    
                    diff = p_ipr_eval - p_vlp_eval
                    zero_crossings = np.where(np.diff(np.sign(diff)))[0]
                    
                    if len(zero_crossings) > 0:
                        idx = zero_crossings[0]
                        # Refinar con interpolación lineal entre los dos puntos del cruce
                        q1, q2 = q_eval[idx], q_eval[idx+1]
                        d1, d2 = diff[idx], diff[idx+1]
                        # Si d1 y d2 tienen signos opuestos, interpolamos linealmente para Q exacto donde diff = 0
                        q_opt = q1 - d1 * (q2 - q1) / (d2 - d1) if d2 != d1 else q1
                        p_opt = np.interp(q_opt, q_ipr_asc, p_ipr_asc)
                        
                        self.graph.plot_point(
                            q_opt, p_opt, 
                            label=f"Caudal Óptimo (Q={q_opt:.1f} STB/d, Pwf={p_opt:.1f} psi)", 
                            color="#FF0000", 
                            tooltip_text=f"Nivel Óptimo\nQ: {q_opt:.1f} STB/d\nPwf: {p_opt:.1f} psi"
                        )
                    else:
                        print("No hay cruce en el rango.")
            except Exception as cross_err:
                print(f"No se pudo encontrar intersección: {cross_err}")
            
            # Llenar tabla con los 31 pasos del último punto calculado
            if last_details:
                for key, value in last_details.items():
                    self.tree.insert("", "end", values=(key, f"{value:.4f}"))
                
                # Mensaje de éxito sobre la iteración
                h_calc = last_details.get("Paso 30 (Delta H)", 0)
                messagebox.showinfo("Cálculo Exitoso", 
                                    f"Iteración completada.\nDelta H calculado: {h_calc:.1f} ft\n"
                                    f"Profundidad real: {depth} ft\n"
                                    "Condición H ≈ L cumplida.")

        except Exception as e:
            messagebox.showerror("Error Cálculo", f"Fallo: {str(e)}")
            print(e)