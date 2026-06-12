import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from ui.styles import VioletTheme

class GraphWidget(ttk.Frame):
    """
    Widget reutilizable para gráficas Matplotlib en Tkinter, con soporte de Zoom interactivo.
    """
    def __init__(self, parent, title="Gráfica"):
        super().__init__(parent)
        self.figure, self.ax = plt.subplots(figsize=(6, 5), dpi=100)
        
        c = VioletTheme.get_colors()
        self.is_dark = VioletTheme._mode == "dark"
        
        # Tema Dinámico para la Gráfica
        self.figure.patch.set_facecolor(c["BG_COLOR"])
        self.ax.set_facecolor(c["FRAME_BG"])
        self.ax.tick_params(colors=c["TEXT_COLOR"])
        for spine in self.ax.spines.values():
            spine.set_color(c["TEXT_COLOR"])
        
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        
        # Añadir barra de herramientas (Zoom, Pan)
        self.toolbar_frame = ttk.Frame(self)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()
        
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.set_labels("Caudal Q [STB/d]", "Pwf [psi]", title)
        
        # Almacenar puntos importantes (intersecciones) para el hover
        self.points_data = []
        
        # Anotación para el tooltip (Botón Lindo)
        c = VioletTheme.get_colors()
        self.annot = self.ax.annotate(
            "", xy=(0,0), xytext=(15, 15), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.6", fc=c["BTN_COLOR"], ec=c["TEXT_COLOR"], lw=1.5, alpha=0.95),
            arrowprops=dict(arrowstyle="wedge,tail_width=0.7", fc=c["BTN_COLOR"], ec=c["TEXT_COLOR"], patchA=None, patchB=None, relpos=(0.2, 0.2)),
            color="#FFFFFF", weight="bold", fontsize=9, fontname="Segoe UI"
        )
        self.annot.set_visible(False)
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)

    def set_labels(self, xlabel, ylabel, title):
        c = VioletTheme.get_colors()
        self.ax.set_xlabel(xlabel, fontsize=9, fontname="Segoe UI", color=c["TEXT_COLOR"])
        self.ax.set_ylabel(ylabel, fontsize=9, fontname="Segoe UI", color=c["TEXT_COLOR"])
        self.ax.set_title(title, fontsize=11, fontname="Segoe UI", weight='bold', color=c["TEXT_COLOR"])
        self.ax.grid(True, linestyle='--', alpha=0.3, color=c["TEXT_COLOR"])

    def plot_curve(self, x, y, label, color, clear=False, xlabel="Caudal Q [STB/d]", ylabel="Pwf [psi]", title="Análisis Nodal"):
        c = VioletTheme.get_colors()
        if clear:
            self.ax.clear()
            self.points_data = []
            self.set_labels(xlabel, ylabel, title)
            self.annot = self.ax.annotate(
                "", xy=(0,0), xytext=(15, 15), textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.6", fc=c["BTN_COLOR"], ec=c["TEXT_COLOR"], lw=1.5, alpha=0.95),
                arrowprops=dict(arrowstyle="wedge,tail_width=0.7", fc=c["BTN_COLOR"], ec=c["TEXT_COLOR"], patchA=None, patchB=None, relpos=(0.2, 0.2)),
                color="#FFFFFF", weight="bold", fontsize=9, fontname="Segoe UI"
            )
            self.annot.set_visible(False)
            
        self.ax.plot(x, y, label=label, color=color, linewidth=2, picker=True, pickradius=5)
        self.ax.legend(facecolor=c["BG_COLOR"], edgecolor=c["TEXT_COLOR"], labelcolor=c["TEXT_COLOR"])
        self.canvas.draw()
        
    def plot_point(self, x, y, label, color="#E74C3C", tooltip_text=None):
        """Grafica un punto específico y lo registra para el hover."""
        self.ax.plot(x, y, marker='o', markersize=8, color=color, label=label, zorder=5)
        self.points_data.append({'x': x, 'y': y, 'text': tooltip_text or f"({x:.1f}, {y:.1f})"})
        self.ax.legend(facecolor='#2B2B2B', edgecolor='#F5F5F5', labelcolor='#F5F5F5')
        self.canvas.draw()

    def on_hover(self, event):
        vis = self.annot.get_visible()
        if event.inaxes == self.ax:
            x, y = event.xdata, event.ydata
            if x is not None and y is not None:
                point_found = False
                
                # 1. Comprobar si está cerca de un punto importante (Intersección)
                for p in self.points_data:
                    if abs(x - p['x']) < (self.ax.get_xlim()[1] - self.ax.get_xlim()[0]) * 0.05 and \
                       abs(y - p['y']) < (self.ax.get_ylim()[1] - self.ax.get_ylim()[0]) * 0.05:
                        self.annot.xy = (p['x'], p['y'])
                        self.annot.set_text(p['text'])
                        self.annot.get_bbox_patch().set_facecolor("#E74C3C") # Rojo para punto óptimo
                        point_found = True
                        break
                
                # 2. Si no es un punto óptimo, anclar a la curva más cercana (Snapping)
                if not point_found:
                    min_dist = float('inf')
                    closest_x, closest_y = None, None
                    
                    for line in self.ax.get_lines():
                        xdata = line.get_xdata()
                        ydata = line.get_ydata()
                        # Ignorar puntos individuales (marcadores solos) comparando longitud
                        if len(xdata) > 1:
                            # Calcular distancia en pixeles aproximada para no distorsionar por escala
                            dist = np.sqrt(((xdata - x)/(self.ax.get_xlim()[1] - self.ax.get_xlim()[0]))**2 + 
                                           ((ydata - y)/(self.ax.get_ylim()[1] - self.ax.get_ylim()[0]))**2)
                            idx = np.argmin(dist)
                            if dist[idx] < 0.05: # Umbral de 5% de la gráfica
                                if dist[idx] < min_dist:
                                    min_dist = dist[idx]
                                    closest_x = xdata[idx]
                                    closest_y = ydata[idx]
                    
                    if closest_x is not None:
                        self.annot.xy = (closest_x, closest_y)
                        unit = "Mscf/d" if "Mscf" in self.ax.get_xlabel() else "STB/d"
                        self.annot.set_text(f"  Q: {closest_x:.1f} {unit}  \n  Pwf: {closest_y:.1f} psi  ")
                        self.annot.get_bbox_patch().set_facecolor("#6C4B91") # Morado para líneas
                        point_found = True
                
                if point_found:
                    self.annot.set_visible(True)
                    self.canvas.draw_idle()
                else:
                    if vis:
                        self.annot.set_visible(False)
                        self.canvas.draw_idle()
        else:
            if vis:
                self.annot.set_visible(False)
                self.canvas.draw_idle()