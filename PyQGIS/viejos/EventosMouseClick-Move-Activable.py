from qgis.gui import QgsMapTool, QgsMapMouseEvent
from PyQt5.QtCore import Qt

#from CrearBarraHerrCursorEstados import estado_flujo_trabajo

class CustomMapTool(QgsMapTool):
    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.active = False  # Variable para rastrear el estado de la herramienta

    def canvasPressEvent(self, event):
        # Manejar el evento de clic del mouse
        if self.active and event.button() == Qt.LeftButton:
            print("Clic en el mapa en la posición:", event.mapPoint())

            if estado_flujo_trabajo == "seleccion":
                self.deactivate()


    def canvasMoveEvent(self, event):
        # Manejar el evento de movimiento del mouse
        if self.active:
            print("Movimiento del mouse en la posición:", event.mapPoint())

    def activate(self):
        # Activar la herramienta y cambiar el ícono del puntero
        self.active = True
        self.canvas.setCursor(Qt.CrossCursor)
        QgsMapTool.activate(self)

    def deactivate(self):
        # Desactivar la herramienta y restaurar el ícono del puntero
        self.active = False
        self.canvas.unsetCursor()
        QgsMapTool.deactivate(self)

# Crear una instancia de la herramienta personalizada
custom_map_tool = CustomMapTool(iface.mapCanvas())

# Activar la herramienta desde otro script
custom_map_tool.activate()

# Desactivar la herramienta desde otro script
#custom_map_tool.deactivate()
