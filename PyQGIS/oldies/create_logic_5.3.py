import os
import uuid
from PyQt5.QtGui import QIcon, QCursor, QPixmap
from PyQt5.QtWidgets import QToolBar, QToolButton, QButtonGroup, QAction, QActionGroup, QApplication, QInputDialog
from qgis.utils import iface
from qgis.PyQt.QtCore import QSize, Qt
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsPointXY, QgsPoint, QgsSingleSymbolRenderer, QgsLineSymbol, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsRectangle, QVariant
from qgis.gui import QgsMapTool
import win32com.client

# Función para seleccionar el SRC
def seleccionar_src():
    crs_list = [
        "EPSG:4326",  # WGS 84
        "EPSG:22182", # POSGAR 94 / Argentina 2
        # Agrega más SRC según sea necesario
    ]
    item, ok = QInputDialog.getItem(None, "Seleccionar SRC", "Elige un Sistema de Referencia de Coordenadas (SRC):", crs_list, 0, False)
    if ok and item:
        return item
    else:
        return None

# Obtener el SRC seleccionado
app = QApplication([])
selected_crs = seleccionar_src()
if not selected_crs:
    raise Exception("No se seleccionó ningún SRC. El script se detendrá.")

# Crear el objeto CRS
crs = QgsCoordinateReferenceSystem(selected_crs)

# Transformar las coordenadas al CRS seleccionado
transformer = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:4326"), crs, QgsProject.instance())

# Función para convertir puntos al SRC seleccionado
def convert_point_to_crs(point):
    return transformer.transform(point)

# Variables de Estado Edición General:
estado_edicion = "Selec_None"  # puede ser cualquira de ["Selec_None", "Insertando", "Moviendo_Nodo"]
estado_flujo_trabajo = None # puede ser cualquira de ["Seleccion", "Nodo", "Linea", "Interruptor", "Carga", "Generador"]
estado_nivel_tension = "MT" # puede ser cualquira de ["MT", "BT"]
estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["T_Selec", "T_Pre_Selec", "Selec_None"]
estado_seleccion_seta = "Selec_None"  # puede ser cualquira de ["T_Selec", "T_Pre_Selec", "Selec_None"]
estado_seleccion_et = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]

ubicacion_switch = 0.85 # Determina la ubicación en porcentaje de la longitud de línea del switch correspondiente al terminal 2

class DSS():
    def __init__(self, end_modelo_DSS):
        self.end_modelo_DSS = end_modelo_DSS
        # Crea Conexión
        self.dssObj = win32com.client.Dispatch("OpenDSSEngine.DSS")
        # Iniciar Objeto DSS
        if self.dssObj.Start(0) == False:
            print("Problemas para iniciar OpenDSS")
        else:
            # Crea las ppales interfaces
            self.dssText = self.dssObj.Text
            self.dssCircuit = self.dssObj.ActiveCircuit
            self.dssSolution = self.dssCircuit.Solution
            self.dssCktElement = self.dssCircuit.ActiveCktElement
            self.dssBus = self.dssCircuit.ActiveBus # Para acceder a este objeto, es necesario antes de setear la barra activa
            self.dssLines = self.dssCircuit.Lines
            self.dssTransformers = self.dssCircuit.Transformers

    def version_DSS(self):
        return self.dssObj.Version

    def compilar_DSS(self):
        # Limpiar toda la información anterior
        self.dssObj.ClearAll()
        self.dssText.Command = "compile " + str(self.end_modelo_DSS)

    def resolver_DSS_snapshot(self, multiplicador_carga):
        # Configuraciones
        self.dssText.Command = "Set Mode=SnapShot"
        self.dssText.Command = "Set ControlMode=Static"
        # Multiplicar el valor nominal de las cargas por el multiplicador_carga
        self.dssSolution.LoadMult = multiplicador_carga
        # Resolver el Flujo de Potencia
        self.dssSolution.Solve()

    def obtener_resultados_potencia(self):
        self.dssText.Command = "Show powers kva elements"

    def obtener_nombre_circuito(self):
        return self.dssCircuit.Name

    def obtener_potencias_circuito(self):
        # convención -> potencia positiva si entra, negativa si sale.
        p = -self.dssCircuit.TotalPower[0] # Entrega una lista, prim elem-> p. activa
        q = -self.dssCircuit.TotalPower[1]  # Segundo elem. -> p. reactiva
        return p, q

    def activar_barra(self, nombre_barra):
        self.dssCircuit.SetActiveBus(nombre_barra)
        return self.dssBus.Name

    def obtener_distancia_barra(self):
        return self.dssBus.Distance

    def obtener_kVBase_barra(self):
        return self.dssBus.kVBase

    def obtener_VMagAng_barra(self):
        return self.dssBus.VMagAngle

    def activar_elemento(self, nombre_elemento):
        # Activa elemento por su nombre completo Tipo.Nombre
        self.dssCircuit.SetActiveElement(nombre_elemento)
        # Retornar el nombre del elemento activado
        return self.dssCktElement.Name

    def obtener_barras_elemento(self):
        barras = self.dssCktElement.BusNames
        barra1 = barras[0]
        barra2 = barras[1]
        return barra1, barra2

    def obtener_tensiones_elemento(self):
        return self.dssCktElement.VoltagesMagAng

    def obtener_potencias_elemento(self):
        return self.dssCktElement.Powers

    def obtener_nombre_linea(self):
        return self.dssLines.Name

    def obtener_tamaño_linea(self):
        return self.dssLines.Length

    def establecer_tamaño_linea(self, tamaño):
        self.dssLines.Length = tamaño

    def obtener_nombre_transformador(self):
        return self.dssTransformers.Name

    def obtener_tension_terminal_transformador(self, terminal):
        # Activa uno de los terminales del transformador
        self.dssTransformers.Wdg = terminal
        return self.dssTransformers.kV

    def obtener_nombre_y_tamaño_lineas(self):
        # Definiendo dos listas
        nombre_lineas_lista = []
        tamaño_lineas_lista = []
        # Selecciona la primera línea
        self.dssLines.First #Es raro, pero en la info dice:
        #Invoking this property sets the first element active.
        #Returns 0 if no lines.  Otherwise, index of the line element.

        for i in range(self.dssLines.Count):

            print("Elemento Activo:", self.dssCktElement.Name) #Aqui compriebo que va cambiando el elemento activo

            nombre_lineas_lista.append(self.dssLines.Name)
            tamaño_lineas_lista.append(self.dssLines.Length)
            self.dssLines.Next

        return nombre_lineas_lista, tamaño_lineas_lista

class CustomToolbarPanel:
    def __init__(self, map_tool, node_mt_layer, node_bt_layer, line_mt_layer, line_bt_layer, generator_layer, load_layer, switch_layer, transformer_layer, et_layer, seta_layer):
        self.toolbox = None
        self.tool_buttons = []
        self.button_group = None
        self.map_tool = map_tool  # Referencia a la herramienta de mapa
        self.node_mt_layer = node_mt_layer  # Referencia a la capa de nodos
        self.node_bt_layer = node_bt_layer  # Referencia a la capa de nodos
        self.line_mt_layer = line_mt_layer  # Referencia a la capa de lineas
        self.line_bt_layer = line_bt_layer  # Referencia a la capa de lineas
        self.generator_layer = generator_layer  # Referencia a la capa de lineas
        self.load_layer = load_layer  # Referencia a la capa de cargas
        self.switch_layer = switch_layer  # Referencia a la capa de interruptores
        self.transformer_layer = transformer_layer  # Referencia a la capa de transformadores
        self.et_layer = et_layer  # Referencia a la capa de estacion_transformadora
        self.seta_layer = seta_layer # Referencia a la capa de setas
        self.voltage_action_group = None  # Grupo de acciones para seleccionar el voltaje

    def init_panel(self):
        # Crear la caja de herramientas
        self.toolbox = QToolBar("OpenREiD")
        self.toolbox.setIconSize(QSize(50, 50))  # Ajustar el tamaño del ícono según sea necesario

        # Crear acciones para seleccionar el tipo de voltaje
        self.voltage_action_group = QActionGroup(self.toolbox)
        self.voltage_action_group.setExclusive(True)

        # Acción para Media Tensión
        mt_action = QAction("MT", self.toolbox)
        mt_action.setCheckable(True)
        mt_action.setChecked(True)  # Por defecto seleccionado
        mt_action.setToolTip("Edición en Media Tensión")  # Editar el texto del tooltip aquí
        mt_action.triggered.connect(lambda: self.handle_voltage_change("MT"))
        self.voltage_action_group.addAction(mt_action)
        self.toolbox.addAction(mt_action)

        # Acción para Baja Tensión
        bt_action = QAction("BT", self.toolbox)
        bt_action.setCheckable(True)
        bt_action.setToolTip("Edición en Baja Tensión")  # Editar el texto del tooltip aquí
        bt_action.triggered.connect(lambda: self.handle_voltage_change("BT"))
        self.voltage_action_group.addAction(bt_action)
        self.toolbox.addAction(bt_action)

        # Obtener la ruta del directorio de trabajo actual
        script_dir = os.getcwd()
        iconos_dir = os.path.join(script_dir, "iconos")

        # Lista de nombres de botones
        button_names = [
            ("Seleccion", "Seleccionar elementos en el mapa"),
            ("Estacion_transformadora", "Agregar una estación transformadora"),
            ("Nodo", "Agregar un nodo"),
            ("Linea", "Agregar una línea"),
            ("Interruptor", "Agregar un interruptor"),
            ("Carga", "Agregar una carga"),
            ("Generador", "Agregar un generador"),
            ("Transformador", "Agregar un transformador"),
            ("Seta", "Agregar una seta"),
            ("DSS", "Importar dss")
        ]

        # Agregar botones de opción a la caja de herramientas
        self.button_group = QButtonGroup()

        def create_handler(button_name, cursor_icon_path):
            def handler():
                self.handle_button_click(button_name, cursor_icon_path)
            return handler

        for button_name, tooltip in button_names:
            button_icon_path = os.path.join(iconos_dir, f"{button_name.lower()}.png")
            cursor_icon_path = os.path.join(iconos_dir, f"{button_name.lower()}.cur")
            tool_button = QToolButton()
            tool_button.setIcon(QIcon(button_icon_path))
            tool_button.setCheckable(True)
            tool_button.setObjectName(button_name.lower())
            tool_button.setToolTip(tooltip)  # Establecer el tooltip aquí
            self.toolbox.addWidget(tool_button)
            self.tool_buttons.append(tool_button)
            self.button_group.addButton(tool_button)
            tool_button.clicked.connect(create_handler(button_name, cursor_icon_path))

        self.button_group.setExclusive(True)

    def handle_voltage_change(self, voltage_type):
        global estado_nivel_tension
        print(f"Voltaje seleccionado: {voltage_type}")
        # Encuentra los botones específicos por su texto o alguna otra propiedad identificativa
        estacion_transformadora_button = next((btn for btn in self.tool_buttons if btn.objectName() == "estacion_transformadora"), None)
        seta_button = next((btn for btn in self.tool_buttons if btn.objectName() == "seta"), None)

        if voltage_type == "MT":
            estado_nivel_tension = "MT"
            # Habilitar los botones            
            if estacion_transformadora_button:
                estacion_transformadora_button.setEnabled(True)
            if seta_button:
                seta_button.setEnabled(True)
        elif voltage_type == "BT":
            estado_nivel_tension = "BT"
            # Deshabilitar los botones
            if estacion_transformadora_button:
                estacion_transformadora_button.setEnabled(False)
            if seta_button:
                seta_button.setEnabled(False)

    def handle_button_click(self, button_name, cursor_icon_path):
        global estado_flujo_trabajo
        global estado_edicion
        # Desactivar cualquier herramienta de mapa activa
        iface.mapCanvas().setMapTool(None)
        # Reactivar la herramienta de mapa personalizada
        iface.mapCanvas().setMapTool(self.map_tool)
        
        # Cambiar el cursor al hacer clic en el botón
        if button_name.lower() == "seleccion":
            estado_flujo_trabajo = "seleccion"
            estado_edicion = "Selec_None"
            iface.mapCanvas().unsetCursor()
        elif  button_name.lower() == "dss":
            estado_flujo_trabajo = "dss"
            estado_edicion = "Selec_None"
            iface.mapCanvas().unsetCursor()
            import_dss(self.map_tool.node_mt_layer, self.map_tool.line_mt_layer)
        else:
            estado_flujo_trabajo = button_name.lower()
            estado_edicion = "Insertando"   
            cursor = QCursor(QPixmap(cursor_icon_path), 0, 0)
            iface.mapCanvas().setCursor(cursor)
        print(f"Botón {button_name} clicado - Estado del flujo de trabajo: {estado_flujo_trabajo}")

# Esta clase maneja toda la lógica de edición gráfica de elementos de la red eléctrica
class CustomMapTool(QgsMapTool):
    def __init__(self, canvas, node_mt_layer, node_bt_layer, line_mt_layer, line_bt_layer, generator_layer, load_layer, switch_layer, transformer_layer, et_layer, seta_layer):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.active = False  # Agregar una variable para rastrear el estado de activación
        self.node_mt_layer = node_mt_layer  # Referencia a la capa de nodos
        self.node_bt_layer = node_bt_layer  # Referencia a la capa de nodos
        self.line_mt_layer = line_mt_layer  # Referencia a la capa de lineas
        self.line_bt_layer = line_bt_layer  # Referencia a la capa de lineas
        self.generator_layer = generator_layer  # Referencia a la capa de generadores
        self.load_layer = load_layer  # Referencia a la capa de cargas
        self.switch_layer = switch_layer  # Referencia a la capa de interruptores
        self.transformer_layer = transformer_layer  # Referencia a la capa de transformadores
        self.et_layer = et_layer  # Referencia a la capa de transformadores
        self.seta_layer = seta_layer # Referencia a la capa de setas
        self.node_feature = None  # Inicializar la variable fuera del bloque condicional
        self.selected_node = None
        self.start_node = None
        self.end_node = None
        self.linked_line = None  # línea para asociar a un elemento de control
        self.linked_node = None  # Terminal asociado

        self.associated_mt_lines = []  # Se utilizan tanto para el movimiento de un nodo_mt como un nodo_bt 
        self.associated_bt_lines = []  # Se utilizan tanto para el movimiento de un nodo_mt como un nodo_bt 
        self.associated_mt_nodes = [] # En realidad va a ser solo uno, es el nodo_mt binculado por una seta
        self.associated_bt_nodes = [] # En realidad va a ser solo uno, es el nodo_bt binculado por una seta
        self.associated_generators = [] #La restricción de ingreso no debe permitir mas de 1 elemento
        self.associated_loads = [] #La restricción de ingreso no debe permitir mas de 1 elemento
        self.associated_switches = [] #La restricción de ingreso no debe permitir mas de 1 elemento

        self.associated_transformers = [] #La restricción de ingreso no debe permitir mas de 1 elemento
        self.associated_ets = [] #Debido a la forma de creación se asegura 1 solo elemento
        self.associated_setas = [] #La restricción de ingreso no debe permitir mas de 1 elemento

    def canvasPressEvent(self, event): #Este evento de dispara al presionar, no al hacer clic (presionar y soltar)
        print("canvasPressEvent")
        global estado_nivel_tension
        global estado_flujo_trabajo
        global estado_seleccion_linea
        global estado_seleccion_nodo
        global estado_seleccion_generador
        global estado_seleccion_carga
        global estado_seleccion_interruptor
        global estado_seleccion_transformador
        global estado_seleccion_seta
        global estado_seleccion_et
        global estado_edicion

        # Convertir la coordenada del evento al SRC seleccionado
        clicked_point = convert_point_to_crs(event.mapPoint())

        if estado_nivel_tension == "MT":
            if event.button() == Qt.RightButton:
                if estado_flujo_trabajo == "linea":
                    if estado_seleccion_linea == "N1_Selec":
                        estado_seleccion_linea = "Selec_None"
                        self.removeTempLineLayer()
                        self.line_mt_layer.triggerRepaint()
            elif event.button() == Qt.LeftButton:
                if estado_flujo_trabajo == "seleccion":
                    estado_seleccion_linea = "Selec_None"
                    estado_seleccion_nodo = "Selec_None"
                    estado_seleccion_generador = "Selec_None"
                    estado_seleccion_carga = "Selec_None"
                    estado_seleccion_interruptor = "Selec_None"
                    estado_seleccion_transformador = "Selec_None"
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("Seleccionando")
                    self.selected_node = find_nearest_node_index(self.node_mt_layer, clicked_point)
                    if self.selected_node:
                        estado_seleccion_nodo = "N_Selec"
                        print(f"Nodo seleccionado: {self.selected_node.id()}")
                        self.startNode_Mt_Movement(self.selected_node.attribute("id"), estado_nivel_tension)
                        self.node_mt_layer.selectByIds([self.selected_node.id()])
                        self.node_mt_layer.triggerRepaint()
                        estado_edicion = "Moviendo_Nodo"
                elif estado_flujo_trabajo == "nodo":
                    estado_seleccion_linea = "Selec_None"
                    estado_seleccion_generador = "Selec_None"
                    estado_seleccion_carga = "Selec_None"
                    estado_seleccion_interruptor = "Selec_None"
                    estado_seleccion_transformador = "Selec_None"
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando nodo")
                    unique_node_id = str(uuid.uuid4())
                    field_name = "id"
                    if field_name in self.node_mt_layer.fields().names():
                        node_feature = QgsFeature(self.node_mt_layer.fields())
                        node_feature.setAttribute(field_name, unique_node_id)
                        node_geometry = QgsGeometry.fromPointXY(clicked_point)
                        node_feature.setGeometry(node_geometry)
                        success, new_feature_ids = self.node_mt_layer.dataProvider().addFeatures([node_feature])
                        if success:
                            print(f"Nodo agregado con unique_node_id: {unique_node_id}")
                            self.node_mt_layer.triggerRepaint()
                        else:
                            print("Error al agregar el nodo.")
                    else:
                        print(f"Error: El campo '{field_name}' no existe en la capa de nodos.")
                elif estado_flujo_trabajo == "linea":
                    estado_seleccion_nodo = "Selec_None"
                    estado_seleccion_generador = "Selec_None"
                    estado_seleccion_carga = "Selec_None"
                    estado_seleccion_interruptor = "Selec_None"
                    estado_seleccion_transformador = "Selec_None"
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando linea")
                    if estado_seleccion_linea == "Selec_None":
                        self.start_node = find_nearest_node_index(self.node_mt_layer, clicked_point)
                        if self.start_node:
                            estado_seleccion_linea = "N1_Selec"
                            self.createTempLineLayer()
                            print(f"Nodo de inicio ID: {self.start_node.id()}")
                        else:
                            print("Haga clic sobre el primer nodo")
                    elif estado_seleccion_linea == "N1_Selec":
                        self.end_node = find_nearest_node_index(self.node_mt_layer, clicked_point)
                        if self.end_node:
                            start_point = QgsPoint(self.start_node.geometry().asPoint())
                            end_point = QgsPoint(self.end_node.geometry().asPoint())
                            unique_line_id = str(uuid.uuid4())
                            field_names = ["id", "start_node", "end_node"]
                            if all(field_name in self.line_mt_layer.fields().names() for field_name in field_names):
                                line_feature = QgsFeature(self.line_mt_layer.fields())
                                line_feature.setAttribute("id", unique_line_id)
                                line_feature.setAttribute("start_node", self.start_node.attribute("id"))
                                line_feature.setAttribute("end_node", self.end_node.attribute("id"))
                                line_geometry = QgsGeometry.fromPolyline([start_point, end_point])
                                line_feature.setGeometry(line_geometry)
                                success, new_feature_ids = self.line_mt_layer.dataProvider().addFeatures([line_feature])
                                if success:
                                    estado_seleccion_linea = "Selec_None"
                                    self.removeTempLineLayer()
                                    print(f"Línea agregada con ID: {unique_line_id}")
                                    self.line_mt_layer.triggerRepaint()
                                else:
                                    print("Error al agregar la línea.")
                            else:
                                print("Error: Campos faltantes en la capa de líneas.")
                        else:
                            print("Haga clic sobre el segundo nodo")
                elif estado_flujo_trabajo == "generador":
                    estado_seleccion_linea = "Selec_None"
                    estado_seleccion_nodo = "Selec_None"
                    estado_seleccion_carga = "Selec_None"
                    estado_seleccion_interruptor = "Selec_None"
                    estado_seleccion_transformador = "Selec_None"
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando generador")
                    if estado_seleccion_generador == "Selec_None":
                        self.start_node = find_nearest_node_index(self.node_mt_layer, clicked_point)
                        if self.start_node:
                            start_point = QgsPointXY(self.start_node.geometry().asPoint())
                            unique_generator_id = str(uuid.uuid4())
                            field_names = ["id", "start_node"]
                            if all(field_name in self.generator_layer.fields().names() for field_name in field_names):
                                generator_feature = QgsFeature(self.generator_layer.fields())
                                generator_feature.setAttribute("id", unique_generator_id)
                                generator_feature.setAttribute("start_node", self.start_node.attribute("id"))
                                generator_geometry = QgsGeometry.fromPointXY(start_point)
                                generator_feature.setGeometry(generator_geometry)
                                success, new_feature_ids = self.generator_layer.dataProvider().addFeatures([generator_feature])
                                if success:
                                    estado_seleccion_generador = "Selec_None"
                                    print(f"Generador agregado con ID: {unique_generator_id}")
                                    self.generator_layer.triggerRepaint()
                                else:
                                    print("Error al agregar el generador.")
                            else:
                                print("Error: Campos faltantes en la capa de generadores.")
                        else:
                            print("Haga clic sobre un nodo")
                elif estado_flujo_trabajo == "carga":
                    estado_seleccion_linea = "Selec_None"
                    estado_seleccion_nodo = "Selec_None"
                    estado_seleccion_generador = "Selec_None"
                    estado_seleccion_interruptor = "Selec_None"
                    estado_seleccion_transformador = "Selec_None"
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando carga")
                    if estado_seleccion_carga == "Selec_None":
                        self.start_node = find_nearest_node_index(self.node_mt_layer, clicked_point)
                        if self.start_node:
                            start_point = QgsPointXY(self.start_node.geometry().asPoint())
                            unique_load_id = str(uuid.uuid4())
                            field_names = ["id", "start_node"]
                            if all(field_name in self.load_layer.fields().names() for field_name in field_names):
                                load_feature = QgsFeature(self.load_layer.fields())
                                load_feature.setAttribute("id", unique_load_id)
                                load_feature.setAttribute("start_node", self.start_node.attribute("id"))
                                load_geometry = QgsGeometry.fromPointXY(start_point)
                                load_feature.setGeometry(load_geometry)
                                success, new_feature_ids = self.load_layer.dataProvider().addFeatures([load_feature])
                                if success:
                                    estado_seleccion_carga = "Selec_None"
                                    print(f"Carga agregada con ID: {unique_load_id}")
                                    self.load_layer.triggerRepaint()
                                else:
                                    print("Error al agregar la carga.")
                            else:
                                print("Error: Campos faltantes en la capa de cargas.")
                        else:
                            print("Haga clic sobre un nodo")
                elif estado_flujo_trabajo == "interruptor":
                    estado_seleccion_linea = "Selec_None"
                    estado_seleccion_nodo = "Selec_None"
                    estado_seleccion_generador = "Selec_None"
                    estado_seleccion_carga = "Selec_None"
                    estado_seleccion_transformador = "Selec_None"
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando interruptor")
                    if estado_seleccion_interruptor == "Selec_None":
                        self.linked_line, terminal, point_on_line  = find_nearest_line_index(self.line_mt_layer, self.node_mt_layer, clicked_point)
                        if self.linked_line:
                            start_point = point_on_line
                            unique_switch_id = str(uuid.uuid4())
                            field_names = ["id", "line", "terminal"]
                            if all(field_name in self.switch_layer.fields().names() for field_name in field_names):
                                switch_feature = QgsFeature(self.switch_layer.fields())
                                switch_feature.setAttribute("id", unique_switch_id)
                                switch_feature.setAttribute("line", self.linked_line.attribute("id"))
                                switch_feature.setAttribute("terminal", terminal)
                                switch_geometry = start_point
                                switch_feature.setGeometry(switch_geometry)
                                success, new_feature_ids = self.switch_layer.dataProvider().addFeatures([switch_feature])
                                if success:
                                    estado_seleccion_interruptor = "Selec_None"
                                    print(f"Interruptor agregado con ID: {unique_switch_id}")
                                    self.switch_layer.triggerRepaint()
                                else:
                                    print("Error al agregar el interruptor.")
                            else:
                                print("Error: Campos faltantes en la capa de interruptores.")
                        else:
                            print("Haga clic sobre una línea")
                elif estado_flujo_trabajo == "transformador":
                    estado_seleccion_linea = "Selec_None"
                    estado_seleccion_nodo = "Selec_None"
                    estado_seleccion_generador = "Selec_None"
                    estado_seleccion_carga = "Selec_None"
                    estado_seleccion_interruptor = "Selec_None"
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando transformador")
                    if estado_seleccion_transformador == "Selec_None":
                        self.start_node = find_nearest_node_index(self.node_mt_layer, clicked_point)
                        if self.start_node:
                            start_point = QgsPointXY(self.start_node.geometry().asPoint())

                            unique_node_id = str(uuid.uuid4())
                            field_name = "id"
                            if field_name in self.node_bt_layer.fields().names():
                                node_feature = QgsFeature(self.node_bt_layer.fields())
                                node_feature.setAttribute(field_name, unique_node_id)
                                node_geometry = QgsGeometry.fromPointXY(start_point)
                                node_feature.setGeometry(node_geometry)
                                success, new_feature_ids = self.node_bt_layer.dataProvider().addFeatures([node_feature])
                                if success:
                                    print(f"Nodo BT agregado con unique_node_id: {unique_node_id}")
                                    self.node_bt_layer.triggerRepaint()
                                else:
                                    print("Error al agregar el nodo.")
                            else:
                                print(f"Error: El campo '{field_name}' no existe en la capa de nodos.")

                            unique_transformer_id = str(uuid.uuid4())
                            field_names = ["id", "wdg1_node", "wdg2_node"]
                            if all(field_name in self.transformer_layer.fields().names() for field_name in field_names):
                                transformer_feature = QgsFeature(self.transformer_layer.fields())
                                transformer_feature.setAttribute("id", unique_transformer_id)
                                transformer_feature.setAttribute("wdg1_node", self.start_node.attribute("id"))                            
                                transformer_feature.setAttribute("wdg2_node", unique_node_id)
                                transformer_geometry = QgsGeometry.fromPointXY(start_point)
                                transformer_feature.setGeometry(transformer_geometry)
                                success, new_feature_ids = self.transformer_layer.dataProvider().addFeatures([transformer_feature])
                                if success:
                                    estado_seleccion_transformador = "Selec_None"
                                    print(f"Transformador agregado con ID: {unique_transformer_id}")
                                    self.transformer_layer.triggerRepaint()
                                else:
                                    print("Error al agregar la transformador.")
                            else:
                                print("Error: Campos faltantes en la capa de transformadores.")
                        else:
                            print("Haga clic sobre un nodo")
                elif estado_flujo_trabajo == "estacion_transformadora":
                    estado_seleccion_linea = "Selec_None"
                    estado_seleccion_nodo = "Selec_None"
                    estado_seleccion_generador = "Selec_None"
                    estado_seleccion_carga = "Selec_None"
                    estado_seleccion_interruptor = "Selec_None"
                    estado_seleccion_transformador = "Selec_None"

                    print("agregando estacion transformadora")
                    
                    unique_node_id = str(uuid.uuid4())
                    field_name = "id"
                    if field_name in self.node_mt_layer.fields().names():
                        node_feature = QgsFeature(self.node_mt_layer.fields())
                        node_feature.setAttribute(field_name, unique_node_id)
                        node_geometry = QgsGeometry.fromPointXY(clicked_point)
                        node_feature.setGeometry(node_geometry)
                        success, new_feature_ids = self.node_mt_layer.dataProvider().addFeatures([node_feature])
                        if success:
                            print(f"Nodo MT agregado con unique_node_id: {unique_node_id}")
                            self.node_mt_layer.triggerRepaint()
                        else:
                            print("Error al agregar el nodo.")
                    else:
                        print(f"Error: El campo '{field_name}' no existe en la capa de nodos.")

                    unique_et_id = str(uuid.uuid4())
                    field_names = ["id", "start_node"]
                    if all(field_name in self.et_layer.fields().names() for field_name in field_names):
                        et_feature = QgsFeature(self.et_layer.fields())
                        et_feature.setAttribute("id", unique_et_id)
                        et_feature.setAttribute("start_node", unique_node_id)                            
                        et_geometry = QgsGeometry.fromPointXY(clicked_point)
                        et_feature.setGeometry(et_geometry)
                        success, new_feature_ids = self.et_layer.dataProvider().addFeatures([et_feature])
                        if success:
                            print(f"estacion transformadora agregada con ID: {unique_et_id}")
                            self.et_layer.triggerRepaint()
                        else:
                            print("Error al agregar la estacion transformadora.")
                    else:
                        print("Error: Campos faltantes en la capa de estacion_transformadora.")
                elif estado_flujo_trabajo == "seta":
                    estado_seleccion_linea = "Selec_None"
                    estado_seleccion_nodo = "Selec_None"
                    estado_seleccion_generador = "Selec_None"
                    estado_seleccion_carga = "Selec_None"
                    estado_seleccion_interruptor = "Selec_None"
                    estado_seleccion_transformador = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando seta")
                    if estado_seleccion_seta == "Selec_None":
                        self.start_node = find_nearest_node_index(self.node_mt_layer, clicked_point)
                        if self.start_node:
                            start_point = QgsPointXY(self.start_node.geometry().asPoint())

                            unique_node_id = str(uuid.uuid4())
                            field_name = "id"
                            if field_name in self.node_bt_layer.fields().names():
                                node_feature = QgsFeature(self.node_bt_layer.fields())
                                node_feature.setAttribute(field_name, unique_node_id)
                                node_geometry = QgsGeometry.fromPointXY(start_point)
                                node_feature.setGeometry(node_geometry)
                                success, new_feature_ids = self.node_bt_layer.dataProvider().addFeatures([node_feature])
                                if success:
                                    print(f"Nodo BT agregado con unique_node_id: {unique_node_id}")
                                    self.node_bt_layer.triggerRepaint()
                                else:
                                    print("Error al agregar el nodo.")
                            else:
                                print(f"Error: El campo '{field_name}' no existe en la capa de nodos.")

                            unique_seta_id = str(uuid.uuid4())
                            field_names = ["id", "wdg1_node", "wdg2_node"]
                            if all(field_name in self.seta_layer.fields().names() for field_name in field_names):
                                seta_feature = QgsFeature(self.seta_layer.fields())
                                seta_feature.setAttribute("id", unique_seta_id)
                                seta_feature.setAttribute("wdg1_node", self.start_node.attribute("id"))                            
                                seta_feature.setAttribute("wdg2_node", unique_node_id)
                                seta_geometry = QgsGeometry.fromPointXY(start_point)
                                seta_feature.setGeometry(seta_geometry)
                                success, new_feature_ids = self.seta_layer.dataProvider().addFeatures([seta_feature])
                                if success:
                                    estado_seleccion_seta = "Selec_None"
                                    print(f"Seta agregada con ID: {unique_seta_id}")
                                    self.seta_layer.triggerRepaint()
                                else:
                                    print("Error al agregar la seta.")
                            else:
                                print("Error: Campos faltantes en la capa de setas.")
                        else:
                            print("Haga clic sobre un nodo")
        elif estado_nivel_tension == "BT":
            if event.button() == Qt.RightButton:
                if estado_flujo_trabajo == "linea":
                    if estado_seleccion_linea == "N1_Selec":
                        estado_seleccion_linea = "Selec_None"
                        self.removeTempLineLayer()
                        self.line_bt_layer.triggerRepaint()
            elif event.button() == Qt.LeftButton:
                if estado_flujo_trabajo == "seleccion":
                    estado_seleccion_linea = "Selec_None"
                    estado_seleccion_nodo = "Selec_None"
                    estado_seleccion_generador = "Selec_None"
                    estado_seleccion_carga = "Selec_None"
                    estado_seleccion_interruptor = "Selec_None"
                    estado_seleccion_transformador = "Selec_None"
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("Seleccionando")
                    self.selected_node = find_nearest_node_index(self.node_bt_layer, clicked_point)
                    if self.selected_node:
                        estado_seleccion_nodo = "N_Selec"
                        print(f"Nodo seleccionado: {self.selected_node.id()}")
                        self.startNode_Bt_Movement(self.selected_node.attribute("id"), estado_nivel_tension)
                        self.node_bt_layer.selectByIds([self.selected_node.id()])
                        self.node_bt_layer.triggerRepaint()
                        estado_edicion = "Moviendo_Nodo"
                elif estado_flujo_trabajo == "nodo":
                    estado_seleccion_linea = "Selec_None"
                    estado_seleccion_generador = "Selec_None"
                    estado_seleccion_carga = "Selec_None"
                    estado_seleccion_interruptor = "Selec_None"
                    estado_seleccion_transformador = "Selec_None"
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando nodo")
                    unique_node_id = str(uuid.uuid4())
                    field_name = "id"
                    if field_name in self.node_bt_layer.fields().names():
                        node_feature = QgsFeature(self.node_bt_layer.fields())
                        node_feature.setAttribute(field_name, unique_node_id)
                        node_geometry = QgsGeometry.fromPointXY(clicked_point)
                        node_feature.setGeometry(node_geometry)
                        success, new_feature_ids = self.node_bt_layer.dataProvider().addFeatures([node_feature])
                        if success:
                            print(f"Nodo agregado con unique_node_id: {unique_node_id}")
                            self.node_bt_layer.triggerRepaint()
                        else:
                            print("Error al agregar el nodo.")
                    else:
                        print(f"Error: El campo '{field_name}' no existe en la capa de nodos.")
                elif estado_flujo_trabajo == "linea":
                    estado_seleccion_nodo = "Selec_None"
                    estado_seleccion_generador = "Selec_None"
                    estado_seleccion_carga = "Selec_None"
                    estado_seleccion_interruptor = "Selec_None"
                    estado_seleccion_transformador = "Selec_None"
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando linea")
                    if estado_seleccion_linea == "Selec_None":
                        self.start_node = find_nearest_node_index(self.node_bt_layer, clicked_point)
                        if self.start_node:
                            estado_seleccion_linea = "N1_Selec"
                            self.createTempLineLayer()
                            print(f"Nodo de inicio ID: {self.start_node.id()}")
                        else:
                            print("Haga clic sobre el primer nodo")
                    elif estado_seleccion_linea == "N1_Selec":
                        self.end_node = find_nearest_node_index(self.node_bt_layer, clicked_point)
                        if self.end_node:
                            start_point = QgsPoint(self.start_node.geometry().asPoint())
                            end_point = QgsPoint(self.end_node.geometry().asPoint())
                            unique_line_id = str(uuid.uuid4())
                            field_names = ["id", "start_node", "end_node"]
                            if all(field_name in self.line_bt_layer.fields().names() for field_name in field_names):
                                line_feature = QgsFeature(self.line_bt_layer.fields())
                                line_feature.setAttribute("id", unique_line_id)
                                line_feature.setAttribute("start_node", self.start_node.attribute("id"))
                                line_feature.setAttribute("end_node", self.end_node.attribute("id"))
                                line_geometry = QgsGeometry.fromPolyline([start_point, end_point])
                                line_feature.setGeometry(line_geometry)
                                success, new_feature_ids = self.line_bt_layer.dataProvider().addFeatures([line_feature])
                                if success:
                                    estado_seleccion_linea = "Selec_None"
                                    self.removeTempLineLayer()
                                    print(f"Línea agregada con ID: {unique_line_id}")
                                    self.line_bt_layer.triggerRepaint()
                                else:
                                    print("Error al agregar la línea.")
                            else:
                                print("Error: Campos faltantes en la capa de líneas.")
                        else:
                            print("Haga clic sobre el segundo nodo")

    def canvasMoveEvent(self, event):
        global estado_nivel_tension
        global estado_flujo_trabajo
        global estado_seleccion_linea
        global estado_seleccion_generador
        global estado_seleccion_carga
        global estado_edicion

        # Convertir la coordenada del evento al SRC seleccionado
        clicked_point = convert_point_to_crs(event.mapPoint())

        if estado_nivel_tension == "MT":
            if estado_flujo_trabajo == "linea":
                if estado_seleccion_linea == "N1_Selec":
                    self.redrawTempLineLayer(event)
                nearby_nodes = find_nearest_node_index(self.node_mt_layer, clicked_point)
                if nearby_nodes:
                    print(f"Nodo cercano: {nearby_nodes.id()}")
                    self.node_mt_layer.selectByIds([nearby_nodes.id()])
                    self.node_mt_layer.triggerRepaint()
                else:
                    self.node_mt_layer.removeSelection()
            elif estado_flujo_trabajo == "generador":
                nearby_nodes = find_nearest_node_index(self.node_mt_layer, clicked_point)
                if nearby_nodes:
                    self.node_mt_layer.selectByIds([nearby_nodes.id()])
                    self.node_mt_layer.triggerRepaint()
                else:
                    self.node_mt_layer.removeSelection()
            elif estado_flujo_trabajo == "carga":
                nearby_node = find_nearest_node_index(self.node_mt_layer, clicked_point)
                if nearby_node:
                    self.node_mt_layer.selectByIds([nearby_node.id()])
                    self.node_mt_layer.triggerRepaint()
                else:
                    self.node_mt_layer.removeSelection()
            elif estado_flujo_trabajo == "interruptor":
                nearby_line, terminal, point_on_line = find_nearest_line_index(self.line_mt_layer, self.node_mt_layer, clicked_point)
                if nearby_line:
                    print(f"Línea cercana: {nearby_line.id()}, Terminal: {terminal}")
                    self.line_mt_layer.selectByIds([nearby_line.id()])
                    self.line_mt_layer.triggerRepaint()
                else:
                    print("No se encontró una línea cercana")
                    self.line_mt_layer.removeSelection()
            elif estado_flujo_trabajo == "transformador":
                nearby_node = find_nearest_node_index(self.node_mt_layer, clicked_point)
                if nearby_node:
                    self.node_mt_layer.selectByIds([nearby_node.id()])
                    self.node_mt_layer.triggerRepaint()
                else:
                    self.node_mt_layer.removeSelection()
            elif estado_flujo_trabajo == "seta":
                nearby_node = find_nearest_node_index(self.node_mt_layer, clicked_point)
                if nearby_node:
                    self.node_mt_layer.selectByIds([nearby_node.id()])
                    self.node_mt_layer.triggerRepaint()
                else:
                    self.node_mt_layer.removeSelection()
            if estado_edicion == "Moviendo_Nodo" and self.selected_node:
                new_geom = QgsGeometry.fromPointXY(clicked_point)
                self.node_mt_layer.startEditing()
                self.node_mt_layer.changeGeometry(self.selected_node.id(), new_geom)
                moving_node_id = self.selected_node.attribute("id")

                for line_feat in self.associated_mt_lines:
                    updateLineGeometry(self.line_mt_layer, line_feat, clicked_point, moving_node_id)

                for generator_feat in self.associated_generators:
                    self.updateGeneratorGeometry(generator_feat, clicked_point)

                for load_feat in self.associated_loads:
                    self.updateLoadGeometry(load_feat, clicked_point)

                for transformer_feat in self.associated_transformers:
                    self.updateTransformerGeometry(transformer_feat, clicked_point)

                for et_feat in self.associated_ets:
                    self.updateEtGeometry(et_feat, clicked_point)

                for switch_feat in self.associated_switches:
                    self.updateSwitchGeometry(switch_feat)

                for seta_feat in self.associated_setas:
                    self.updateSetaGeometry(seta_feat, clicked_point)

                for node_feat in self.associated_bt_nodes:
                    updateNodeGeometry(self.node_bt_layer, node_feat, clicked_point)
                    moving_node_id = node_feat.attribute("id")

                    for line_feat in self.associated_bt_lines:
                        updateLineGeometry(self.line_bt_layer, line_feat, clicked_point, moving_node_id)
        elif estado_nivel_tension == "BT":
            if estado_flujo_trabajo == "linea":
                if estado_seleccion_linea == "N1_Selec":
                    self.redrawTempLineLayer(event)
                nearby_nodes = find_nearest_node_index(self.node_bt_layer, clicked_point)
                if nearby_nodes:
                    print(f"Nodo cercano: {nearby_nodes.id()}")
                    self.node_bt_layer.selectByIds([nearby_nodes.id()])
                    self.node_bt_layer.triggerRepaint()
                else:
                    self.node_bt_layer.removeSelection()
            if estado_edicion == "Moviendo_Nodo" and self.selected_node:
                new_geom = QgsGeometry.fromPointXY(clicked_point)
                self.node_bt_layer.startEditing()
                self.node_bt_layer.changeGeometry(self.selected_node.id(), new_geom)
                moving_node_id = self.selected_node.attribute("id")

                for line_feat in self.associated_bt_lines:
                    updateLineGeometry(self.line_bt_layer, line_feat, clicked_point, moving_node_id)

                for node_feat in self.associated_mt_nodes:
                    updateNodeGeometry(self.node_mt_layer, node_feat, clicked_point)
                    moving_node_id = node_feat.attribute("id")

                    for line_feat in self.associated_mt_lines:
                        updateLineGeometry(self.line_mt_layer, line_feat, clicked_point, moving_node_id)

                    for generator_feat in self.associated_generators:
                        self.updateGeneratorGeometry(generator_feat, clicked_point)

                    for load_feat in self.associated_loads:
                        self.updateLoadGeometry(load_feat, clicked_point)

                    for transformer_feat in self.associated_transformers:
                        self.updateTransformerGeometry(transformer_feat, clicked_point)

                    for et_feat in self.associated_ets:
                        self.updateEtGeometry(et_feat, clicked_point)

                    for switch_feat in self.associated_switches:
                        self.updateSwitchGeometry(switch_feat)

                    for seta_feat in self.associated_setas:
                        self.updateSetaGeometry(seta_feat, clicked_point)

    def canvasReleaseEvent(self, event):
        global estado_edicion
        global estado_seleccion_nodo

        print("canvasReleaseEvent")
        print(f"Botón Liberado: {event.button()}")

        if estado_edicion == "Moviendo_Nodo":
            estado_edicion = "Selec_None"
            estado_seleccion_nodo = "Selec_None"
            self.node_mt_layer.triggerRepaint()

    def createTempLineLayer(self):
        temp_line_layer = QgsVectorLayer("LineString?crs=epsg:22182", "TempLineLayer", "memory")
        temp_line_layer.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple({'color': 'red', 'width': '0.5'})))
        QgsProject.instance().addMapLayer(temp_line_layer, False)
        self.temp_line_layer = temp_line_layer
        self.temp_line_layer.startEditing()

    def redrawTempLineLayer(self, event):
        # Convertir la coordenada del evento al SRC seleccionado
        point = convert_point_to_crs(event.mapPoint())

        if not self.temp_line_layer.isEditable():
            self.temp_line_layer.startEditing()
        self.temp_line_layer.dataProvider().truncate()
        line_feature = QgsFeature()
        start_point = self.start_node.geometry().asPoint()
        end_point = point
        line_feature.setGeometry(QgsGeometry.fromPolyline([start_point, end_point]))
        self.temp_line_layer.dataProvider().addFeatures([line_feature])
        self.temp_line_layer.triggerRepaint()

    def removeTempLineLayer(self):
        QgsProject.instance().removeMapLayer(self.temp_line_layer)

    def updateGeneratorGeometry(self, generator_feat, new_point):
        generator_geom = QgsGeometry.fromPointXY(new_point)
        self.generator_layer.changeGeometry(generator_feat.id(), generator_geom)

    def updateLoadGeometry(self, load_feat, new_point):
        load_geom = QgsGeometry.fromPointXY(new_point)
        self.load_layer.changeGeometry(load_feat.id(), load_geom)

    def updateTransformerGeometry(self, transformer_feat, new_point):
        transformer_geom = QgsGeometry.fromPointXY(new_point)
        self.transformer_layer.changeGeometry(transformer_feat.id(), transformer_geom)

    def updateEtGeometry(self, et_feat, new_point):
        et_geom = QgsGeometry.fromPointXY(new_point)
        self.et_layer.changeGeometry(et_feat.id(), et_geom)

    def updateSetaGeometry(self, seta_feat, new_point):
        seta_geom = QgsGeometry.fromPointXY(new_point)
        self.seta_layer.changeGeometry(seta_feat.id(), seta_geom)

    def updateSwitchGeometry(self, switch_feat):
        terminal = switch_feat.attribute("terminal")
        start_line_id = switch_feat.attribute("line")

        start_line = find_line_by_id(self.line_mt_layer, start_line_id)
        line_geom = start_line.geometry()

        point = point_along_line(line_geom, terminal)

        switch_geom = QgsGeometry.fromPointXY(point)
        self.switch_layer.changeGeometry(switch_feat.id(), switch_geom)

    def startNode_Mt_Movement(self, node_id, estado_nivel_tension):
        self.associated_mt_lines = find_lines_connected_to_node(self.line_mt_layer, node_id)
        self.associated_bt_lines = []
        self.associated_generators = []
        self.associated_loads = []
        self.associated_transformers = []
        self.associated_ets = []
        self.associated_switches = []
        self.associated_setas = []

        self.associated_bt_nodes = find_nodes_connected_to_node(self.seta_layer, node_id)
        for node in self.associated_bt_nodes:
            node_id = node.attribute("id")
            self.associated_bt_lines.extend(find_lines_connected_to_node(self.line_bt_layer, node_id))

        self.associated_generators = find_elements_connected_to_node(self.generator_layer, node_id)
        self.associated_loads = find_elements_connected_to_node(self.load_layer, node_id)
        self.associated_switches = find_elements_connected_to_node(self.switch_layer, node_id)
        self.associated_transformers = find_elements_connected_to_node(self.transformer_layer, node_id)
        self.associated_ets = find_elements_connected_to_node(self.et_layer, node_id)
        self.associated_setas = find_elements_connected_to_node(self.seta_layer, node_id)

    def startNode_Bt_Movement(self, node_id, estado_nivel_tension):
        self.associated_mt_lines = []
        self.associated_bt_lines = find_lines_connected_to_node(self.line_bt_layer, node_id)
        self.associated_generators = []
        self.associated_loads = []
        self.associated_transformers = []
        self.associated_ets = []
        self.associated_switches = []
        self.associated_setas = []

        self.associated_mt_nodes = find_nodes_connected_to_node(self.seta_layer, node_id)
        for node in self.associated_mt_nodes:
            node_id = node.attribute("id")
            self.associated_mt_lines.extend(find_lines_connected_to_node(self.line_mt_layer, node_id))

        self.associated_generators = find_elements_connected_to_node(self.generator_layer, node_id)
        self.associated_loads = find_elements_connected_to_node(self.load_layer, node_id)
        self.associated_switches = find_elements_connected_to_node(self.switch_layer, node_id)
        self.associated_transformers = find_elements_connected_to_node(self.transformer_layer, node_id)
        self.associated_ets = find_elements_connected_to_node(self.et_layer, node_id)
        self.associated_setas = find_elements_connected_to_node(self.seta_layer, node_id)

def find_nearest_node_index(node_layer, point):
    search_radius = 0.0005
    node_features = [feat for feat in node_layer.getFeatures()]
    if not node_features:
        return None
    nearest_node = min(node_features, key=lambda feat: feat.geometry().distance(QgsGeometry.fromPointXY(point)))
    if nearest_node.geometry().distance(QgsGeometry.fromPointXY(point)) <= search_radius:
        return nearest_node
    return None

def find_nearest_line_index(line_layer, node_layer, point):
    search_radius = 0.0005
    line_features = [feat for feat in line_layer.getFeatures()]
    node_features = [feat for feat in node_layer.getFeatures()]
    if not line_features:
        return None, None, None
    nearest_line = min(line_features, key=lambda feat: feat.geometry().distance(QgsGeometry.fromPointXY(point)))
    terminal = 1 if nearest_line.geometry().closestVertex(QgsPointXY(point))[1] < nearest_line.geometry().length() * ubicacion_switch else 2
    point_on_line = nearest_line.geometry().interpolate(nearest_line.geometry().closestVertex(QgsPointXY(point))[1]).asPoint()
    if QgsGeometry.fromPointXY(point).distance(QgsGeometry.fromPointXY(point_on_line)) <= search_radius:
        return nearest_line, terminal, QgsGeometry.fromPointXY(point_on_line)
    return None, None, None

def find_line_by_id(line_layer, line_id):
    for feat in line_layer.getFeatures():
        if feat.attribute("id") == line_id:
            return feat
    return None

def updateLineGeometry(line_layer, line_feat, new_point, moving_node_id):
    line_geom = line_feat.geometry()
    node1_id = line_feat.attribute("start_node")
    node2_id = line_feat.attribute("end_node")

    if moving_node_id == node1_id:
        new_line_geom = QgsGeometry.fromPolyline([QgsPoint(new_point), line_geom.vertexAt(1)])
    elif moving_node_id == node2_id:
        new_line_geom = QgsGeometry.fromPolyline([line_geom.vertexAt(0), QgsPoint(new_point)])
    line_layer.changeGeometry(line_feat.id(), new_line_geom)

def updateNodeGeometry(node_layer, node_feat, new_point):
    node_geom = QgsGeometry.fromPointXY(new_point)
    node_layer.changeGeometry(node_feat.id(), node_geom)

def point_along_line(line_geom, terminal):
    point = line_geom.interpolate(ubicacion_switch * line_geom.length() if terminal == 1 else (1 - ubicacion_switch) * line_geom.length()).asPoint()
    return QgsPointXY(point)

def find_lines_connected_to_node(line_layer, node_id):
    connected_lines = []
    for line in line_layer.getFeatures():
        if line.attribute("start_node") == node_id or line.attribute("end_node") == node_id:
            connected_lines.append(line)
    return connected_lines

def find_nodes_connected_to_node(seta_layer, node_id):
    connected_nodes = []
    for seta in seta_layer.getFeatures():
        if seta.attribute("wdg1_node") == node_id or seta.attribute("wdg2_node") == node_id:
            connected_nodes.append(seta)
    return connected_nodes

def find_elements_connected_to_node(layer, node_id):
    connected_elements = []
    for element in layer.getFeatures():
        if element.attribute("start_node") == node_id:
            connected_elements.append(element)
    return connected_elements

def import_dss(node_layer, line_layer):
    # Crear una instancia del objeto DSS
    end_modelo_DSS = "ruta_a_tu_modelo.DSS"  # Cambia esto a la ruta real de tu archivo DSS
    dss = DSS(end_modelo_DSS)

    # Compilar el archivo DSS
    dss.compilar_DSS()

    # Iterar sobre las barras y líneas en el modelo DSS y agregar los nodos y líneas correspondientes en las capas QGIS
    dss_bus_names = dss.dssCircuit.AllBusNames
    dss_line_names = dss.dssLines.AllNames

    # Agregar nodos (barras)
    for bus_name in dss_bus_names:
        dss.activar_barra(bus_name)
        bus_vmagang = dss.obtener_VMagAng_barra()
        bus_geometry = QgsGeometry.fromPointXY(QgsPointXY(bus_vmagang[0], bus_vmagang[1]))  # Ajusta la geometría según tus necesidades

        node_feature = QgsFeature(node_layer.fields())
        node_feature.setAttribute("id", bus_name)
        node_feature.setGeometry(bus_geometry)
        node_layer.dataProvider().addFeatures([node_feature])

    # Agregar líneas
    for line_name in dss_line_names:
        dss.activar_elemento(f"Line.{line_name}")
        line_buses = dss.obtener_barras_elemento()
        line_geometry = QgsGeometry.fromPolyline([
            QgsPointXY(dss_bus_names.index(line_buses[0]), dss_bus_names.index(line_buses[1]))  # Ajusta la geometría según tus necesidades
        ])

        line_feature = QgsFeature(line_layer.fields())
        line_feature.setAttribute("id", line_name)
        line_feature.setAttribute("start_node", line_buses[0])
        line_feature.setAttribute("end_node", line_buses[1])
        line_feature.setGeometry(line_geometry)
        line_layer.dataProvider().addFeatures([line_feature])

    node_layer.triggerRepaint()
    line_layer.triggerRepaint()

canvas = iface.mapCanvas()

# Crear capas de nodos y líneas
node_mt_layer = QgsVectorLayer("Point?crs=EPSG:22182", "Nodos MT", "memory")
node_bt_layer = QgsVectorLayer("Point?crs=EPSG:22182", "Nodos BT", "memory")
line_mt_layer = QgsVectorLayer("LineString?crs=EPSG:22182", "Líneas MT", "memory")
line_bt_layer = QgsVectorLayer("LineString?crs=EPSG:22182", "Líneas BT", "memory")
generator_layer = QgsVectorLayer("Point?crs=EPSG:22182", "Generadores", "memory")
load_layer = QgsVectorLayer("Point?crs=EPSG:22182", "Cargas", "memory")
switch_layer = QgsVectorLayer("Point?crs=EPSG:22182", "Interruptores", "memory")
transformer_layer = QgsVectorLayer("Point?crs=EPSG:22182", "Transformadores", "memory")
et_layer = QgsVectorLayer("Point?crs=EPSG:22182", "Estaciones Transformadoras", "memory")
seta_layer = QgsVectorLayer("Point?crs=EPSG:22182", "Setas", "memory")

# Agregar las capas al proyecto
QgsProject.instance().addMapLayer(node_mt_layer)
QgsProject.instance().addMapLayer(node_bt_layer)
QgsProject.instance().addMapLayer(line_mt_layer)
QgsProject.instance().addMapLayer(line_bt_layer)
QgsProject.instance().addMapLayer(generator_layer)
QgsProject.instance().addMapLayer(load_layer)
QgsProject.instance().addMapLayer(switch_layer)
QgsProject.instance().addMapLayer(transformer_layer)
QgsProject.instance().addMapLayer(et_layer)
QgsProject.instance().addMapLayer(seta_layer)

# Crear una herramienta de mapa personalizada
map_tool = CustomMapTool(canvas, node_mt_layer, node_bt_layer, line_mt_layer, line_bt_layer, generator_layer, load_layer, switch_layer, transformer_layer, et_layer, seta_layer)

# Crear un panel de barra de herramientas personalizado
toolbar_panel = CustomToolbarPanel(map_tool, node_mt_layer, node_bt_layer, line_mt_layer, line_bt_layer, generator_layer, load_layer, switch_layer, transformer_layer, et_layer, seta_layer)
toolbar_panel.init_panel()

# Agregar el panel de barra de herramientas a la interfaz de QGIS
iface.addToolBar(toolbar_panel.toolbox)

# Establecer la herramienta de mapa personalizada como la herramienta de mapa activa
iface.mapCanvas().setMapTool(map_tool)
