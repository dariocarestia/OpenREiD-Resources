import os
import uuid
from PyQt5.QtGui import QIcon, QCursor, QPixmap
from PyQt5.QtWidgets import QToolBar, QToolButton, QButtonGroup
from qgis.utils import iface
from qgis.PyQt.QtCore import QSize, Qt
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsPointXY, QgsPoint
from qgis.gui import QgsMapTool

from math import radians, sin, cos, sqrt, atan2

# Variable global para almacenar el estado del flujo de trabajo
estado_flujo_trabajo = None # puede ser cualquira de ["Seleccion", "Nodo", "Linea", "Interruptor", "Carga", "Generador"]
estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]


class CustomToolbarPanel:
    def __init__(self, map_tool, node_layer, line_layer):
        self.toolbox = None
        self.tool_buttons = []
        self.button_group = None
        self.map_tool = map_tool  # Referencia a la herramienta de mapa
        self.node_layer = node_layer  # Referencia a la capa de nodos
        self.line_layer = line_layer  # Referencia a la capa de lineas

    def init_panel(self):
        # Obtener la ruta del directorio de trabajo actual
        script_dir = os.getcwd()
        iconos_dir = os.path.join(script_dir, "iconos")

        # Crear la caja de herramientas
        self.toolbox = QToolBar("MiCajaDeHerramientas")
        self.toolbox.setIconSize(QSize(50, 50))  # Ajustar el tamaño del ícono según sea necesario

        # Lista de nombres de botones
        button_names = ["Seleccion", "Nodo", "Linea", "Interruptor", "Carga", "Generador"]

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

        # Desactivar cualquier herramienta de mapa activa
        iface.mapCanvas().setMapTool(None)
        # Reactivar la herramienta de mapa personalizada
        iface.mapCanvas().setMapTool(self.map_tool)

        # Cambiar el cursor al hacer clic en el botón
        if button_name.lower() == "seleccion":
            estado_flujo_trabajo = "seleccion"
            iface.mapCanvas().unsetCursor()

        else:
            estado_flujo_trabajo = button_name.lower()
            cursor = QCursor(QPixmap(cursor_icon_path), 0, 0)
            iface.mapCanvas().setCursor(cursor)

        print(f"Botón {button_name} clicado - Estado del flujo de trabajo: {estado_flujo_trabajo}")

class CustomMapTool(QgsMapTool):
    def __init__(self, canvas, node_layer, line_layer):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.active = False  # Agregar una variable para rastrear el estado de activación
        self.node_layer = node_layer  # Referencia a la capa de nodos
        self.line_layer = line_layer  # Referencia a la capa de lineas
        self.node_feature = None  # Inicializar la variable fuera del bloque condicional
        self.selected_node = None
        self.start_node = None
        self.end_node = None
        self.spatial_index = QgsSpatialIndex(node_layer.getFeatures())



    def canvasPressEvent(self, event):
        global estado_flujo_trabajo
        global estado_seleccion_linea
        global estado_seleccion_nodo
        # Manejar el evento de clic del mouse
        if event.button() == Qt.LeftButton:
            #print("Clic en el mapa en la posición:", event.mapPoint())
            #print("Estado del flujo de trabajo:", estado_flujo_trabajo)

            if estado_flujo_trabajo == "seleccion":

                estado_seleccion_linea = "Selec_None"
                print("Seleccionando")

                self.selected_node = find_nearest_node_index(self.node_layer, self.spatial_index, QgsPointXY(event.mapPoint()))

                if self.selected_node:
                    estado_seleccion_nodo = "N_Selec"
                    print(f"Nodo seleccionado: {self.selected_node.id()}")

                    # Seleccionar el nodo encontrado
                    self.node_layer.selectByIds([self.selected_node.id()])
                    self.node_layer.triggerRepaint()

                else:
                    estado_seleccion_nodo = "Selec_None"
                    print("Select nada")
                    node_layer.removeSelection()


            elif estado_flujo_trabajo == "nodo":

                estado_seleccion_linea = "Selec_None"

                # Generar un ID único para el nodo
                unique_node_id = str(uuid.uuid4())

                # Asegurarse de que el nombre del campo sea exactamente "id"
                field_name = "id"

                # Verificar si el campo existe en la capa de nodos
                if field_name in self.node_layer.fields().names():
                    node_feature = QgsFeature(self.node_layer.fields())
                    node_feature.setAttribute(field_name, unique_node_id)
                    node_geometry = QgsGeometry.fromPointXY(QgsPointXY(event.mapPoint()))
                    node_feature.setGeometry(node_geometry)

                    # Añadir la característica a la capa de nodos
                    success, new_feature_ids = self.node_layer.dataProvider().addFeatures([node_feature])

                    if success:
                        print(f"Nodo agregado con unique_node_id: {unique_node_id}")
                        # print(f"new_feature_ids: {new_feature_ids}")
                        print(f"Feature.id: {new_feature_ids[0].id()}")

                        self.node_layer.triggerRepaint()
                        # vuelve a crear el indice espacial para agregar el nodo recien insertado
                        self.spatial_index = QgsSpatialIndex(node_layer.getFeatures())

                    else:
                        print("Error al agregar el nodo.")

                else:
                    print(f"Error: El campo '{field_name}' no existe en la capa de nodos.")

            elif estado_flujo_trabajo == "linea":

                if estado_seleccion_linea == "Selec_None": # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]

                    #self.start_node = find_nearest_node(self.node_layer, QgsPoint(event.mapPoint()))
                    self.start_node = find_nearest_node_index(self.node_layer, self.spatial_index, QgsPointXY(event.mapPoint()))

                    if self.start_node:
                        estado_seleccion_linea = "N1_Selec"
                        self.createTempLineLayer()

                        print(f"Nodo de inicio ID: {self.start_node.id()}")

                    else:
                        print("Haga clic sobre el primer nodo")

                elif estado_seleccion_linea == "N1_Selec":

                    #self.end_node = find_nearest_node(self.node_layer, QgsPoint(event.mapPoint()))
                    self.end_node = find_nearest_node_index(self.node_layer, self.spatial_index, QgsPointXY(event.mapPoint()))

                    if self.end_node:
                        #estado_seleccion_linea = "Selec_None"
                                                
                        print(f"Nodo de fin ID: {self.end_node.id()}")

                        start_point = QgsPoint(self.start_node.geometry().asPoint())
                        end_point = QgsPoint(self.end_node.geometry().asPoint())

                        unique_line_id = str(uuid.uuid4())
                        field_names = ["id", "start_node", "end_node"]

                        if all(field_name in self.line_layer.fields().names() for field_name in field_names):
                            line_feature = QgsFeature(self.line_layer.fields())
                            line_feature.setAttribute("id", unique_line_id)
                            line_feature.setAttribute("start_node", self.start_node.attribute("id"))
                            line_feature.setAttribute("end_node", self.end_node.attribute("id"))
                            line_geometry = QgsGeometry.fromPolyline([start_point, end_point])
                            line_feature.setGeometry(line_geometry)

                            success, new_feature_ids = self.line_layer.dataProvider().addFeatures([line_feature])

                            if success:
                                estado_seleccion_linea = "Selec_None"
                                self.removeTempLineLayer()                                

                                print(f"Línea agregada con ID: {unique_line_id}")
                                # print(f"new_feature_ids: {new_feature_ids}")
                                print(f"Feature.id: {new_feature_ids[0].id()}")
                                self.line_layer.triggerRepaint()
                            else:
                                print("Error al agregar la línea.")
                        else:
                            print("Error: Campos faltantes en la capa de líneas.")

                    else:
                        print("Haga clic sobre el segundo nodo")


    def canvasMoveEvent(self, event):
        # Manejar el evento de movimiento del mouse
        global estado_flujo_trabajo
        global estado_seleccion_linea

        # clicked_point.x() y clicked_point.y() son expresadas en coordenadas del mapa, según el src del mapa
        clicked_point = event.mapPoint()
        #print(f"Movimiento: {clicked_point.x()}, {clicked_point.y()}")

        if estado_flujo_trabajo == "linea":

            if estado_seleccion_linea == "N1_Selec":
                self.redrawTempLineLayer(event)

            nearby_nodes = find_nearest_node_index(self.node_layer, self.spatial_index, QgsPointXY(event.mapPoint()))

            if nearby_nodes:
                #print(f"Nodo cercano: {nearby_nodes.id()}")
                # Seleccionar el nodo encontrado
                self.node_layer.selectByIds([nearby_nodes.id()])
                self.node_layer.triggerRepaint()
            else:
                #print("No se encontró un nodo cercano")
                node_layer.removeSelection()


    def createTempLineLayer(self):
        self.temp_line_layer = QgsVectorLayer("LineString?crs=EPSG:4326", "temp_line", "memory")  # Crear la capa temporal en el constructor
        QgsProject.instance().addMapLayer(self.temp_line_layer)  # Añadir la capa temporal al proyecto        
        self.temp_line_layer_provider = self.temp_line_layer.dataProvider()
        self.temp_line_layer_provider.addAttributes([QgsField("id", QVariant.String)])
        self.temp_line_layer.updateFields()
        self.temp_line_feature = None
        # Configurar la simbología para hacer visible la geometría en el mapa
        symbol = QgsLineSymbol.createSimple({'color': 'red', 'width': '0.2', 'line_style': 'dash'})
        renderer = QgsSingleSymbolRenderer(symbol)
        self.temp_line_layer.setRenderer(renderer)
        self.canvas.refresh()


    def redrawTempLineLayer(self, event):
        self.temp_line_layer_provider.deleteFeatures(self.temp_line_layer.allFeatureIds())
        self.temp_line_layer.triggerRepaint()
        # Crear una nueva línea auxiliar entre el punto de inicio y la posición actual del cursor
        start_point = QgsPoint(self.start_node.geometry().asPoint())
        end_point = QgsPoint(event.mapPoint().x(), event.mapPoint().y())
        unique_temp_line_id = str(uuid.uuid4())
        temp_line_feature = QgsFeature(self.temp_line_layer.fields())
        temp_line_feature.setAttribute("id", unique_temp_line_id)
        temp_line_geometry = QgsGeometry.fromPolyline([start_point, end_point])
        temp_line_feature.setGeometry(temp_line_geometry)
        # Añadir la línea auxiliar a la capa temporal
        self.temp_line_layer_provider.addFeature(temp_line_feature)
        # Guardar la referencia a la nueva línea auxiliar
        self.temp_line_feature = temp_line_feature
        # Forzar la actualización del lienzo
        self.canvas.refresh()


    def removeTempLineLayer(self):
        # Limpiar la capa temporal
        self.temp_line_layer_provider.deleteFeatures(self.temp_line_layer.allFeatureIds())
        self.temp_line_layer.triggerRepaint()
        QgsProject.instance().removeMapLayer(self.temp_line_layer.id())






def find_nearest_node_index(node_layer, spatial_index, target_point):
    
    scale = iface.mapCanvas().scale()
    #Ajusta max_distance_meters basado en la escala actual
    buffer_meters = scale / 100  # Ejemplo: 1 metro por cada 100 unidades en la escala

    #print(f"Escala: {scale}")
    #print(f"Buffer en metros: {buffer_meters}")

    # Convertir la distancia máxima de metros a grados utilizando una aproximación simple
    buffer_deg = buffer_meters / 111000.0  # Asumiendo que 1 grado de latitud ~ 111,000 metros
    #print(f"Buffer en deg: {buffer_deg}")

    buffer_distance = buffer_deg

    # Crear un área de selección alrededor del punto objetivo
    #buffer_distance = 0.0003  # Puedes ajustar este valor según tus necesidades
    rect = QgsRectangle(target_point.x() - buffer_distance, target_point.y() - buffer_distance, target_point.x() + buffer_distance, target_point.y() + buffer_distance)

    # Realizar una selección basada en la ubicación del punto objetivo
    node_layer.selectByRect(rect)

    # Obtener las características seleccionadas
    selected_nodes = [feature for feature in node_layer.selectedFeatures()]

    # Limpiar la selección
    #node_layer.removeSelection()

    if selected_nodes:
        # Devolver el índice del nodo más cercano entre los seleccionados
        nearest_node = min(selected_nodes, key=lambda node: node.geometry().distance(QgsGeometry.fromPointXY(target_point)))
        return nearest_node

    # Devolver None si no se encontraron nodos seleccionados
    return None



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
