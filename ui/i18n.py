class I18N:
    _lang = "es"

    _dict = {
        "es": {
            "title": "VIOLET - Análisis Nodal & PVT",
            "well_type": "Tipo de Pozo:",
            "vertical": "Vertical",
            "horizontal": "Horizontal",
            "tab_ipr": "  Curvas IPR  ",
            "tab_vlp": "  VLP & Nodal  ",
            "model_sel": "Selección de Modelo",
            "ipr_model": "Modelo IPR:",
            "inputs": "Parámetros de Entrada",
            "calc_ipr": "Calcular Curva IPR",
            "graph_ipr": "Curva IPR (Inflow)",
            "q_label": "Caudal Q [STB/d]",
            "p_label": "Pwf [psi]",
            "geom": "Geometría Pozo",
            "prod_data": "Datos Producción",
            "ipr_data": "Datos IPR",
            "calc_nodal": "Calcular Análisis Nodal",
            "nodal_analysis": "Análisis Nodal",
            "calc_vars": "Variables calculadas (Último Punto)",
            "optimal_point": "Nivel Óptimo / Punto de Operación",
            "pres_yac": "Presión Yac. (psi):",
            "q_max": "Q max (STB/d):",
            "rec_factor": "Factor Recobro (frac):",
            "view_nv_graph": "Ver Regresión n y V",
            "depth": "Profundidad (ft)",
            "tubing": "Tubing ID (in)",
            "thp": "Temp. Cabeza (°F)",
            "bhp": "Temp. Fondo (°F)",
            "whp": "P Cabeza (psi)",
            "api": "API Petróleo",
            "sg_gas": "Gravedad Gas",
            "sg_wat": "Gravedad Agua",
            "bw": "Bw (rb/stb)",
            "gor": "GOR (scf/stb)",
            "wcut": "Corte de Agua %",
            "note_ipr": "Nota: El modelo IPR y sus datos se\ntomarán automáticamente de la\npestaña 'Curvas IPR'."
        },
        "en": {
            "title": "VIOLET - Nodal Analysis & PVT",
            "well_type": "Well Type:",
            "vertical": "Vertical",
            "horizontal": "Horizontal",
            "tab_ipr": "  IPR Curves  ",
            "tab_vlp": "  VLP & Nodal  ",
            "model_sel": "Model Selection",
            "ipr_model": "IPR Model:",
            "inputs": "Input Parameters",
            "calc_ipr": "Calculate IPR Curve",
            "graph_ipr": "IPR Curve (Inflow)",
            "q_label": "Flow Rate Q [STB/d]",
            "p_label": "Pwf [psi]",
            "geom": "Well Geometry",
            "prod_data": "Production Data",
            "ipr_data": "IPR Data",
            "calc_nodal": "Calculate Nodal Analysis",
            "nodal_analysis": "Nodal Analysis",
            "calc_vars": "Calculated Variables (Last Point)",
            "optimal_point": "Optimal Level / Operating Point",
            "pres_yac": "Res. Pressure (psi):",
            "q_max": "Q max (STB/d):",
            "rec_factor": "Recovery Factor (frac):",
            "view_nv_graph": "View n & V Regression",
            "depth": "Depth (ft)",
            "tubing": "Tubing ID (in)",
            "thp": "Wellhead Temp (°F)",
            "bhp": "Bottomhole Temp (°F)",
            "whp": "Wellhead P (psi)",
            "api": "Oil API",
            "sg_gas": "Gas Gravity",
            "sg_wat": "Water Gravity",
            "bw": "Bw (rb/stb)",
            "gor": "GOR (scf/stb)",
            "wcut": "Water Cut %",
            "note_ipr": "Note: The IPR model and its data\nwill be automatically taken from\nthe 'IPR Curves' tab."
        }
    }

    @classmethod
    def set_lang(cls, lang):
        if lang in cls._dict:
            cls._lang = lang

    @classmethod
    def get(cls, key):
        return cls._dict[cls._lang].get(key, key)
