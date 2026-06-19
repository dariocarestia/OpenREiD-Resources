import os
import uuid  # Agrega esta línea para importar el módulo uuid
from PyQt5.QtGui import QIcon, QCursor, QPixmap
from PyQt5.QtWidgets import QToolBar, QToolButton, QButtonGroup
from qgis.utils import iface
from qgis.PyQt.QtCore import QSize, Qt
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsPointXY
from qgis.gui import QgsMapTool

# Variable global para almacenar el estado del flujo de trabajo
estado_flujo_trabajo = None

class CustomToolbarPanel:
    def __init__(self, map_tool, node_layer, line_layer):
        self.toolbox = None
        self.tool_buttons = []
        self.button_group = None
        self.map_tool = map_tool  # Referencia a la herramienta de mapa
        self.node_layer = node_layer  # Referencia a la capa de nodos
        self.line_layer = line_layer  # Referencia a la capa de líneas

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
            self.map_tool.activate()  # Activar la herramienta de mapa

        print(f"Botón {button_name} clicado - Estado del flujo de trabajo: {estado_flujo_trabajo}")

class CustomMapTool(QgsMapTool):
    def __init__(self, canvas, node_layer, line_layer):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.active = False  # Agregar una variable para rastrear el estado de activación
        self.node_layer = node_layer  # Referencia a la capa de nodos
        self.line_layer = line_layer  # Referencia a la capa de líneas
        self.node_feature = None  # Inicializar la variable fuera del bloque condicional
        self.start_node = None
        self.end_node = None

    def canvasPressEvent(self, event):
        global estado_flujo_trabajo
        # Manejar el evento de clic del mouse
        if event.button() == Qt.LeftButton:
            print("Clic en el mapa en la posición:", event.mapPoint())
            print("Estado del flujo de trabajo:", estado_flujo_trabajo)

            if estado_flujo_trabajo == "selección":
                print("Desactivando eventos")
                self.deactivate()

            elif estado_flujo_trabajo == "nodo":
                # Generar un ID único para el nodo
                unique_node_id = str(uuid.uuid4())

                # Asegurarse de que el nombre del campo sea exactamente "id"
                field_name = "id"

                # Verificar si el campo existe en la capa de nodos
                if field_name in self.node_layer.fields().names():
                    node_feature = QgsFeature(self.node_layer.fields())
                    node_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(event.mapPoint())))
                    node_feature.setAttribute(field_name, unique_node_id)

                    # Añadir la característica a la capa de nodos
                    success, new_feature_ids = self.node_layer.dataProvider().addFeatures([node_feature])

                    if success:
                        print(f"Nodo agregado con ID: {unique_node_id}")

                        # Actualizar la vista de manera más completa
                        self.node_layer.removeSelection()
                        self.node_layer.selectByIds(new_feature_ids)
                        self.node_layer.triggerRepaint()

                    else:
                        print("Error al agregar el nodo.")

                else:
                    print(f"Error: El campo '{field_name}' no existe en la capa de nodos.")

            elif estado_flujo_trabajo == "línea":
                if not self.start_node:
                    self.start_node = find_nearest_node(self.node_layer, event.mapPoint())

                    if self.start_node:
                        print(f"Nodo de inicio ID: {self.start_node.id()}")
                    else:
                        print("No se encontró un nodo cercano al primer clic")
                else:
                    self.end_node = find_nearest_node(self.node_layer, event.mapPoint())

                    if self.end_node:
                        print(f"Nodo de fin ID: {self.end_node.id()}")
                        start_point = QgsPoint(self.start_node.geometry().asPoint())
                        end_point = QgsPoint(self.end_node.geometry().asPoint())

                        unique_line_id = str(uuid.uuid4())
                        field_names = ["id", "start_node", "end_node"]

                        if all(field_name in self.line_layer.fields().names() for field_name in field_names):
                            line_feature = QgsFeature(self.line_layer.fields())
                            line_geometry = QgsGeometry.fromPolyline([start_point, end_point])
                            line_feature.setGeometry(line_geometry)
                            line_feature.setAttribute("id", unique_line_id)
                            line_feature.setAttribute("start_node", self.start_node.attribute("id"))
                            line_feature.setAttribute("end_node", self.end_node.attribute("id"))

                            success, new_feature_ids = self.line_layer.dataProvider().addFeatures([line_feature])

                            if success:
                                print(f"Línea agregada con ID: {unique_line_id}")
                                self.line_layer.removeSelection()
                                self.line_layer.selectByIds(new_feature_ids)
                                self.line_layer.triggerRepaint()
                            else:
                                print("Error al agregar la línea.")
                        else:
                            print("Error: Campos faltantes en la capa de líneas.")
                    else:
                        print("No se encontró un nodo cercano al segundo clic")

                    self.start_node = None
                    self.end_node = None


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

def find_nearest_node(node_layer, target_point):
    nearest_node = None

    #min_distance = float('inf')
    min_distance = 20.0

    # Iterar sobre las características de la capa de nodos
    for feature in node_layer.getFeatures():
        geom = feature.geometry()
        if geom and geom.isMultipart() is False:
            # Obtener la geometría del nodo
            #node_point = geom.asPoint()
            node_point = QgsPoint(geom.asPoint())

            # Calcular la distancia entre el nodo y el punto objetivo
            distance = node_point.distance(target_point)

            # Actualizar el nodo más cercano si se encuentra uno más cercano
            if distance < min_distance:
                nearest_node = feature
                min_distance = distance

    return nearest_node

# Obtener la capa de nodos y la capa de líneas del proyecto
node_layer_name = "nodos"
line_layer_name = "lineas"

node_layer = QgsProject.instance().mapLayersByName(node_layer_name)[0]
line_layer = QgsProject.instance().mapLayersByName(line_layer_name)[0]

# Crear una instancia de la herramienta personalizada
custom_map_tool = CustomMapTool(iface.mapCanvas(), node_layer, line_layer)
iface.mapCanvas().setMapTool(custom_map_tool)

# Crear una instancia de la clase y mostrar la caja de herramientas
custom_toolbar_panel = CustomToolbarPanel(custom_map_tool, node_layer, line_layer)
custom_toolbar_panel.init_panel()

# Agregar la caja de herramientas a la barra de herramientas principal
iface.addToolBar(custom_toolbar_panel.toolbox)
