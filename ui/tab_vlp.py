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
        from ui.i18n import I18N
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
        self.geom_frame = ttk.LabelFrame(self.scroll_frame, text=I18N.get("geom"), padding=10)
        self.geom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.geom_fields = [
            (I18N.get("depth"), "depth", "8000"),
            (I18N.get("tubing"), "tubing", "2.441"),
            (I18N.get("temp_wh"), "temp_wh", "100"),
            (I18N.get("temp_bh"), "temp_bh", "200")
        ]
        for i, (lbl, key, default) in enumerate(self.geom_fields):
            ttk.Label(self.geom_frame, text=lbl).grid(row=i, column=0, sticky="w")
            entry = ttk.Entry(self.geom_frame, width=10)
            entry.insert(0, default)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.entries[key] = entry

        self.prod_frame = ttk.LabelFrame(self.scroll_frame, text=I18N.get("prod_data"), padding=10)
        self.prod_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Nota informativa
        info_frame = ttk.LabelFrame(self.scroll_frame, text=I18N.get("ipr_data"), padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(info_frame, text=I18N.get("note_ipr")).pack()

        # Botón Calcular Nodal
        self.calc_btn = ttk.Button(self.scroll_frame, text=I18N.get("calc_nodal"), command=self.calculate_nodal)
        self.calc_btn.pack(pady=15, fill=tk.X, padx=10)

        # --- PANEL DERECHO (PanedWindow) ---
        right_panel = ttk.PanedWindow(self, orient=tk.VERTICAL)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Panel Superior: Gráfica
        graph_frame = tk.Frame(right_panel, bg=c["BG_COLOR"])
        self.graph = GraphWidget(graph_frame, title=I18N.get("nodal_analysis"))
        self.graph.pack(fill=tk.BOTH, expand=True)
        right_panel.add(graph_frame, weight=3) # Dale más peso inicial a la gráfica
        
        # Panel Inferior: Tabla de Variables
        self.table_frame = ttk.LabelFrame(right_panel, text=I18N.get("calc_vars"), padding=5)
        
        self.tree = ttk.Treeview(self.table_frame, columns=("Variable", "Valor"), show="headings", height=8)
        self.tree.heading("Variable", text="Paso / Variable")
        self.tree.heading("Valor", text="Valor Calculado")
        self.tree.column("Variable", width=200)
        self.tree.column("Valor", width=150)
        
        vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        right_panel.add(self.table_frame, weight=1)
        
        # Inicializar inputs de producción
        self.update_fields_for_fluid_type()

    def update_fields_for_fluid_type(self):
        from ui.i18n import I18N
        
        # 1. Determinar si es Gas
        is_gas = False
        if self.ipr_tab:
            model = self.ipr_tab.modelo_cb.get()
            if model == "Fetkovich-gas":
                is_gas = True
                
        # 2. Guardar valores actuales de campos comunes si existen, para no perderlos
        saved_vals = {}
        for k in ["p_tf", "whp", "sg_gas"]:
            if k in self.entries:
                saved_vals[k] = self.entries[k].get()
        # Fallback si whp existe en saved_vals pero no p_tf
        if "whp" in saved_vals and "p_tf" not in saved_vals:
            saved_vals["p_tf"] = saved_vals["whp"]
                
        # 3. Limpiar frame de producción y las claves correspondientes en self.entries
        for widget in self.prod_frame.winfo_children():
            widget.destroy()
            
        # Limpiar de self.entries las entradas que pertenecen a la sección de producción
        prod_keys = ["p_tf", "whp", "api", "sg_gas", "sg_wat", "bw", "gor", "wcut", "visc_gas", "roughness"]
        for pk in prod_keys:
            if pk in self.entries:
                del self.entries[pk]
                
        # 4. Re-poblar según fluido
        if is_gas:
            self.prod_frame.config(text=I18N.get("prod_data_gas"))
            fields = [
                (I18N.get("p_tf"), "p_tf", saved_vals.get("p_tf", "1000")),
                (I18N.get("sg_gas"), "sg_gas", saved_vals.get("sg_gas", "0.75")),
                (I18N.get("visc_gas"), "visc_gas", "0.012"),
                (I18N.get("roughness"), "roughness", "0.0006")
            ]
        else:
            self.prod_frame.config(text=I18N.get("prod_data"))
            fields = [
                (I18N.get("whp"), "whp", saved_vals.get("whp", "150")),
                (I18N.get("api"), "api", "30"),
                (I18N.get("sg_gas"), "sg_gas", saved_vals.get("sg_gas", "0.75")),
                (I18N.get("sg_wat"), "sg_wat", "1.02"),
                (I18N.get("bw"), "bw", "1.0"),
                (I18N.get("gor"), "gor", "800"),
                (I18N.get("wcut"), "wcut", "10")
            ]
            
        for i, (lbl, key, default) in enumerate(fields):
            ttk.Label(self.prod_frame, text=lbl).grid(row=i, column=0, sticky="w")
            entry = ttk.Entry(self.prod_frame, width=10)
            entry.insert(0, default)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.entries[key] = entry
            
        # Actualizar botón de cálculo si existe
        if hasattr(self, "calc_btn"):
            if is_gas:
                self.calc_btn.config(text=I18N.get("calc_nodal") + " (Gas)")
            else:
                self.calc_btn.config(text=I18N.get("calc_nodal") + " (31 Pasos)")

    def on_well_type_changed(self):
        self.update_fields_for_fluid_type()

    def get_val(self, key_fragment):
        # Mapeo por si las moscas para mantener compatibilidad
        mapping = {
            "Profundidad": "depth",
            "Tubing": "tubing",
            "Temp. Cabeza": "temp_wh",
            "Temp. Fondo": "temp_bh",
            "P Cabeza": "p_tf",
            "Ptf": "p_tf",
            "whp": "p_tf",
            "thp": "temp_wh",
            "bhp": "temp_bh",
            "temp_wh": "temp_wh",
            "temp_bh": "temp_bh",
            "p_tf": "p_tf",
            "API": "api",
            "Gravedad Gas": "sg_gas",
            "Gravedad Agua": "sg_wat",
            "Bw": "bw",
            "GOR": "gor",
            "Corte": "wcut",
            "Viscosidad Gas": "visc_gas",
            "Rugosidad": "roughness"
        }
        
        mapped_key = mapping.get(key_fragment, key_fragment)
        if mapped_key in self.entries:
            try:
                return float(self.entries[mapped_key].get())
            except ValueError:
                return 0.0
                
        # Por compatibilidad
        for k, v in self.entries.items():
            if key_fragment in k or mapped_key in k:
                try:
                    return float(v.get())
                except ValueError:
                    return 0.0
        return 0.0

    def calculate_nodal(self):
        if not self.ipr_tab:
            messagebox.showerror("Error", "Referencia a pestaña IPR no encontrada.")
            return

        from ui.i18n import I18N
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

            is_gas = (model == "Fetkovich-gas")

            if model == "Vogel (Subsaturado)":
                q_ipr, p_ipr = IPRModels.vogel_subsaturado(pres_res, self.ipr_tab.get_float("pb"), self.ipr_tab.get_float("j_index"))
            elif model == "Fetkovich-gas":
                q_ipr, p_ipr = IPRModels.fetkovich(self.ipr_tab.get_float("c_fet"), self.ipr_tab.get_float("n_fet"), pres_res)
            elif model == "Wiggins":
                q_ipr, p_ipr = IPRModels.wiggins(pres_res, self.ipr_tab.get_float("pb"), self.ipr_tab.get_float("j_index"))
            elif "Darcy" in model:
                q_ipr, p_ipr = IPRModels.darcy(self.ipr_tab.get_float("k"), self.ipr_tab.get_float("h"), self.ipr_tab.get_float("mu"), self.ipr_tab.get_float("bo"), self.ipr_tab.get_float("re"), self.ipr_tab.get_float("rw"), self.ipr_tab.get_float("skin"), pres_res)
            elif model == "Economides y Retnanto":
                q_ipr, p_ipr = IPRModels.economides_retnanto(
                    self.ipr_tab.get_float("kh"), self.ipr_tab.get_float("kv"), self.ipr_tab.get_float("h"),
                    self.ipr_tab.get_float("mu"), self.ipr_tab.get_float("bo"), self.ipr_tab.get_float("L"),
                    self.ipr_tab.get_float("reh"), self.ipr_tab.get_float("rw"), self.ipr_tab.get_float("skin"),
                    pres_res, self.ipr_tab.get_float("pb")
                )
            elif model == "Brown":
                q_ipr, p_ipr = IPRModels.brown(
                    pres_res, self.ipr_tab.get_float("pb"),
                    self.ipr_tab.get_float("j_index"), self.ipr_tab.get_float("w_cut")
                )
            elif model == "Cheng":
                q_ipr, p_ipr = IPRModels.cheng(
                    self.ipr_tab.get_float("kh"), self.ipr_tab.get_float("kv"), self.ipr_tab.get_float("h"),
                    self.ipr_tab.get_float("mu"), self.ipr_tab.get_float("bo"), self.ipr_tab.get_float("L"),
                    self.ipr_tab.get_float("reh"), self.ipr_tab.get_float("rw"), self.ipr_tab.get_float("skin"),
                    pres_res, self.ipr_tab.get_float("pb"), self.ipr_tab.get_float("angle")
                )
            elif model == "Joshi Horizontal":
                q_ipr, p_ipr = IPRModels.joshi(self.ipr_tab.get_float("kh"), self.ipr_tab.get_float("kv"), self.ipr_tab.get_float("h"), self.ipr_tab.get_float("mu"), self.ipr_tab.get_float("bo"), self.ipr_tab.get_float("L"), self.ipr_tab.get_float("reh"), self.ipr_tab.get_float("rw"), self.ipr_tab.get_float("skin"), pres_res)
            elif model == "Babu y Odeh":
                q_ipr, p_ipr = IPRModels.babu_odeh(self.ipr_tab.get_float("kx"), self.ipr_tab.get_float("ky"), self.ipr_tab.get_float("kz"), self.ipr_tab.get_float("h"), self.ipr_tab.get_float("a_res"), self.ipr_tab.get_float("b_res"), self.ipr_tab.get_float("mu"), self.ipr_tab.get_float("bo"), self.ipr_tab.get_float("L"), self.ipr_tab.get_float("rw"), self.ipr_tab.get_float("x_mid"), self.ipr_tab.get_float("y_0"), self.ipr_tab.get_float("z_0"), self.ipr_tab.get_float("s_res"), pres_res)
            elif model == "Vogel Modificado (Kabir)":
                q_ipr, p_ipr = IPRModels.vogel_kabir(self.ipr_tab.get_float("kh"), self.ipr_tab.get_float("kv"), self.ipr_tab.get_float("h"), self.ipr_tab.get_float("mu"), self.ipr_tab.get_float("bo"), self.ipr_tab.get_float("L"), self.ipr_tab.get_float("reh"), self.ipr_tab.get_float("rw"), self.ipr_tab.get_float("skin"), pres_res, self.ipr_tab.get_float("pb"))
            elif model == "Bendakhlia y Aziz":
                q_ipr, p_ipr = IPRModels.bendakhlia_aziz(
                    self.ipr_tab.get_float("kh"), self.ipr_tab.get_float("kv"), self.ipr_tab.get_float("h"),
                    self.ipr_tab.get_float("mu"), self.ipr_tab.get_float("bo"), self.ipr_tab.get_float("L"),
                    self.ipr_tab.get_float("reh"), self.ipr_tab.get_float("rw"), self.ipr_tab.get_float("skin"),
                    pres_res, self.ipr_tab.get_float("pb"), self.ipr_tab.get_float("rec_factor")
                )

            if 'q_max_ipr' not in locals():
                q_max_ipr = max(q_ipr) if len(q_ipr) > 0 else 1000.0
            
            # Generar barrido de caudales
            q_vlp = np.linspace(100.0, max(100.0, q_max_ipr), 15)
            p_vlp = []
            last_details = {}
            
            # Inputs VLP comunes
            depth = self.get_val("Profundidad")
            tid = self.get_val("Tubing")
            twh = self.get_val("Temp. Cabeza")
            tbh = self.get_val("Temp. Fondo")
            gsg = self.get_val("Gravedad Gas")

            if is_gas:
                # Inputs de Gas
                ptf = self.get_val("Ptf")
                mug = self.get_val("Viscosidad Gas")
                roughness = self.get_val("Rugosidad")
                
                for q in q_vlp:
                    # El solucionador de VLP de gas espera caudales en MMscfd, y el IPR Fetkovich da MMscf/d.
                    q_mmscfd = q
                    pwf_calc, details = VLPModels.calculate_gas_pwf(
                        depth, tid, ptf, twh, tbh, q_mmscfd, gsg, mug, roughness
                    )
                    p_vlp.append(pwf_calc)
                    last_details = details
                
                # Graficar con etiquetas de Gas
                self.graph.plot_curve(
                    q_ipr, p_ipr, f"IPR ({model})", "#E67E22", clear=True, 
                    xlabel=I18N.get("q_label_gas"), ylabel="Pwf [psi]", title="Análisis Nodal (Gas)"
                )
                self.graph.plot_curve(q_vlp, p_vlp, "VLP (Calculada)", "#3498DB", clear=False)
            else:
                # Inputs de Petróleo
                pwh = self.get_val("P Cabeza")
                gor = self.get_val("GOR")
                bsw = self.get_val("Corte")
                api = self.get_val("API")
                wsg = self.get_val("Gravedad Agua")
                bw  = self.get_val("Bw")

                for q in q_vlp:
                    pwf_calc, details = VLPModels.calculate_pwf_31_steps(
                        depth, tid, pwh, twh, tbh, q, gor, bsw, api, gsg, wsg, bw
                    )
                    p_vlp.append(pwf_calc)
                    last_details = details
                
                # Graficar con etiquetas de Petróleo
                self.graph.plot_curve(
                    q_ipr, p_ipr, f"IPR ({model})", "#E67E22", clear=True, 
                    xlabel=I18N.get("q_label"), ylabel="Pwf [psi]", title="Análisis Nodal"
                )
                self.graph.plot_curve(q_vlp, p_vlp, "VLP (Calculada)", "#3498DB", clear=False)
            
            # Encontrar intersección (Punto de Operación)
            try:
                q_ipr_asc = q_ipr[::-1]
                p_ipr_asc = p_ipr[::-1]
                
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
                        q1, q2 = q_eval[idx], q_eval[idx+1]
                        d1, d2 = diff[idx], diff[idx+1]
                        q_opt = q1 - d1 * (q2 - q1) / (d2 - d1) if d2 != d1 else q1
                        p_opt = np.interp(q_opt, q_ipr_asc, p_ipr_asc)
                        
                        unit = "Mscf/d" if is_gas else "STB/d"
                        self.graph.plot_point(
                            q_opt, p_opt, 
                            label=f"Caudal Óptimo (Q={q_opt:.1f} {unit}, Pwf={p_opt:.1f} psi)", 
                            color="#FF0000", 
                            tooltip_text=f"Nivel Óptimo\nQ: {q_opt:.1f} {unit}\nPwf: {p_opt:.1f} psi"
                        )
                    else:
                        print("No hay cruce en el rango.")
            except Exception as cross_err:
                print(f"No se pudo encontrar intersección: {cross_err}")
            
            # Llenar tabla con los pasos del último punto calculado
            if last_details:
                for key, value in last_details.items():
                    self.tree.insert("", "end", values=(key, f"{value:.4f}"))
                
                if is_gas:
                    z_factor = last_details.get("Paso 8 (Z_factor)", 0.9)
                    messagebox.showinfo("Cálculo Exitoso", 
                                        f"Iteración completada.\nFactor Z final: {z_factor:.4f}\n"
                                        f"Pwf calculada: {p_vlp[-1]:.1f} psi.")
                else:
                    h_calc = last_details.get("Paso 30 (Delta H)", 0)
                    messagebox.showinfo("Cálculo Exitoso", 
                                        f"Iteración completada.\nDelta H calculado: {h_calc:.1f} ft\n"
                                        f"Profundidad real: {depth} ft\n"
                                        "Condición H ≈ L cumplida.")

        except Exception as e:
            messagebox.showerror("Error Cálculo", f"Fallo: {str(e)}")
            print(e)