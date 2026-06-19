from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QToolBar, QToolButton, QButtonGroup
from qgis.utils import iface
import os

class CustomToolbarPanel:
    def __init__(self):
        self.toolbox = None
        self.tool_buttons = []
        self.button_group = None

    def init_panel(self):
        # Obtener la ruta del directorio de trabajo actual
        script_dir = os.getcwd()

        # Crear la caja de herramientas
        self.toolbox = QToolBar("MiCajaDeHerramientas")
        self.toolbox.setIconSize(QSize(50, 50))  # Ajustar el tamaño del ícono según sea necesario

        # Lista de nombres de botones
        button_names = ["Selección", "Nodo", "Línea", "Interruptor", "Carga", "Generador"]

        # Agregar botones de opción a la caja de herramientas
        self.button_group = QButtonGroup()

        def create_handler(button_name):
            def handler():
                self.handle_button_click(button_name)
            return handler

        for button_name in button_names:
            button_icon_path = os.path.join(script_dir,"iconos", f"{button_name.lower()}.png")
            
            
            tool_button = QToolButton()
            tool_button.setIcon(QIcon(button_icon_path))
            tool_button.setCheckable(True)
            self.toolbox.addWidget(tool_button)
            self.tool_buttons.append(tool_button)
            self.button_group.addButton(tool_button)
            tool_button.clicked.connect(create_handler(button_name))

        self.button_group.setExclusive(True)

    def handle_button_click(self, button_name):
        print(f"Botón {button_name} clicado")

# Crear una instancia de la clase y mostrar la caja de herramientas
custom_toolbar_panel = CustomToolbarPanel()
custom_toolbar_panel.init_panel()

# Agregar la caja de herramientas a la barra de herramientas principal
iface.addToolBar(custom_toolbar_panel.toolbox)
