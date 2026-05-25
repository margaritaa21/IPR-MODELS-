import tkinter as tk
from tkinter import ttk
from ui.styles import VioletTheme
from ui.tab_ipr import IPRTab
from ui.tab_vlp import VLPTab
from ui.i18n import I18N

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(I18N.get("title"))
        self.geometry("1000x700")
        
        c = VioletTheme.get_colors()
        self.configure(bg=c["BG_COLOR"])
        
        VioletTheme.apply_styles(self)
        self.build_ui()

    def build_ui(self):
        c = VioletTheme.get_colors()
        
        # Header
        header = tk.Frame(self, bg=c["HEADER_COLOR"], height=60)
        header.pack(fill=tk.X)
        
        title_frame = tk.Frame(header, bg=c["HEADER_COLOR"])
        title_frame.pack(side=tk.LEFT, padx=20, pady=15)
        
        tk.Label(
            title_frame, 
            text="🛢️ " + I18N.get("title"),
            bg=c["HEADER_COLOR"],
            fg="white",
            font=(VioletTheme.FONT_FAMILY, 16, "bold")
        ).pack(side=tk.LEFT)

        # Global Well Type Selection
        self.well_type_var = tk.StringVar(value=I18N.get("vertical"))
        
        c = VioletTheme.get_colors()
        type_frame = tk.Frame(header, bg=c["HEADER_COLOR"])
        type_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Botón de Cambio de Idioma
        self.lang_btn = ttk.Button(type_frame, text="ES / EN", command=self.toggle_lang, width=8)
        self.lang_btn.pack(side=tk.RIGHT, padx=5)
        
        # Botón de Tema (Sol/Luna)
        theme_icon = "🌙" if VioletTheme._mode == "light" else "☀️"
        self.theme_btn = ttk.Button(type_frame, text=theme_icon, command=self.toggle_theme, width=4)
        self.theme_btn.pack(side=tk.RIGHT, padx=5)
        
        tk.Label(
            type_frame,
            text=I18N.get("well_type"),
            bg=c["HEADER_COLOR"],
            fg="white",
            font=(VioletTheme.FONT_FAMILY, 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        self.well_type_cb = ttk.Combobox(
            type_frame,
            textvariable=self.well_type_var,
            values=[I18N.get("vertical"), I18N.get("horizontal")],
            state="readonly",
            width=15
        )
        self.well_type_cb.pack(side=tk.LEFT)
        self.well_type_cb.bind("<<ComboboxSelected>>", self.on_well_type_changed)

        # Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Pestañas
        self.tab_ipr = IPRTab(self.notebook, well_type_var=self.well_type_var)
        self.tab_vlp = VLPTab(self.notebook, well_type_var=self.well_type_var, ipr_tab=self.tab_ipr)
        
        self.notebook.add(self.tab_ipr, text=I18N.get("tab_ipr"))
        self.notebook.add(self.tab_vlp, text=I18N.get("tab_vlp"))

    def toggle_lang(self):
        new_lang = "en" if I18N._lang == "es" else "es"
        I18N.set_lang(new_lang)
        self.rebuild_ui()

    def toggle_theme(self):
        VioletTheme.toggle_mode()
        self.rebuild_ui()
        
    def rebuild_ui(self):
        # Guardar estado actual
        current_type = self.well_type_var.get()
        # Reconstruir UI para aplicar idioma o tema (destruyendo lo anterior)
        for widget in self.winfo_children():
            widget.destroy()
        VioletTheme.apply_styles(self)
        self.build_ui()
        self.well_type_var.set(current_type)
        self.on_well_type_changed()

    def on_well_type_changed(self, event=None):
        # Notificar a las pestañas
        if hasattr(self.tab_ipr, 'on_well_type_changed'):
            self.tab_ipr.on_well_type_changed()
        if hasattr(self.tab_vlp, 'on_well_type_changed'):
            self.tab_vlp.on_well_type_changed()