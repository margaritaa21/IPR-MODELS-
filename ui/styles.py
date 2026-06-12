from tkinter import ttk


# Paleta unificada de curvas IPR — pasteles morados extendidos.
# 12 colores; orden estable para que la asignación a cada modelo no varíe
# entre invocaciones (CA-3 de HU-006).
IPR_PALETTE = [
    "#8A56AC",  # primary (violeta clásico)
    "#B58FCB",  # secondary (lila apagado)
    "#5D3A7A",  # primary dark
    "#D98C9C",  # rosa coral pastel (danger soft)
    "#7DBE8A",  # verde pastel (success)
    "#E8C46B",  # amarillo pastel (warning)
    "#8FB7D9",  # azul pastel (info)
    "#A982D6",  # primary hover (violeta brillante)
    "#C9A8DA",  # secondary hover (lila claro)
    "#6E5A82",  # text muted
    "#9B6BBE",  # violeta saturado intermedio
    "#E0B0E0",  # rosa-lila claro
]

# Mapeo determinista modelo → color (uno por cada entrada del Combobox IPR).
IPR_MODEL_COLORS = {
    "Vogel (Subsaturado)":          IPR_PALETTE[0],
    "Fetkovich-gas":                IPR_PALETTE[1],
    "Wiggins":                      IPR_PALETTE[2],
    "Darcy (Semi-Estacionario)":    IPR_PALETTE[3],
    "Brown":                        IPR_PALETTE[4],
    "Joshi Horizontal":             IPR_PALETTE[5],
    "Babu y Odeh":                  IPR_PALETTE[6],
    "Vogel Modificado (Kabir)":     IPR_PALETTE[7],
    "Economides y Retnanto":        IPR_PALETTE[8],
    "Bendakhlia y Aziz":            IPR_PALETTE[9],
    "Cheng":                        IPR_PALETTE[10],
}


class VioletTheme:
    """
    Configuración centralizada de estilos (Soporta Tema Claro y Oscuro Claro).
    """
    _mode = "dark"

    # Paleta de curvas accesible vía la clase para uso desde la UI.
    IPR_PALETTE = IPR_PALETTE
    IPR_MODEL_COLORS = IPR_MODEL_COLORS

    @classmethod
    def get_colors(cls):
        if cls._mode == "dark":
            return {
                # ── Claves existentes (backward-compat) ────────────────
                "BG_COLOR":     "#120F1F",
                "FRAME_BG":     "#1C182F",
                "HEADER_COLOR": "#0B0914",
                "BTN_COLOR":    "#7E4EAC",
                "BTN_HOVER":    "#9F66D6",
                "TEXT_COLOR":   "#F0ECF8",
                "ENTRY_BG":     "#292440",
                # ── Tokens semánticos extendidos (HU-006) ──────────────
                # Superficies
                "SURFACE":          "#1C182F",
                "SURFACE_ALT":      "#25203C",
                "BORDER":           "#332C52",
                # Texto
                "TEXT_MUTED":       "#A795B8",
                "TEXT_ON_PRIMARY":  "#FFFFFF",
                # Acentos
                "PRIMARY":          "#8A56AC",
                "PRIMARY_HOVER":    "#A982D6",
                "PRIMARY_SOFT":     "#2D2342",
                "SECONDARY":        "#7E5E96",
                "SECONDARY_HOVER":  "#9772AE",
                # Estados
                "SUCCESS":          "#8FC79B",
                "WARNING":          "#E4C77A",
                "DANGER":           "#D99AA8",
                "INFO":             "#9CBFDD",
                # Inputs
                "ENTRY_BORDER":     "#332C52",
            }
        else:
            return {
                # ── Claves existentes (backward-compat) ────────────────
                "BG_COLOR":     "#F3EEF8",
                "FRAME_BG":     "#FFFFFF",
                "HEADER_COLOR": "#E7DCF2",
                "BTN_COLOR":    "#8A56AC",
                "BTN_HOVER":    "#A982D6",
                "TEXT_COLOR":   "#2B1C3C",
                "ENTRY_BG":     "#F7F4FA",
                # ── Tokens semánticos extendidos (HU-006) ──────────────
                # Superficies
                "SURFACE":          "#FFFFFF",
                "SURFACE_ALT":      "#F1EBF7",
                "BORDER":           "#E2D8ED",
                # Texto
                "TEXT_MUTED":       "#7D6890",
                "TEXT_ON_PRIMARY":  "#FFFFFF",
                # Acentos
                "PRIMARY":          "#8A56AC",
                "PRIMARY_HOVER":    "#A982D6",
                "PRIMARY_SOFT":     "#F4EBFB",
                "SECONDARY":        "#B58FCB",
                "SECONDARY_HOVER":  "#C9A8DA",
                # Estados
                "SUCCESS":          "#7DBE8A",
                "WARNING":          "#E8C46B",
                "DANGER":           "#D98C9C",
                "INFO":             "#8FB7D9",
                # Inputs
                "ENTRY_BORDER":     "#E2D8ED",
            }

    FONT_FAMILY = "Segoe UI"
    
    @classmethod
    def toggle_mode(cls):
        cls._mode = "light" if cls._mode == "dark" else "dark"
    
    @classmethod
    def apply_styles(cls, root):
        style = ttk.Style()
        style.theme_use("clam")
        
        c = cls.get_colors()
        
        # Configuración General
        style.configure(".", 
                        background=c["BG_COLOR"], 
                        foreground=c["TEXT_COLOR"], 
                        font=(cls.FONT_FAMILY, 10))
        
        # Notebook (Pestañas)
        style.configure("TNotebook", background=c["BG_COLOR"], borderwidth=0)
        style.configure("TNotebook.Tab", 
                        background=c["HEADER_COLOR"], 
                        foreground="#A0A0A0" if cls._mode == "dark" else "#7D6890", 
                        padding=(20, 8),
                        font=(cls.FONT_FAMILY, 10, "bold"),
                        borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", c["BTN_COLOR"])],
                  foreground=[("selected", "#FFFFFF")])
        
        # Botones
        style.configure("TButton", 
                        background=c["BTN_COLOR"], 
                        foreground="white", 
                        font=(cls.FONT_FAMILY, 10, "bold"),
                        borderwidth=0,
                        padding=(12, 6))
        style.map("TButton",
                  background=[("active", c["BTN_HOVER"])])
        
        # Frames y Labels
        style.configure("TFrame", background=c["BG_COLOR"])
        style.configure("Panel.TFrame", background=c["FRAME_BG"])
        style.configure("TLabel", background=c["BG_COLOR"], foreground=c["TEXT_COLOR"])
        style.configure("Panel.TLabel", background=c["FRAME_BG"], foreground=c["TEXT_COLOR"])
        style.configure("TLabelframe", background=c["BG_COLOR"], foreground=c["TEXT_COLOR"], bordercolor=c["BORDER"], borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background=c["BG_COLOR"], foreground=c["PRIMARY"], font=(cls.FONT_FAMILY, 10, "bold"))
        
        # Entry (Padding and border color in Clam theme)
        style.configure("TEntry", 
                        fieldbackground=c["ENTRY_BG"], 
                        foreground=c["TEXT_COLOR"], 
                        bordercolor=c["BORDER"], 
                        lightcolor=c["BORDER"], 
                        darkcolor=c["BORDER"], 
                        insertcolor=c["TEXT_COLOR"], 
                        padding=6,
                        borderwidth=1)
        
        # Combobox
        style.configure("TCombobox", 
                        fieldbackground=c["ENTRY_BG"], 
                        background=c["BG_COLOR"], 
                        foreground=c["TEXT_COLOR"], 
                        bordercolor=c["BORDER"], 
                        lightcolor=c["BORDER"], 
                        darkcolor=c["BORDER"], 
                        arrowcolor=c["TEXT_COLOR"], 
                        padding=6,
                        borderwidth=1)
        
        # Treeview y Scrollbar
        style.configure("Treeview", 
                        background=c["ENTRY_BG"], 
                        foreground=c["TEXT_COLOR"], 
                        fieldbackground=c["ENTRY_BG"], 
                        rowheight=26,
                        font=(cls.FONT_FAMILY, 9),
                        borderwidth=0)
        style.map("Treeview", 
                  background=[("selected", c["BTN_COLOR"])], 
                  foreground=[("selected", "#FFFFFF")])
        
        style.configure("Treeview.Heading", 
                        background=c["HEADER_COLOR"], 
                        foreground="white", 
                        font=(cls.FONT_FAMILY, 9, "bold"),
                        padding=6,
                        borderwidth=1,
                        bordercolor=c["BORDER"])
        
        style.configure("Vertical.TScrollbar", 
                        background=c["FRAME_BG"], 
                        troughcolor=c["BG_COLOR"], 
                        arrowcolor=c["TEXT_COLOR"],
                        borderwidth=0,
                        gripcount=0)
        
        root.configure(bg=c["BG_COLOR"])