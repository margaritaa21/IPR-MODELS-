from tkinter import ttk

class VioletTheme:
    """
    Configuración centralizada de estilos (Soporta Tema Claro y Oscuro Claro).
    """
    _mode = "dark"

    @classmethod
    def get_colors(cls):
        if cls._mode == "dark":
            return {
                "BG_COLOR": "#2B2B2B",
                "FRAME_BG": "#3C3F41",
                "HEADER_COLOR": "#1E1E1E",
                "BTN_COLOR": "#6C4B91",
                "BTN_HOVER": "#8A56AC",
                "TEXT_COLOR": "#F5F5F5",
                "ENTRY_BG": "#4E5254"
            }
        else:
            return {
                "BG_COLOR": "#E8D8F1",
                "FRAME_BG": "#F4EAF9",
                "HEADER_COLOR": "#5D3A7A",
                "BTN_COLOR": "#8A56AC",
                "BTN_HOVER": "#A982D6",
                "TEXT_COLOR": "#2E2133",
                "ENTRY_BG": "#FFFFFF"
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
                        foreground="#A0A0A0" if cls._mode == "dark" else "#D0C0D0", 
                        padding=(15, 5),
                        font=(cls.FONT_FAMILY, 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", c["BTN_COLOR"])],
                  foreground=[("selected", "#FFFFFF")])
        
        # Botones
        style.configure("TButton", 
                        background=c["BTN_COLOR"], 
                        foreground="white", 
                        font=(cls.FONT_FAMILY, 10, "bold"),
                        borderwidth=0,
                        padding=5)
        style.map("TButton",
                  background=[("active", c["BTN_HOVER"])])
        
        # Frames y Labels
        style.configure("TFrame", background=c["BG_COLOR"])
        style.configure("Panel.TFrame", background=c["FRAME_BG"])
        style.configure("TLabel", background=c["BG_COLOR"], foreground=c["TEXT_COLOR"])
        style.configure("Panel.TLabel", background=c["FRAME_BG"], foreground=c["TEXT_COLOR"])
        style.configure("TLabelframe", background=c["BG_COLOR"], foreground=c["TEXT_COLOR"])
        style.configure("TLabelframe.Label", background=c["BG_COLOR"], foreground=c["TEXT_COLOR"], font=(cls.FONT_FAMILY, 10, "bold"))
        
        # Entry
        style.configure("TEntry", fieldbackground=c["ENTRY_BG"], foreground=c["TEXT_COLOR"], borderwidth=0)
        
        # Treeview y Scrollbar
        style.configure("Treeview", 
                        background=c["ENTRY_BG"], 
                        foreground=c["TEXT_COLOR"], 
                        fieldbackground=c["ENTRY_BG"], 
                        borderwidth=0)
        style.map("Treeview", 
                  background=[("selected", c["BTN_COLOR"])], 
                  foreground=[("selected", "#FFFFFF")])
        
        style.configure("Treeview.Heading", 
                        background=c["HEADER_COLOR"], 
                        foreground="white", 
                        font=(cls.FONT_FAMILY, 9, "bold"))
        
        style.configure("Vertical.TScrollbar", 
                        background=c["FRAME_BG"], 
                        troughcolor=c["BG_COLOR"], 
                        arrowcolor=c["TEXT_COLOR"])
        
        root.configure(bg=c["BG_COLOR"])