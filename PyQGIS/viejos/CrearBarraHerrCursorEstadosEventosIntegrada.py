from PyQt5.QtGui import QIcon, QCursor, QPixmap
from PyQt5.QtWidgets import QToolBar, QToolButton, QButtonGroup
from qgis.utils import iface
from qgis.PyQt.QtCore import QSize
import os
import sys

from qgis.gui import QgsMapTool, QgsMapMouseEvent
from PyQt5.QtCore import Qt

# Variable global para almacenar el estado del flujo de trabajo
estado_flujo_trabajo = None


class CustomToolbarPanel:
    def __init__(self, map_tool):
        self.toolbox = None
        self.tool_buttons = []
        self.button_group = None
        self.map_tool = map_tool  # Referencia a la herramienta de mapa

    def init_panel(self):
        # Obtener la ruta del directorio de trabajo actual
        script_dir = os.getcwd()
        iconos_dir = os.path.join(script_dir, "iconos")

        # Crear la caja de herramientas
        self.toolbox = QToolBar("MiCajaDeHerramientas")
        self.toolbox.setIconSize(QSize(50, 50))  # Ajustar el tamaño del ícono según sea necesario

        # Lista de nombres de botones
        button_names = ["Selección", "Nodo", "Línea", "Interruptor", "Carga", "Generador"]

        # Agregar botones de opción a la caja de herramientas
        self.button_group = QButtonGroup()

        def create_handler(button_name, cursor_icon_path):
            def handler():
                self.handle_button_click(button_name, cursor_icon_path)
            return handler

        for button_name in button_names:
            button_icon_path = os.path.join(iconos_dir, f"{button_name.lower()}.png")
            cursor_icon_path = os.path.join(iconos_dir, f"{button_name.lower()}.cur")
            
            tool_button = QToolButton()
            tool_button.setIcon(QIcon(button_icon_path))
            tool_button.setCheckable(True)
            self.toolbox.addWidget(tool_button)
            self.tool_buttons.append(tool_button)
            self.button_group.addButton(tool_button)
            tool_button.clicked.connect(create_handler(button_name, cursor_icon_path))

        self.button_group.setExclusive(True)

    def handle_button_click(self, button_name, cursor_icon_path):
        global estado_flujo_trabajo

        # Cambiar el cursor al hacer clic en el botón
        if button_name.lower() == "selección":
            estado_flujo_trabajo = "selección"
            iface.mapCanvas().unsetCursor()
            self.map_tool.deactivate()  # Desactivar la herramienta de mapa
        else:
            estado_flujo_trabajo = button_name.lower()
            cursor = QCursor(QPixmap(cursor_icon_path), 0, 0)
            iface.mapCanvas().setCursor(cursor)
            self.map_tool.activate()  # Desactivar la herramienta de mapa

        print(f"Botón {button_name} clicado - Estado del flujo de trabajo: {estado_flujo_trabajo}")


class CustomMapTool(QgsMapTool):
    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.active = False  # Agregar una variable para rastrear el estado de activación

    def canvasPressEvent(self, event):
        global estado_flujo_trabajo
        # Manejar el evento de clic del mouse
        if event.button() == Qt.LeftButton:
            print("Clic en el mapa en la posición:", event.mapPoint())
            print("Estado del flujo de trabajo:", estado_flujo_trabajo)
            if estado_flujo_trabajo == "selección":
                print("Desactivando eventos")
                self.deactivate()

    def canvasMoveEvent(self, event):
        # Manejar el evento de movimiento del mouse
        if self.active:
            print("Movimiento del mouse en la posición:", event.mapPoint())

    def activate(self):
        # Cambiar el ícono del puntero al activar la herramienta
        # self.canvas.setCursor(Qt.CrossCursor)
        self.active = True  # Cambiar el estado de activación
        QgsMapTool.activate(self)

    def deactivate(self):
        # Restaurar el ícono del puntero al desactivar la herramienta
        # self.canvas.unsetCursor()
        self.active = False  # Cambiar el estado de activación
        QgsMapTool.deactivate(self)


# Crear una instancia de la herramienta personalizada
custom_map_tool = CustomMapTool(iface.mapCanvas())
iface.mapCanvas().setMapTool(custom_map_tool)

# Crear una instancia de la clase y mostrar la caja de herramientas
custom_toolbar_panel = CustomToolbarPanel(custom_map_tool)
custom_toolbar_panel.init_panel()

# Agregar la caja de herramientas a la barra de herramientas principal
iface.addToolBar(custom_toolbar_panel.toolbox)
