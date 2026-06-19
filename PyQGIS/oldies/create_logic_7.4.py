import os
import uuid
from PyQt5.QtGui import QIcon, QCursor, QPixmap
from PyQt5.QtWidgets import QToolBar, QToolButton, QButtonGroup, QAction, QActionGroup, QFileDialog, QComboBox, QDialog, QVBoxLayout, QDialogButtonBox, QMenu, QFormLayout, QLineEdit, QMessageBox, QDialogButtonBox, QInputDialog
from qgis.utils import iface
from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtWidgets import QProgressBar, QApplication, QLabel
from qgis.core import Qgis, QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsPointXY, QgsPoint, QgsSingleSymbolRenderer, QgsLineSymbol, QgsRectangle, QgsGeometry, QgsPointXY
from qgis.gui import QgsMapTool
from math import radians, sin, cos, sqrt, atan2

import win32com.client
#import pathlib
# from pylab import *
#  import inspect  # Para obtener el path al script actual



# Variables de Estado Edición General:
estado_edicion = "Selec_None"  # puede ser cualquira de ["Selec_None", "Insertando", "Moviendo_Nodo"]
# Selec_None -> Estado Inicial
# Insertando -> Al hacer clic en un botón de la barra de herramientas
# Moviendo_Nodo -> clic en botón Selección -> clic sobre un nodo


estado_flujo_trabajo = None # puede ser cualquira de ["Seleccion", "Nodo", "Linea", "Interruptor", "Carga", "Generador"]

# Variable de edición en Media o Baja tensión:
estado_nivel_tension = "MT" # puede ser cualquira de ["MT", "BT"]

# Variables Estado Edición por Elemento:
estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
estado_seleccion_pvsystem = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
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

            self.dssLoads = self.dssCircuit.Loads
            self.dssRelays = self.dssCircuit.Relays
            self.dssVsources = self.dssCircuit.Vsources

            self.dssCapacitors = self.dssCircuit.Capacitors
            self.dssGenerators = self.dssCircuit.Generators
            self.dssPVSystems = self.dssCircuit.PVSystems
            self.dssSettings = self.dssCircuit.Settings



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
    
    def obtener_barra_elemento(self):
        barras = self.dssCktElement.BusNames
        barra1 = barras[0]
        return barra1

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
    def __init__(self, map_tool, node_mt_layer, node_bt_layer, line_mt_layer, line_bt_layer, generator_layer, pv_system_layer, load_layer, switch_layer, transformer_layer, et_layer, seta_layer, capacitor_layer):
        self.toolbox = None
        self.tool_buttons = []
        self.button_group = None
        self.map_tool = map_tool  # Referencia a la herramienta de mapa
        self.node_mt_layer = node_mt_layer  # Referencia a la capa de nodos
        self.node_bt_layer = node_bt_layer  # Referencia a la capa de nodos
        self.line_mt_layer = line_mt_layer  # Referencia a la capa de lineas
        self.line_bt_layer = line_bt_layer  # Referencia a la capa de lineas
        self.generator_layer = generator_layer  # Referencia a la capa de lineas
        self.pv_system_layer = pv_system_layer  # Referencia a la capa de sistemas fotovoltaicos
        self.load_layer = load_layer  # Referencia a la capa de cargas
        self.capacitor_layer = capacitor_layer  # Referencia a la capa de capacitores
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
        # script_dir = os.path.dirname(os.path.abspath(__file__))
        # script_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        iconos_dir = os.path.join(script_dir, "iconos")

        print(f"Path a los archivos de iconos: {iconos_dir}")

        # Lista de nombres de botones
        #button_names = ["Seleccion","Estacion_transformadora","Nodo","Linea", "Interruptor","Carga","Generador","Transformador","seta"]
        button_names = [
            ("Seleccion", "Seleccionar elementos en el mapa"),
            ("Estacion_transformadora", "Agregar una estación transformadora"),
            ("Nodo", "Agregar un nodo"),
            ("Linea", "Agregar una línea"),
            ("Interruptor", "Agregar un interruptor"),
            ("Carga", "Agregar una carga"),
            ("Capacitor", "Agregar un capacitor"),
            ("Generador", "Agregar un generador"),
            ("sistema_fotovoltaico", "Agregar un sistema fotovoltaico"),
            ("Transformador", "Agregar un transformador"),
            ("Seta", "Agregar una seta"),
            ("DSS-import", "Importar desde dss"),
            ("DSS-export", "Exportar hacia dss")
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

        elif  button_name.lower() == "dss-import":
            estado_flujo_trabajo = "dss-import"
            estado_edicion = "Selec_None"
            iface.mapCanvas().unsetCursor()
            import_dss(self.map_tool.node_mt_layer, self.map_tool.line_mt_layer, self.map_tool.transformer_layer, self.map_tool.generator_layer, self.map_tool.pv_system_layer , self.map_tool.et_layer, self.map_tool.load_layer, self.map_tool.switch_layer, self.map_tool.capacitor_layer)
    
        elif  button_name.lower() == "dss-export":
            estado_flujo_trabajo = "dss-export"
            estado_edicion = "Selec_None"
            iface.mapCanvas().unsetCursor()
            export_dss(self.map_tool.node_mt_layer, self.map_tool.line_mt_layer, self.map_tool.transformer_layer, self.map_tool.generator_layer, self.map_tool.pv_system_layer , self.map_tool.et_layer, self.map_tool.load_layer, self.map_tool.switch_layer, self.map_tool.capacitor_layer)

        else:
            estado_flujo_trabajo = button_name.lower()
            estado_edicion = "Insertando"   
            cursor = QCursor(QPixmap(cursor_icon_path), 0, 0)
            iface.mapCanvas().setCursor(cursor)

        print(f"Botón {button_name} clicado - Estado del flujo de trabajo: {estado_flujo_trabajo}")

# Esta clase maneja toda la lógica de edición gráfica de elementos de la red eléctrica
class CustomMapTool(QgsMapTool):
    def __init__(self, canvas, node_mt_layer, node_bt_layer, line_mt_layer, line_bt_layer, generator_layer, pv_system_layer, load_layer, switch_layer, transformer_layer, et_layer, seta_layer, capacitor_layer):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.active = False  # Agregar una variable para rastrear el estado de activación
        self.node_mt_layer = node_mt_layer  # Referencia a la capa de nodos
        self.node_bt_layer = node_bt_layer  # Referencia a la capa de nodos
        self.line_mt_layer = line_mt_layer  # Referencia a la capa de lineas
        self.line_bt_layer = line_bt_layer  # Referencia a la capa de lineas
        self.generator_layer = generator_layer  # Referencia a la capa de generadores
        self.pv_system_layer = pv_system_layer  # Referencia a la capa de sistemas fotovoltaicos
        self.load_layer = load_layer  # Referencia a la capa de cargas
        self.capacitor_layer = capacitor_layer  # Referencia a la capa de capacitores
        self.switch_layer = switch_layer  # Referencia a la capa de interruptores
        self.transformer_layer = transformer_layer  # Referencia a la capa de transformadores
        self.et_layer = et_layer  # Referencia a la capa de transformadores
        self.seta_layer = seta_layer # Referencia a la capa de setas
        self.node_feature = None  # Inicializar la variable fuera del bloque condicional
        self.selected_node = None
        self.selected_node_pair = None
        self.start_node = None
        self.end_node = None
        self.linked_line = None  # línea para asociar a un elemento de control
        self.linked_node = None  # Terminal asociado

        self.associated_mt_lines = []  # Se utilizan tanto para el movimiento de un nodo_mt como un nodo_bt 
        self.associated_bt_lines = []  # Se utilizan tanto para el movimiento de un nodo_mt como un nodo_bt 
        self.associated_mt_nodes = [] # En realidad va a ser solo uno, es el nodo_mt binculado por una seta
        self.associated_bt_nodes = [] # En realidad va a ser solo uno, es el nodo_bt binculado por una seta
        self.associated_generators = [] #La restricción de ingreso no debe permitir mas de 1 elemento
        self.associated_pvsystems = [] #La restricción de ingreso no debe permitir mas de 1 elemento

        self.associated_loads = [] #La restricción de ingreso no debe permitir mas de 1 elemento
        self.associated_capacitors = [] #La restricción de ingreso no debe permitir mas de 1 elemento
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
        global estado_seleccion_pvsystem
        global estado_seleccion_carga
        global estado_seleccion_capacitor
        global estado_seleccion_interruptor
        global estado_seleccion_transformador
        global estado_seleccion_seta
        global estado_seleccion_et
        global estado_edicion

        #print(f"Botón Presionado: {event.button()}")

        if estado_nivel_tension == "MT":

            if event.button() == Qt.RightButton:
                print("Right button clicked")

                if estado_flujo_trabajo == "seleccion":
                    self.selected_node = find_nearest_node_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                    if self.selected_node:
                        print(f"Selected node ID: {self.selected_node.id()}")
                        self.show_context_menu(event, "node")
                    else:
                        self.selected_line = find_nearest_line_for_editing(self.line_mt_layer, QgsPointXY(event.mapPoint()))
                        if self.selected_line:
                            print(f"Selected line ID: {self.selected_line.id()}")
                            self.show_context_menu(event, "line")

                
                elif estado_flujo_trabajo == "linea":
                    if estado_seleccion_linea == "N1_Selec":
                        estado_seleccion_linea = "Selec_None"
                        self.removeTempLineLayer()
                        self.line_mt_layer.triggerRepaint()        



            elif event.button() == Qt.LeftButton:
                #print("Clic en el mapa en la posición:", event.mapPoint())
                print("Estado del flujo de trabajo:", estado_flujo_trabajo)
                #print("Botón", event.button())
                #print("Boton izq", Qt.LeftButton)

                if estado_flujo_trabajo == "seleccion":
                    estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                    estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_pvsystem = "Selec_None"
                    estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
                    estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_seta = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_et = "Selec_None"

                    print("Seleccionando")
                    self.selected_node = find_nearest_node_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                    
                    if self.selected_node:
                        estado_seleccion_nodo = "N_Selec"
                        print(f"Nodo seleccionado: {self.selected_node.id()}")
                        self.startNodes_Mt_Movement(self.selected_node.attribute("id"), estado_nivel_tension)
                        # Seleccionar el nodo encontrado
                        self.node_mt_layer.selectByIds([self.selected_node.id()])
                        self.node_mt_layer.triggerRepaint()
                        estado_edicion = "Moviendo_Nodo"



                elif estado_flujo_trabajo == "nodo":
                    estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                    #estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_pvsystem = "Selec_None"
                    estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
                    estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando nodo")
                    # Generar un ID único para el nodo
                    unique_node_id = str(uuid.uuid4())
                    # Asegurarse de que el nombre del campo sea exactamente "id"
                    field_name = "id"
                    # Verificar si el campo existe en la capa de nodos
                    if field_name in self.node_mt_layer.fields().names():
                        node_feature = QgsFeature(self.node_mt_layer.fields())
                        node_feature.setAttribute(field_name, unique_node_id)
                        node_geometry = QgsGeometry.fromPointXY(QgsPointXY(event.mapPoint()))
                        node_feature.setGeometry(node_geometry)
                        # Añadir la característica a la capa de nodos
                        success, new_feature_ids = self.node_mt_layer.dataProvider().addFeatures([node_feature])
                        if success:
                            print(f"Nodo agregado con unique_node_id: {unique_node_id}")
                            # print(f"new_feature_ids: {new_feature_ids}")
                            print(f"Feature.id: {new_feature_ids[0].id()}")
                            self.node_mt_layer.triggerRepaint()
                            # vuelve a crear el indice espacial para agregar el nodo recien insertado
                        else:
                            print("Error al agregar el nodo.")
                    else:
                        print(f"Error: El campo '{field_name}' no existe en la capa de nodos.")

                elif estado_flujo_trabajo == "linea":
                    #estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                    estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_pvsystem = "Selec_None"
                    estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
                    estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando linea")
                    if estado_seleccion_linea == "Selec_None": # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                        #self.start_node = find_nearest_node(self.node_layer, QgsPoint(event.mapPoint()))
                        self.start_node = find_nearest_nodes_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                        if self.start_node:
                            estado_seleccion_linea = "N1_Selec"
                            self.createTempLineLayer()
                            print(f"Nodo de inicio ID: {self.start_node.id()}")
                        else:
                            print("Haga clic sobre el primer nodo")

                    elif estado_seleccion_linea == "N1_Selec":
                        #self.end_node = find_nearest_node(self.node_layer, QgsPoint(event.mapPoint()))
                        self.end_node = find_nearest_nodes_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                        if self.end_node:
                            #estado_seleccion_linea = "Selec_None"                                                
                            #print(f"Nodo de fin ID: {self.end_node.id()}")
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
                                    # print(f"new_feature_ids: {new_feature_ids}")
                                    print(f"Feature.id: {new_feature_ids[0].id()}")
                                    self.line_mt_layer.triggerRepaint()
                                else:
                                    print("Error al agregar la línea.")
                            else:
                                print("Error: Campos faltantes en la capa de líneas.")
                        else:
                            print("Haga clic sobre el segundo nodo")


                elif estado_flujo_trabajo == "generador":
                    estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                    estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    #estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_pvsystem = "Selec_None"
                    estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
                    estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando generador")
                    if estado_seleccion_generador == "Selec_None":
                        self.start_node = find_nearest_nodes_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                        if self.start_node:
                            #print(f"Nodo ID: {self.start_node.id()}")
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
                                    print(f"Feature.id: {new_feature_ids[0].id()}")
                                    self.generator_layer.triggerRepaint()
                                else:
                                    print("Error al agregar el generador.")
                            else:
                                print("Error: Campos faltantes en la capa de generadores.")
                        else:
                            print("Haga clic sobre un nodo")


                elif estado_flujo_trabajo == "sistema_fotovoltaico":
                    estado_seleccion_linea = "Selec_None"
                    estado_seleccion_nodo = "Selec_None"
                    estado_seleccion_generador = "Selec_None"
                    # estado_seleccion_pvsystem = "Selec_None"
                    estado_seleccion_carga = "Selec_None"
                    estado_seleccion_capacitor = "Selec_None"
                    estado_seleccion_interruptor = "Selec_None"
                    estado_seleccion_transformador = "Selec_None"
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"                    

                    print("agregando sistema fotovoltaico")
                    if estado_seleccion_pvsystem == "Selec_None":
                        self.start_node = find_nearest_nodes_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                        if self.start_node:
                            start_point = QgsPointXY(self.start_node.geometry().asPoint())
                            unique_pvsystem_id = str(uuid.uuid4())
                            field_names = ["id", "start_node"]
                            if all(field_name in self.pv_system_layer.fields().names() for field_name in field_names):
                                pvsystem_feature = QgsFeature(self.pv_system_layer.fields())
                                pvsystem_feature.setAttribute("id", unique_pvsystem_id)
                                pvsystem_feature.setAttribute("start_node", self.start_node.attribute("id"))
                                pvsystem_geometry = QgsGeometry.fromPointXY(start_point)
                                pvsystem_feature.setGeometry(pvsystem_geometry)
                                success, new_feature_ids = self.pv_system_layer.dataProvider().addFeatures([pvsystem_feature])
                                if success:
                                    estado_seleccion_pvsystem = "Selec_None"
                                    print(f"Sistema fotovoltaico agregado con ID: {unique_pvsystem_id}")
                                    print(f"Feature.id: {new_feature_ids[0].id()}")
                                    self.pv_system_layer.triggerRepaint()
                                else:
                                    print("Error al agregar el sistema fotovoltaico.")
                            else:
                                print("Error: Campos faltantes en la capa de sistemas fotovoltaicos.")
                        else:
                            print("Haga clic sobre un nodo")


                elif estado_flujo_trabajo == "carga":
                    estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                    estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_pvsystem = "Selec_None"
                    #estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
                    estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando carga")
                    if estado_seleccion_carga == "Selec_None":
                        self.start_node = find_nearest_nodes_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                        if self.start_node:
                            #print(f"Nodo ID: {self.start_node.id()}")
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
                                    print(f"Feature.id: {new_feature_ids[0].id()}")
                                    self.load_layer.triggerRepaint()
                                else:
                                    print("Error al agregar la carga.")
                            else:
                                print("Error: Campos faltantes en la capa de cargas.")
                        else:
                            print("Haga clic sobre un nodo")


                elif estado_flujo_trabajo == "capacitor":
                    estado_seleccion_linea = "Selec_None"
                    estado_seleccion_nodo = "Selec_None"
                    estado_seleccion_generador = "Selec_None"
                    estado_seleccion_pvsystem = "Selec_None"
                    estado_seleccion_carga = "Selec_None"
                    # estado_seleccion_capacitor = "Selec_None"
                    estado_seleccion_interruptor = "Selec_None"
                    estado_seleccion_transformador = "Selec_None"
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando capacitor")
                    if estado_seleccion_capacitor == "Selec_None":
                        self.start_node = find_nearest_nodes_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                        if self.start_node:
                            start_point = QgsPointXY(self.start_node.geometry().asPoint())
                            unique_capacitor_id = str(uuid.uuid4())
                            field_names = ["id", "start_node"]
                            if all(field_name in self.capacitor_layer.fields().names() for field_name in field_names):
                                capacitor_feature = QgsFeature(self.capacitor_layer.fields())
                                capacitor_feature.setAttribute("id", unique_capacitor_id)
                                capacitor_feature.setAttribute("start_node", self.start_node.attribute("id"))
                                capacitor_geometry = QgsGeometry.fromPointXY(start_point)
                                capacitor_feature.setGeometry(capacitor_geometry)
                                success, new_feature_ids = self.capacitor_layer.dataProvider().addFeatures([capacitor_feature])
                                if success:
                                    estado_seleccion_capacitor = "Selec_None"
                                    print(f"Capacitor agregado con ID: {unique_capacitor_id}")
                                    print(f"Feature.id: {new_feature_ids[0].id()}")
                                    self.capacitor_layer.triggerRepaint()
                                else:
                                    print("Error al agregar el capacitor.")
                            else:
                                print("Error: Campos faltantes en la capa de capacitores.")
                        else:
                            print("Haga clic sobre un nodo")


                elif estado_flujo_trabajo == "interruptor":
                    estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                    estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_pvsystem = "Selec_None"
                    estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_capacitor = "Selec_None"
                    #estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
                    estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando interruptor")
                    if estado_seleccion_interruptor == "Selec_None":
                        self.linked_line, terminal, point_on_line  = find_nearest_line_index(self.line_mt_layer, self.node_mt_layer, QgsPointXY(event.mapPoint()))
                        if self.linked_line:
                            #print(f"Nodo ID: {self.start_node.id()}")
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
                                    print(f"Feature.id: {new_feature_ids[0].id()}")
                                    self.switch_layer.triggerRepaint()
                                else:
                                    print("Error al agregar el interruptor.")
                            else:
                                print("Error: Campos faltantes en la capa de interruptores.")
                        else:
                            print("Haga clic sobre una línea")


                elif estado_flujo_trabajo == "transformador":
                    estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                    estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_pvsystem = "Selec_None"
                    estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
                    #estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando transformador")
                    if estado_seleccion_transformador == "Selec_None":
                        self.start_node = find_nearest_node_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                        if self.start_node:

                            start_point = QgsPointXY(self.start_node.geometry().asPoint())

                            # *********Primero debo crear el nodo de media tensión<<<<<******************
                            unique_node_id = str(uuid.uuid4())
                            # Asegurarse de que el nombre del campo sea exactamente "id"
                            field_name = "id"
                            # Verificar si el campo existe en la capa de nodos
                            if field_name in self.node_mt_layer.fields().names():
                                node_feature = QgsFeature(self.node_mt_layer.fields())
                                node_feature.setAttribute(field_name, unique_node_id)
                                node_geometry = QgsGeometry.fromPointXY(start_point)
                                node_feature.setGeometry(node_geometry)
                                # Añadir la característica a la capa de nodos
                                success, new_feature_ids = self.node_mt_layer.dataProvider().addFeatures([node_feature])
                                if success:
                                    print(f"Nodo MT agregado con unique_node_id: {unique_node_id}")
                                    # print(f"new_feature_ids: {new_feature_ids}")
                                    print(f"Feature.id: {new_feature_ids[0].id()}")
                                    self.node_mt_layer.triggerRepaint()
                                    # vuelve a crear el indice espacial para agregar el nodo recien insertado
                                else:
                                    print("Error al agregar el nodo.")
                            else:
                                print(f"Error: El campo '{field_name}' no existe en la capa de nodos.")
                            # *********>>>>>>Primero debo agregar el nodo de baja tensión******************

                            #print(f"Nodo ID: {self.start_node.id()}")
                            #start_point = QgsPointXY(self.start_node.geometry().asPoint())
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
                                    print(f"Feature.id: {new_feature_ids[0].id()}")
                                    self.transformer_layer.triggerRepaint()
                                else:
                                    print("Error al agregar la transformador.")
                            else:
                                print("Error: Campos faltantes en la capa de transformadores.")

                        else:
                            print("Haga clic sobre un nodo")


                elif estado_flujo_trabajo == "estacion_transformadora":
                    estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                    estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_pvsystem = "Selec_None"
                    estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
                    estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    #estado_seleccion_et = "Selec_None"

                    print("agregando estacion transformadora")
                    
                    # *********Primero debo crear el nodo SourceBus ******************
                    unique_node_id = str(uuid.uuid4())
                    field_name = "id"
                    if field_name in self.node_mt_layer.fields().names():
                        node_feature = QgsFeature(self.node_mt_layer.fields())
                        node_feature.setAttribute(field_name, unique_node_id)
                        node_geometry = QgsGeometry.fromPointXY(QgsPointXY(event.mapPoint()))
                        node_feature.setGeometry(node_geometry)
                        success, new_feature_ids = self.node_mt_layer.dataProvider().addFeatures([node_feature])
                        if success:
                            print(f"Nodo MT agregado con unique_node_id: {unique_node_id}")
                            print(f"Feature.id: {new_feature_ids[0].id()}")
                            self.node_mt_layer.triggerRepaint()
                        else:
                            print("Error al agregar el nodo.")
                    else:
                        print(f"Error: El campo '{field_name}' no existe en la capa de nodos.")

                    # *********Luego debo crear el id para la estacion transformadora******************

                    unique_et_id = str(uuid.uuid4())
                    field_names = ["id", "start_node"]
                    if all(field_name in self.et_layer.fields().names() for field_name in field_names):
                        et_feature = QgsFeature(self.et_layer.fields())
                        et_feature.setAttribute("id", unique_et_id)
                        et_feature.setAttribute("start_node", unique_node_id)                            
                        et_geometry = QgsGeometry.fromPointXY(QgsPointXY(event.mapPoint()))
                        et_feature.setGeometry(et_geometry)
                        success, new_feature_ids = self.et_layer.dataProvider().addFeatures([et_feature])
                        if success:
                            #estado_seleccion_et = "Selec_None"
                            print(f"estacion transformadora agregada con ID: {unique_et_id}")
                            print(f"Feature.id: {new_feature_ids[0].id()}")
                            self.et_layer.triggerRepaint()
                        else:
                            print("Error al agregar la estacion transformadora.")
                    else:
                        print("Error: Campos faltantes en la capa de estacion_transformadora.")


                elif estado_flujo_trabajo == "seta":
                    estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                    estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_pvsystem = "Selec_None"
                    estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
                    estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    #estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando seta")
                    if estado_seleccion_seta == "Selec_None":
                        self.start_node = find_nearest_node_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                        if self.start_node:

                            start_point = QgsPointXY(self.start_node.geometry().asPoint())

                            # *********Primero debo crear el nodo de baja tensión<<<<<******************
                            unique_node_id = str(uuid.uuid4())
                            # Asegurarse de que el nombre del campo sea exactamente "id"
                            field_name = "id"
                            # Verificar si el campo existe en la capa de nodos
                            if field_name in self.node_bt_layer.fields().names():
                                node_feature = QgsFeature(self.node_bt_layer.fields())
                                node_feature.setAttribute(field_name, unique_node_id)
                                node_geometry = QgsGeometry.fromPointXY(start_point)
                                node_feature.setGeometry(node_geometry)
                                # Añadir la característica a la capa de nodos
                                success, new_feature_ids = self.node_bt_layer.dataProvider().addFeatures([node_feature])
                                if success:
                                    print(f"Nodo BT agregado con unique_node_id: {unique_node_id}")
                                    # print(f"new_feature_ids: {new_feature_ids}")
                                    print(f"Feature.id: {new_feature_ids[0].id()}")
                                    self.node_bt_layer.triggerRepaint()
                                    # vuelve a crear el indice espacial para agregar el nodo recien insertado
                                else:
                                    print("Error al agregar el nodo.")
                            else:
                                print(f"Error: El campo '{field_name}' no existe en la capa de nodos.")
                            # *********>>>>>>Primero debo agregar el nodo de baja tensión******************

                            #print(f"Nodo ID: {self.start_node.id()}")
                            #start_point = QgsPointXY(self.start_node.geometry().asPoint())
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
                                    print(f"Feature.id: {new_feature_ids[0].id()}")
                                    self.seta_layer.triggerRepaint()
                                else:
                                    print("Error al agregar la seta.")
                            else:
                                print("Error: Campos faltantes en la capa de setas.")

                        else:
                            print("Haga clic sobre un nodo")



        elif estado_nivel_tension == "BT":
            #print("Hacer lo mismo con BT")

            if event.button() == Qt.RightButton:
                if estado_flujo_trabajo == "linea":
                    if estado_seleccion_linea == "N1_Selec":
                        estado_seleccion_linea = "Selec_None"
                        self.removeTempLineLayer()
                        self.line_bt_layer.triggerRepaint()


            # Manejar el evento de clic del mouse
            elif event.button() == Qt.LeftButton:
                #print("Clic en el mapa en la posición:", event.mapPoint())
                print("Estado del flujo de trabajo:", estado_flujo_trabajo)
                #print("Botón", event.button())
                #print("Boton izq", Qt.LeftButton)

                if estado_flujo_trabajo == "seleccion":
                    estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                    estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_pvsystem = "Selec_None"
                    estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
                    estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_seta = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_et = "Selec_None"

                    print("Seleccionando")
                    self.selected_node = find_nearest_node_index(self.node_bt_layer, QgsPointXY(event.mapPoint()))
                    
                    if self.selected_node:
                        estado_seleccion_nodo = "N_Selec"
                        print(f"Nodo seleccionado: {self.selected_node.id()}")
                        self.startNode_Bt_Movement(self.selected_node.attribute("id"), estado_nivel_tension)
                        # Seleccionar el nodo encontrado
                        self.node_bt_layer.selectByIds([self.selected_node.id()])
                        self.node_bt_layer.triggerRepaint()
                        estado_edicion = "Moviendo_Nodo"


                elif estado_flujo_trabajo == "nodo":
                    estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                    #estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_pvsystem = "Selec_None"
                    estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
                    estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando nodo")
                    # Generar un ID único para el nodo
                    unique_node_id = str(uuid.uuid4())
                    # Asegurarse de que el nombre del campo sea exactamente "id"
                    field_name = "id"
                    # Verificar si el campo existe en la capa de nodos
                    if field_name in self.node_bt_layer.fields().names():
                        node_feature = QgsFeature(self.node_bt_layer.fields())
                        node_feature.setAttribute(field_name, unique_node_id)
                        node_geometry = QgsGeometry.fromPointXY(QgsPointXY(event.mapPoint()))
                        node_feature.setGeometry(node_geometry)
                        # Añadir la característica a la capa de nodos
                        success, new_feature_ids = self.node_bt_layer.dataProvider().addFeatures([node_feature])
                        if success:
                            print(f"Nodo agregado con unique_node_id: {unique_node_id}")
                            # print(f"new_feature_ids: {new_feature_ids}")
                            print(f"Feature.id: {new_feature_ids[0].id()}")
                            self.node_bt_layer.triggerRepaint()
                            # vuelve a crear el indice espacial para agregar el nodo recien insertado
                        else:
                            print("Error al agregar el nodo.")
                    else:
                        print(f"Error: El campo '{field_name}' no existe en la capa de nodos.")

                elif estado_flujo_trabajo == "linea":
                    #estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                    estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_pvsystem = "Selec_None"
                    estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
                    estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                    estado_seleccion_seta = "Selec_None"
                    estado_seleccion_et = "Selec_None"

                    print("agregando linea")
                    if estado_seleccion_linea == "Selec_None": # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                        #self.start_node = find_nearest_node(self.node_layer, QgsPoint(event.mapPoint()))
                        self.start_node = find_nearest_node_index(self.node_bt_layer, QgsPointXY(event.mapPoint()))
                        if self.start_node:
                            estado_seleccion_linea = "N1_Selec"
                            self.createTempLineLayer()
                            print(f"Nodo de inicio ID: {self.start_node.id()}")
                        else:
                            print("Haga clic sobre el primer nodo")

                    elif estado_seleccion_linea == "N1_Selec":
                        #self.end_node = find_nearest_node(self.node_layer, QgsPoint(event.mapPoint()))
                        self.end_node = find_nearest_node_index(self.node_bt_layer, QgsPointXY(event.mapPoint()))
                        if self.end_node:
                            #estado_seleccion_linea = "Selec_None"                                                
                            #print(f"Nodo de fin ID: {self.end_node.id()}")
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
                                    # print(f"new_feature_ids: {new_feature_ids}")
                                    print(f"Feature.id: {new_feature_ids[0].id()}")
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
        global estado_seleccion_pvsystem
        global estado_seleccion_carga
        global estado_seleccion_capacitor
        global estado_edicion

        #print(f"Botón Presionado: {event.button()}")
        # NOTA--> Este evento "canvasMoveEvent" no trae la información del botón presionado
        # Por lo tanto no podemos usar esto para la lógica

        clicked_point = event.mapPoint()

        if estado_nivel_tension == "MT":

            if estado_flujo_trabajo == "linea":
                if estado_seleccion_linea == "N1_Selec":
                    self.redrawTempLineLayer(event)
                nearby_nodes = find_nearest_node_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                if nearby_nodes:
                    print(f"Nodo cercano: {nearby_nodes.id()}")
                    # Seleccionar el nodo encontrado
                    self.node_mt_layer.selectByIds([nearby_nodes.id()])
                    self.node_mt_layer.triggerRepaint()
                else:
                    #print("No se encontró un nodo cercano")
                    self.node_mt_layer.removeSelection()


            elif estado_flujo_trabajo == "generador":
                nearby_nodes = find_nearest_node_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                if nearby_nodes:
                    #print(f"Nodo cercano: {nearby_nodes.id()}")
                    # Seleccionar el nodo encontrado
                    self.node_mt_layer.selectByIds([nearby_nodes.id()])
                    self.node_mt_layer.triggerRepaint()
                else:
                    #print("No se encontró un nodo cercano")
                    self.node_mt_layer.removeSelection()
    

            elif estado_flujo_trabajo == "sistema_fotovoltaico":
                nearby_nodes = find_nearest_node_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                if nearby_nodes:
                    #print(f"Nodo cercano: {nearby_nodes.id()}")
                    # Seleccionar el nodo encontrado
                    self.node_mt_layer.selectByIds([nearby_nodes.id()])
                    self.node_mt_layer.triggerRepaint()
                else:
                    #print("No se encontró un nodo cercano")
                    self.node_mt_layer.removeSelection()


            elif estado_flujo_trabajo == "carga":
                nearby_node = find_nearest_node_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                if nearby_node:
                    #print(f"Nodo cercano: {nearby_nodes.id()}")
                    # Seleccionar el nodo encontrado
                    self.node_mt_layer.selectByIds([nearby_node.id()])
                    self.node_mt_layer.triggerRepaint()
                else:
                    #print("No se encontró un nodo cercano")
                    self.node_mt_layer.removeSelection()

 
            elif estado_flujo_trabajo == "capacitor":
                nearby_node = find_nearest_node_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                if nearby_node:
                    self.node_mt_layer.selectByIds([nearby_node.id()])
                    self.node_mt_layer.triggerRepaint()
                else:
                    self.node_mt_layer.removeSelection()


            elif estado_flujo_trabajo == "interruptor":
                nearby_line, terminal, point_on_line = find_nearest_line_index(self.line_mt_layer, self.node_mt_layer, QgsPointXY(event.mapPoint()))
                
                if nearby_line:
                    print(f"Línea cercana: {nearby_line.id()}, Terminal: {terminal}")
                    self.line_mt_layer.selectByIds([nearby_line.id()])
                    self.line_mt_layer.triggerRepaint()
                else:
                    print("No se encontró una línea cercana")
                    self.line_mt_layer.removeSelection()  #FIJARSE SI SE ESTA ACCEDIENDO CORRECTAMENTE A LA CAPA


            elif estado_flujo_trabajo == "transformador":
                nearby_node = find_nearest_node_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                if nearby_node:
                    #print(f"Nodo cercano: {nearby_nodes.id()}")
                    # Seleccionar el nodo encontrado
                    self.node_mt_layer.selectByIds([nearby_node.id()])
                    self.node_mt_layer.triggerRepaint()
                else:
                    #print("No se encontró un nodo cercano")
                    self.node_mt_layer.removeSelection()

            elif estado_flujo_trabajo == "seta":
                nearby_node = find_nearest_node_index(self.node_mt_layer, QgsPointXY(event.mapPoint()))
                if nearby_node:
                    #print(f"Nodo cercano: {nearby_nodes.id()}")
                    # Seleccionar el nodo encontrado
                    self.node_mt_layer.selectByIds([nearby_node.id()])
                    self.node_mt_layer.triggerRepaint()
                else:
                    #print("No se encontró un nodo cercano")
                    self.node_mt_layer.removeSelection()


            if estado_edicion == "Moviendo_Nodo" and self.selected_node:

                for generator_feat in self.associated_generators:
                    self.updateGeneratorGeometry(generator_feat, QgsPointXY(clicked_point))

                for pvsystem_feat in self.associated_pvsystems:
                    self.updatePvsystemGeometry(pvsystem_feat, QgsPointXY(clicked_point))

                for load_feat in self.associated_loads:
                    self.updateLoadGeometry(load_feat, QgsPointXY(clicked_point))

                for capacitor_feat in self.associated_capacitors:
                    self.updateCapacitorGeometry(capacitor_feat, QgsPointXY(clicked_point))

                for transformer_feat in self.associated_transformers:
                    self.updateTransformerGeometry(transformer_feat, QgsPointXY(clicked_point))

                for et_feat in self.associated_ets:
                    self.updateEtGeometry(et_feat, QgsPointXY(clicked_point))

                for seta_feat in self.associated_setas:
                    self.updateSetaGeometry(seta_feat, QgsPointXY(clicked_point))

                for node_feat in self.associated_bt_nodes:
                    updateNodeGeometry(self.node_bt_layer, node_feat, clicked_point)
                    moving_node_id = node_feat.attribute("id")

                    for line_feat in self.associated_bt_lines:
                        updateLineGeometry(self.line_bt_layer, line_feat, QgsPointXY(clicked_point), moving_node_id)

                for node_feat in self.associated_mt_nodes:
                    updateNodeGeometry(self.node_mt_layer, node_feat, clicked_point)
                    moving_node_id = node_feat.attribute("id")

                for line_feat in self.associated_mt_lines:
                    self.updateLine_mtGeometry(line_feat)

                for switch_feat in self.associated_switches:
                    self.updateSwitchGeometry(switch_feat)


        elif estado_nivel_tension == "BT":
            #print("Hacer lo mismo con BT")

            if estado_flujo_trabajo == "linea":
                if estado_seleccion_linea == "N1_Selec":
                    self.redrawTempLineLayer(event)
                nearby_nodes = find_nearest_node_index(self.node_bt_layer, QgsPointXY(event.mapPoint()))
                if nearby_nodes:
                    print(f"Nodo cercano: {nearby_nodes.id()}")
                    # Seleccionar el nodo encontrado
                    self.node_bt_layer.selectByIds([nearby_nodes.id()])
                    self.node_bt_layer.triggerRepaint()
                else:
                    #print("No se encontró un nodo cercano")
                    node_bt_layer.removeSelection()


            if estado_edicion == "Moviendo_Nodo" and self.selected_node:
                # Actualizar la geometría del nodo seleccionado con la nueva ubicación
                #print(f"canvasMoveEvent:")
                new_geom = QgsGeometry.fromPointXY(QgsPointXY(clicked_point))
                self.node_bt_layer.startEditing()
                self.node_bt_layer.changeGeometry(self.selected_node.id(), new_geom)
                moving_node_id = self.selected_node.attribute("id")

                for line_feat in self.associated_bt_lines:
                    updateLineGeometry(self.line_bt_layer, line_feat, QgsPointXY(clicked_point), moving_node_id)

                for node_feat in self.associated_mt_nodes:
                    updateNodeGeometry(self.node_mt_layer, node_feat, clicked_point)
                    moving_node_id = node_feat.attribute("id")

                    for line_feat in self.associated_mt_lines:
                        updateLineGeometry(self.line_mt_layer, line_feat, QgsPointXY(clicked_point), moving_node_id)

                    for generator_feat in self.associated_generators:
                        self.updateGeneratorGeometry(generator_feat, QgsPointXY(clicked_point))

                    for pvsystem_feat in self.associated_pvsystems:
                        self.updatePvsystemGeometry(pvsystem_feat, QgsPointXY(clicked_point))

                    for load_feat in self.associated_loads:
                        self.updateLoadGeometry(load_feat, QgsPointXY(clicked_point))

                    for capacitor_feat in self.associated_capacitors:
                        self.updateCapacitorGeometry(capacitor_feat, QgsPointXY(clicked_point))

                    for transformer_feat in self.associated_transformers:
                        self.updateTransformerGeometry(transformer_feat, QgsPointXY(clicked_point))

                    for et_feat in self.associated_ets:
                        self.updateEtGeometry(et_feat, QgsPointXY(clicked_point))

                    for switch_feat in self.associated_switches:
                        self.updateSwitchGeometry(switch_feat)

                    for seta_feat in self.associated_setas:
                        self.updateSetaGeometry(seta_feat, QgsPointXY(clicked_point))



    def canvasReleaseEvent(self, event):
        #print(f"canvasReleaseEvent:")
        global estado_edicion
        global estado_seleccion_nodo

        print("canvasReleaseEvent")
        print(f"Botón Liberado: {event.button()}")

        self.node_mt_layer.removeSelection()
        self.node_bt_layer.removeSelection()
        self.line_mt_layer.removeSelection()
        self.line_bt_layer.removeSelection()


        if estado_edicion == "Moviendo_Nodo":
            estado_edicion = "Selec_None"
            estado_seleccion_nodo = "Selec_None"
            # self.node_mt_layer.removeSelection()
            # elf.node_bt_layer.removeSelection()
            # Finalizar la edición y guardar los cambios
            self.node_mt_layer.commitChanges()
            self.node_bt_layer.commitChanges()
            self.line_mt_layer.commitChanges()
            self.line_bt_layer.commitChanges()
            self.generator_layer.commitChanges()
            self.pv_system_layer.commitChanges()
            self.load_layer.commitChanges()
            self.capacitor_layer.commitChanges()
            self.switch_layer.commitChanges()
            self.transformer_layer.commitChanges()
            self.seta_layer.commitChanges()
            self.et_layer.commitChanges()

            self.selected_node = None
            self.associated_mt_lines = []
            self.associated_bt_lines = []
            self.associated_mt_nodes = [] 
            self.associated_bt_nodes = []
            self.associated_generators = []
            self.associated_pvsystems = []
            self.associated_loads = []
            self.associated_capacitors = []
            self.associated_switches = []
            self.associated_transformers = []
            self.associated_ets = []
            self.associated_setas = []



    def startNodes_Mt_Movement(self, node_id, estado_nivel_tension):
        print(f"startNodes_Mt_Movement:")
        
        self.associated_mt_nodes = []  # Esto es para mover los nodos de transformadores
        self.associated_mt_lines = []
        self.associated_loads = []
        self.associated_capacitors = []
        self.associated_switches = []

        first_node = find_node_by_uuid(self.node_mt_layer, node_id)
        if first_node:
            self.associated_mt_nodes.append(first_node)

        #self.associated_mt_lines = [feat for feat in self.line_mt_layer.getFeatures() if feat['start_node'] == node_id or feat['end_node'] == node_id]
        #print(f"Cantidad lineas en nodo 1: {len(self.associated_mt_lines)}")

        self.associated_generators = [feat for feat in self.generator_layer.getFeatures() if feat['start_node'] == node_id]
        self.associated_pvsystems = [feat for feat in self.pv_system_layer.getFeatures() if feat['start_node'] == node_id]
        #self.associated_loads = [feat for feat in self.load_layer.getFeatures() if feat['start_node'] == node_id]
        self.associated_transformers = [feat for feat in self.transformer_layer.getFeatures() if feat['wdg1_node'] == node_id]
        self.associated_ets = [feat for feat in self.et_layer.getFeatures() if feat['start_node'] == node_id]

        # Si viene del movimiento de un nodo de BT no tiene que volver a buscar las setas asociadas
        if estado_nivel_tension != "BT":
            self.associated_setas = [feat for feat in self.seta_layer.getFeatures() if feat['wdg1_node'] == node_id]

            self.associated_bt_nodes = []

            for seta_feat in self.associated_setas:
                node_bt_id = seta_feat.attribute("wdg2_node")
                node_bt_for_seta = find_node_by_uuid(self.node_bt_layer, node_bt_id)
                if node_bt_for_seta:
                    self.associated_bt_nodes.append(node_bt_for_seta)
            #print(f"Cantidad de elementos en associated_bt_nodes: {len(self.associated_bt_nodes)}")

            for node_bt_feat in self.associated_bt_nodes:
                #node_bt_id = node_bt_feat['id']
                node_bt_id = node_bt_feat.attribute("id")
                # Ojo! aquí se supone que va a ser un solo nodo_bt ya que si iterara, quedarian las lineas asociadas al ultimo elemento en el arreglo
                self.startNode_Bt_Movement(node_bt_id, estado_nivel_tension)

            for transformer_feat in self.associated_transformers:
                node_mt_id = transformer_feat.attribute("wdg2_node")
                node_mt_for_transformer = find_node_by_uuid(self.node_mt_layer, node_mt_id)
                if node_mt_for_transformer:
                    self.associated_mt_nodes.append(node_mt_for_transformer)
            
            for mt_node_feat in self.associated_mt_nodes:
                node_mt_id = mt_node_feat.attribute("id")

                mt_lines_for_associated_node = [feat for feat in self.line_mt_layer.getFeatures() if feat['start_node'] == node_mt_id or feat['end_node'] == node_mt_id]
                if mt_lines_for_associated_node:
                    self.associated_mt_lines.extend(mt_lines_for_associated_node)

                loads_for_associated_node = [feat for feat in self.load_layer.getFeatures() if feat['start_node'] == node_mt_id]
                if loads_for_associated_node:
                    self.associated_loads.extend(loads_for_associated_node)
                
                capacitors_for_associated_node = [feat for feat in self.capacitor_layer.getFeatures() if feat['start_node'] == node_mt_id]
                if capacitors_for_associated_node:
                    self.associated_capacitors.extend(capacitors_for_associated_node)


        for line_feat in self.associated_mt_lines:
            line_id = line_feat.attribute("id")
            # Buscar interruptores asociados a la línea actual
            switches_for_line = [switch_feat for switch_feat in self.switch_layer.getFeatures() if switch_feat['line'] == line_id]
            self.associated_switches.extend(switches_for_line)
            


    def startNode_Mt_Movement(self, node_id, estado_nivel_tension):
        print(f"startNode_Mt_Movement:")
        self.associated_mt_lines = [feat for feat in self.line_mt_layer.getFeatures() if feat['start_node'] == node_id or feat['end_node'] == node_id]
        self.associated_generators = [feat for feat in self.generator_layer.getFeatures() if feat['start_node'] == node_id]
        self.associated_pvsystems = [feat for feat in self.pv_system_layer.getFeatures() if feat['start_node'] == node_id]
        self.associated_loads = [feat for feat in self.load_layer.getFeatures() if feat['start_node'] == node_id]
        self.associated_capacitors = [feat for feat in self.capacitor_layer.getFeatures() if feat['start_node'] == node_id]
        self.associated_transformers = [feat for feat in self.transformer_layer.getFeatures() if feat['wdg1_node'] == node_id]
        self.associated_ets = [feat for feat in self.et_layer.getFeatures() if feat['start_node'] == node_id]

        self.associated_switches = []

        for line_feat in self.associated_mt_lines:
            line_id = line_feat.attribute("id")
            # Buscar interruptores asociados a la línea actual
            switches_for_line = [switch_feat for switch_feat in self.switch_layer.getFeatures() if switch_feat['line'] == line_id]
            self.associated_switches.extend(switches_for_line)
            #self.associated_switches.append(switches_for_line)

        # Si viene del movimiento de un nodo de BT no tiene que volver a buscar las setas asociadas
        if estado_nivel_tension != "BT":
            self.associated_setas = [feat for feat in self.seta_layer.getFeatures() if feat['wdg1_node'] == node_id]
            self.associated_bt_nodes = []

            for seta_feat in self.associated_setas:
                node_bt_id = seta_feat.attribute("wdg2_node")
                node_bt_for_seta = find_node_by_uuid(self.node_bt_layer, node_bt_id)
                if node_bt_for_seta:
                    self.associated_bt_nodes.append(node_bt_for_seta)            
            #print(f"Cantidad de elementos en associated_bt_nodes: {len(self.associated_bt_nodes)}")

            for node_bt_feat in self.associated_bt_nodes:
                #node_bt_id = node_bt_feat['id']
                node_bt_id = node_bt_feat.attribute("id")
                # Ojo! aquí se supone que va a ser un solo nodo_bt ya que si iterara, quedarian las lineas asociadas al ultimo elemento en el arreglo
                self.startNode_Bt_Movement(node_bt_id, estado_nivel_tension)

            self.associated_mt_nodes = []  # Esto es para mover los nodos de transformadores

            for transformer_feat in self.associated_transformers:
                node_mt_id = transformer_feat.attribute("wdg2_node")
                node_mt_for_transformer = find_node_by_uuid(self.node_mt_layer, node_mt_id)
                if node_mt_for_transformer:
                    self.associated_mt_nodes.append(node_mt_for_transformer)


    def startNode_Bt_Movement(self, node_id, estado_nivel_tension):
        print(f"startNode_Bt_Movement:")
        self.associated_bt_lines = [feat for feat in self.line_bt_layer.getFeatures() if feat['start_node'] == node_id or feat['end_node'] == node_id]
        # self.associated_generators = [feat for feat in self.generator_layer.getFeatures() if feat['start_node'] == node_id]
        # self.associated_loads = [feat for feat in self.load_layer.getFeatures() if feat['start_node'] == node_id]
        # self.associated_transformers = [feat for feat in self.transformer_layer.getFeatures() if feat['wdg1_node'] == node_id]
        # self.associated_ets = [feat for feat in self.et_layer.getFeatures() if feat['start_node'] == node_id]
 
        # Si viene del movimiento de un nodo de MT no tiene que volver a buscar las setas asociadas
        if estado_nivel_tension != "MT":
            self.associated_setas = [feat for feat in self.seta_layer.getFeatures() if feat['wdg2_node'] == node_id]
            self.associated_mt_nodes = []

            for seta_feat in self.associated_setas:
                node_mt_id = seta_feat.attribute("wdg1_node")
                node_mt_for_seta = find_node_by_uuid(self.node_mt_layer, node_mt_id)
                if node_mt_for_seta:
                    self.associated_mt_nodes.append(node_mt_for_seta)

            #print(f"cantidad de node_mt_for_seta: {len(self.associated_mt_nodes)}")

            for node_mt_feat in self.associated_mt_nodes:
                node_mt_id = node_mt_feat.attribute("id") 
                # Ojo! aquí se supone que va a ser un solo nodo_bt ya que si iterara, quedarian las lineas asociadas al ultimo elemento en el arreglo
                self.startNode_Mt_Movement(node_mt_id, estado_nivel_tension)
      
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

    def updateTransformerGeometry(self, transformer_feat, new_point):
        self.transformer_layer.startEditing()
        self.transformer_layer.changeGeometry(transformer_feat.id(), QgsGeometry.fromPointXY(new_point))

    def updateSetaGeometry(self, seta_feat, new_point):
        self.seta_layer.startEditing()
        self.seta_layer.changeGeometry(seta_feat.id(), QgsGeometry.fromPointXY(new_point))

    def updateEtGeometry(self, et_feat, new_point):
        self.et_layer.startEditing()
        self.et_layer.changeGeometry(et_feat.id(), QgsGeometry.fromPointXY(new_point))

    def updateGeneratorGeometry(self, generator_feat, new_point):
        self.generator_layer.startEditing()
        self.generator_layer.changeGeometry(generator_feat.id(), QgsGeometry.fromPointXY(new_point))
    
    def updatePvsystemGeometry(self, pvsystem_feat, new_point):
        self.pv_system_layer.startEditing()
        self.pv_system_layer.changeGeometry(pvsystem_feat.id(), QgsGeometry.fromPointXY(new_point))

    def updateLoadGeometry(self, load_feat, new_point):
        self.load_layer.startEditing()
        self.load_layer.changeGeometry(load_feat.id(), QgsGeometry.fromPointXY(new_point))

    def updateCapacitorGeometry(self, capacitor_feat, new_point):
        self.capacitor_layer.startEditing()
        self.capacitor_layer.changeGeometry(capacitor_feat.id(), QgsGeometry.fromPointXY(new_point))

    def updateSwitchGeometry(self, switch_feat):
        # Asegurarse de que la capa de interruptores esté en modo de edición
        self.switch_layer.startEditing()
        # Obtener el ID de la línea asociada al interruptor
        line_id = switch_feat['line']
        #line_id = switch_feat.attribute("line")
        # Buscar la característica de línea actualizada por su ID
        line_feat = find_line_by_uuid(self.line_mt_layer, line_id)
        if line_feat:
            # Calcular la nueva posición del interruptor basándose en la geometría actualizada de la línea
            new_switch_point = find_point_on_line(line_feat, switch_feat['terminal'])
            if new_switch_point:
                # Actualizar la geometría del interruptor con la nueva posición
                self.switch_layer.changeGeometry(switch_feat.id(), new_switch_point)
                #print(f"Moviendo Switch: {switch_feat.id()} a nueva posición")
            else:
                print("No se pudo calcular la nueva posición del interruptor")
        else:
            print("Línea asociada al interruptor no encontrada")

    def updateLine_mtGeometry(self, line_feat):
        self.line_mt_layer.startEditing()
        node1_feat = find_node_by_uuid(self.node_mt_layer, line_feat['start_node'])
        node2_feat = find_node_by_uuid(self.node_mt_layer, line_feat['end_node'])

        new_point_n1 = QgsPointXY(node1_feat.geometry().asPoint())
        new_point_n2 = QgsPointXY(node2_feat.geometry().asPoint())

        line_geom = line_feat.geometry()
        if line_geom.isMultipart():            
            #print(f"La linea es multi-polilínea")
            lines = line_geom.asMultiPolyline()
            for i in range(len(lines)):
                lines[i][0] = new_point_n1
                lines[i][-1] = new_point_n2
            new_geom = QgsGeometry.fromMultiPolylineXY(lines)
        else:
            #print(f"La linea es polilínea")
            line = line_geom.asPolyline()
            line[0] = new_point_n1
            line[-1] = new_point_n2
            new_geom = QgsGeometry.fromPolylineXY(line)

        self.line_mt_layer.changeGeometry(line_feat.id(), new_geom)

    def show_context_menu(self, event, element_type):
        menu = QMenu()
        edit_action = QAction("Editar elemento", self.canvas)
        if element_type == "node":
            edit_action.triggered.connect(self.edit_node_element)
        elif element_type == "line":
            edit_action.triggered.connect(self.edit_line_element)
        menu.addAction(edit_action)
        menu.exec_(self.canvas.mapToGlobal(event.pos()))

    def edit_node_element(self):
        if self.selected_node:
            node_id = self.selected_node.attribute("id")
            print(f"Editar nodo con ID: {node_id}")
            self.show_edit_form(self.selected_node, self.node_mt_layer)

    def edit_line_element(self):
        if self.selected_line:
            line_id = self.selected_line.attribute("id")
            print(f"Editar línea con ID: {line_id}")
            self.show_edit_form(self.selected_line, self.line_mt_layer)

    def show_edit_form(self, element, layer):
        dialog = QDialog()
        dialog.setWindowTitle("Editar elemento")

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.fields = {}
        for field_name in element.fields().names():
            field_value = element.attribute(field_name)
            line_edit = QLineEdit(str(field_value))
            self.fields[field_name] = line_edit
            form_layout.addRow(field_name, line_edit)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_edits(element, layer, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        dialog.exec_()

    def save_edits(self, element, layer, dialog):
        for field_name, line_edit in self.fields.items():
            element.setAttribute(field_name, line_edit.text())
        
        # Actualizar la capa con los cambios
        layer.startEditing()
        layer.updateFeature(element)
        layer.commitChanges()
        layer.triggerRepaint()

        dialog.accept()

# **** Hasta aquí estoy dentro de la clase CustomMapTool ****
# **** Hasta aquí estoy dentro de la clase CustomMapTool ****
# **** Hasta aquí estoy dentro de la clase CustomMapTool ****
# **** Hasta aquí estoy dentro de la clase CustomMapTool ****

def find_nearest_line_for_editing(line_layer, target_point):
    scale = iface.mapCanvas().scale()
    buffer_meters = scale / 500
    buffer_deg = buffer_meters / 111000.0
    buffer_distance = buffer_deg

    rect = QgsRectangle(target_point.x() - buffer_distance, target_point.y() - buffer_distance, target_point.x() + buffer_distance, target_point.y() + buffer_distance)
    line_layer.selectByRect(rect)
    selected_lines = [feature for feature in line_layer.selectedFeatures()]

    if selected_lines:
        nearest_line = min(selected_lines, key=lambda line: line.geometry().distance(QgsGeometry.fromPointXY(target_point)))
        return nearest_line

    return None


def updateLineGeometry(line_layer, line_feat, new_point, moving_node_id):
    line_layer.startEditing()
    line_geom = line_feat.geometry()
    if line_geom.isMultipart():
        lines = line_geom.asMultiPolyline()
        if line_feat['start_node'] == moving_node_id:
            for i in range(len(lines)):
                lines[i][0] = new_point
        if line_feat['end_node'] == moving_node_id:
            for i in range(len(lines)):
                lines[i][-1] = new_point
        new_geom = QgsGeometry.fromMultiPolylineXY(lines)
    else:
        line = line_geom.asPolyline()
        if line_feat['start_node'] == moving_node_id:
            line[0] = new_point
        if line_feat['end_node'] == moving_node_id:
            line[-1] = new_point
        new_geom = QgsGeometry.fromPolylineXY(line)
    line_layer.changeGeometry(line_feat.id(), new_geom)

# Funciona tanto para Nodos_MT como BT
# def updateNodeGeometry(node_layer, node_feat, clicked_point):
#     node_layer.startEditing()
#     new_geom = QgsGeometry.fromPointXY(QgsPointXY(clicked_point))
#     node_layer.changeGeometry(node_feat.id(), new_geom)

def updateNodeGeometry(node_layer, node_feat, clicked_point):
    node_layer.startEditing()
    new_geom = QgsGeometry.fromPointXY(QgsPointXY(clicked_point))
    node_layer.changeGeometry(node_feat.id(), new_geom)


def find_nearest_node_index(node_layer, target_point):
    scale = iface.mapCanvas().scale()
    #Ajusta max_distance_meters basado en la escala actual
    buffer_meters = scale / 100  # Ejemplo: 1 metro por cada 100 unidades en la escala
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
        node_layer.selectByIds([nearest_node.id()])
        return nearest_node
    # Devolver None si no se encontraron nodos seleccionados
    return None


def find_nearest_nodes_index(node_layer, target_point):
    # La diferencia con find_nearest_node_index es que esta función abre un cuadro de selección 
    # en el caso de que haya mas de un nodo en la misma coordenada, para elegirlo
    scale = iface.mapCanvas().scale()
    buffer_meters = scale / 100  # Ajustar según sea necesario
    buffer_deg = buffer_meters / 111000.0  # Aproximadamente 1 grado de latitud ~ 111,000 metros
    buffer_distance = buffer_deg
    
    rect = QgsRectangle(target_point.x() - buffer_distance, target_point.y() - buffer_distance, target_point.x() + buffer_distance, target_point.y() + buffer_distance)
    node_layer.selectByRect(rect)
    selected_nodes = [feature for feature in node_layer.selectedFeatures()]

    if selected_nodes:
        nearest_node = min(selected_nodes, key=lambda node: node.geometry().distance(QgsGeometry.fromPointXY(target_point)))
        nearest_node_coords = nearest_node.geometry().asPoint()
        nodes_at_same_location = [node for node in selected_nodes if node.geometry().asPoint() == nearest_node_coords]
        # Una forma más correcta de detectar nodos de entrada y salida de transformadores sería,no usar la superposición
        # de coordenadas, sinó, buscar entre trafos, y sus pares de nodos e/s el nodo faltante
        if len(nodes_at_same_location) > 1:
            nearest_node = select_node_dialog(nodes_at_same_location)

        return nearest_node
    return None


def select_node_dialog(nodes):
    dialog = QDialog()
    dialog.setWindowTitle("Select Node")
    layout = QVBoxLayout(dialog)
    combo_box = QComboBox(dialog)
    
    for node in nodes:
        node_id = node.attribute("id")
        combo_box.addItem(node_id, node)
    
    layout.addWidget(combo_box)
    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
    layout.addWidget(button_box)
    
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    
    dialog.setLayout(layout)
    
    if dialog.exec_() == QDialog.Accepted:
        return combo_box.currentData()
    return None


def find_nearest_line_index(line_layer, node_layer, target_point):    
    scale = iface.mapCanvas().scale()
    buffer_meters = scale / 500
    buffer_deg = buffer_meters / 111000.0
    buffer_distance = buffer_deg

    rect = QgsRectangle(target_point.x() - buffer_distance, target_point.y() - buffer_distance, target_point.x() + buffer_distance, target_point.y() + buffer_distance)
    line_layer.selectByRect(rect)
    selected_lines = [feature for feature in line_layer.selectedFeatures()]

    if selected_lines:
        nearest_line = min(selected_lines, key=lambda line: line.geometry().distance(QgsGeometry.fromPointXY(target_point)))
        
        start_node_id = nearest_line['start_node']
        end_node_id = nearest_line['end_node']

        start_node = find_node_by_uuid(node_layer, start_node_id)
        end_node = find_node_by_uuid(node_layer, end_node_id)

        start_node_distance = start_node.geometry().distance(QgsGeometry.fromPointXY(target_point))
        end_node_distance = end_node.geometry().distance(QgsGeometry.fromPointXY(target_point))

        # Calcular el punto a una distancia del 20% del closest_node en la línea
        line_length = nearest_line.geometry().length()

        if start_node_distance < end_node_distance:
            closest_node = start_node
            terminal = "1"
            distance_along_line = line_length * (1-ubicacion_switch)

        else:
            closest_node = end_node
            terminal = "2"
            distance_along_line = line_length * ubicacion_switch
   
        point_on_line = nearest_line.geometry().interpolate(distance_along_line)

        return nearest_line, terminal, point_on_line

    return None, None, None


def find_point_on_line(line_feature, terminal):

    if line_feature:
        line_length = line_feature.geometry().length()

        if terminal == "1":
            distance_along_line = line_length * (1-ubicacion_switch)
        elif terminal == "2":
            distance_along_line = line_length * ubicacion_switch
        else:
            print(f"Terminal erroneo: {terminal}")
            distance_along_line = line_length * ubicacion_switch

        point_on_line = line_feature.geometry().interpolate(distance_along_line)
        return point_on_line
    
    return None


def find_node_by_uuid(node_layer, uuid_str):
    for feature in node_layer.getFeatures():
        if feature['id'] == uuid_str:
            return feature
    return None


def find_line_by_uuid(line_layer, uuid_str):
    for feature in line_layer.getFeatures():
        if feature['id'] == uuid_str:
            return feature
    return None


#*************VERSION DE IMPORTACION CON PREFIJOS*************

def import_dss(node_mt_layer, line_layer, transformer_layer, generator_layer, pv_system_layer, et_layer, load_layer, switch_layer, capacitor_layer):
    # Preguntar al usuario si desea recodificar los elementos
    recodificar = QMessageBox.question(None, "Recodificar elementos", "¿Desea recodificar los elementos con nuevos UUIDs?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

    # Preguntar al usuario si desea usar un prefijo para la recodificación
    use_prefix, ok = QInputDialog.getText(None, "Prefijo de recodificación", "Ingrese un prefijo para la recodificación de elementos (dejar vacío para no usar prefijo):")
    if not ok:
        return

    # Abrir un cuadro de diálogo para seleccionar el archivo DSS
    options = QFileDialog.Options()
    options |= QFileDialog.ReadOnly
    dss_path, _ = QFileDialog.getOpenFileName(None, "Seleccionar archivo DSS", "", "Archivos DSS (*.dss);;Todos los archivos (*)", options=options)

    if not dss_path:
        print("No se seleccionó ningún archivo DSS.")
        return
    dss_instance = DSS(dss_path)

    # Inicializar la barra de progreso
    progressMessageBar = iface.messageBar().createMessage("Importando elementos DSS...")
    progress = QProgressBar()
    progress.setMaximum(100)  # Establecer el valor máximo según las etapas esperadas
    progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    messageLabel = QLabel("Iniciando importación...")  # Inicializar con un mensaje
    progressMessageBar.layout().addWidget(messageLabel)
    progressMessageBar.layout().addWidget(progress)
    iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)
    progress_level = 0
    
    dss_instance.compilar_DSS()
    dss_instance.resolver_DSS_snapshot(1.0)

    dssCktElement =  dss_instance.dssCktElement
    nodes = dss_instance.dssCircuit.AllBusNames
    lines = dss_instance.dssLines
    transformers = dss_instance.dssTransformers
    loads = dss_instance.dssLoads
    relays = dss_instance.dssRelays
    vsources = dss_instance.dssVsources
    Capacitors = dss_instance.dssCapacitors
    Generators = dss_instance.dssGenerators
    PVSystems = dss_instance.dssPVSystems
    Settings = dss_instance.dssSettings

    node_count = len(nodes)
    line_count = len(lines)
    transformer_count = len(transformers)
    load_count = loads.Count
    relay_count = relays.Count
    vsource_count = vsources.Count
    capacitor_count = Capacitors.Count
    generator_count = Generators.Count
    pvsystem_count = PVSystems.Count
    myVBases = Settings.VoltageBases

    print(f"Cantidad de nodos en la red: {node_count}")
    print(f"Cantidad de líneas en la red: {line_count}")
    print(f"Cantidad de transformadores en la red: {transformer_count}")
    print(f"Cantidad de cargas en la red: {load_count}")
    print(f"Cantidad de relays en la red: {relay_count}")
    print(f"Cantidad de Vsource en la red: {vsource_count}")
    print(f"Cantidad de Capacitores en la red: {capacitor_count}")
    print(f"Cantidad de Generadores en la red: {generator_count}")
    print(f"Cantidad de PVSystems en la red: {pvsystem_count}")
    print(f"Los Voltaje Base son: {myVBases}")

    # Tablas de equivalencias
    node_equivalences = {}
    line_equivalences = {}
    transformer_equivalences = {}
    load_equivalences = {}
    capacitor_equivalences = {}
    generator_equivalences = {}
    pv_system_equivalences = {}
    switch_equivalences = {}
    et_equivalences = {}

    total_elements = node_count + line_count + transformer_count + load_count + relay_count + vsource_count + capacitor_count + generator_count + pvsystem_count
    increment_per_element = 100 / total_elements
    messageLabel.setText("Importando nodos...")
    progress.setValue(int(progress_level))
    QApplication.processEvents()
    # Importar nodos MT
    node_mt_layer.startEditing()
    for node in nodes:
        dss_instance.activar_barra(node)
        x, y = dss_instance.dssBus.x, dss_instance.dssBus.y
        if x != 0 and y != 0:
            new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else generate_new_id(node, use_prefix)
            #new_id = str(uuid.uuid4())
            node_equivalences[node] = new_id
            node_feature = QgsFeature(node_mt_layer.fields())
            node_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
            node_feature.setAttribute("id", new_id)
            node_mt_layer.addFeature(node_feature)

        progress_level += increment_per_element
        progress.setValue(int(progress_level))
        QApplication.processEvents()

    node_mt_layer.commitChanges()
    print(f"Cantidad de nodos importados: {len(node_mt_layer)}")

    #print(f"Tabla de Nodos: {node_equivalences}")

    # Importar líneas MT
    messageLabel.setText("Importando lineas...")
    line_layer.startEditing()

    if lines.First != 0:
        while True:
            line_name = lines.Name
            bus1 = lines.Bus1.split('.')[0]
            bus2 = lines.Bus2.split('.')[0]

            # Verificar si las claves existen en node_equivalences
            bus1_new_id = node_equivalences.get(bus1, None)
            bus2_new_id = node_equivalences.get(bus2, None)

            if bus1_new_id is None or bus2_new_id is None:
                print(f"Clave {bus1} o {bus2} no encontrada en node_equivalences")
                # Manejar el caso donde la clave no existe
                iface.messageBar().clearWidgets()  # Limpiar la barra de mensajes
                return

            bus1_feature = find_node_by_uuid(node_mt_layer, bus1_new_id)
            bus2_feature = find_node_by_uuid(node_mt_layer, bus2_new_id)


            if bus1_feature and bus2_feature:
                bus1_geom = bus1_feature.geometry().asPoint()
                bus2_geom = bus2_feature.geometry().asPoint()
                #new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else line_name
                new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else generate_new_id(line_name, use_prefix)
                line_equivalences[line_name] = new_id
                line_feature = QgsFeature(line_layer.fields())
                line_feature.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(bus1_geom), QgsPointXY(bus2_geom)]))
                line_feature.setAttribute("id", new_id)
                line_feature.setAttribute("start_node", node_equivalences[bus1])
                line_feature.setAttribute("end_node", node_equivalences[bus2])
                #******<Parametros esenciales***************
                line_feature.setAttribute("length", str(lines.Length))
                line_feature.setAttribute("units", str(lines.Units)) # Ocurre que viene en none porque no toma el atributo units=m en el .dss
                line_feature.setAttribute("r1", str(lines.R1))
                line_feature.setAttribute("r0", str(lines.R0))
                line_feature.setAttribute("x1", str(lines.X1))
                line_feature.setAttribute("x0", str(lines.X0))
                line_feature.setAttribute("c1", str(lines.C1))
                line_feature.setAttribute("c0", str(lines.C0))                
                line_feature.setAttribute("phases", str(lines.Phases))
                #line_feature.setAttribute("enabled", lines.Units)
                dss_instance.activar_elemento(f"Line.{line_name}")
                Enabled = dssCktElement.Properties("enabled").Val
                line_feature.setAttribute("enabled", Enabled)
                #******<Parametros adicionales**************
                #line_feature.setAttribute("rg", str(lines.Rg))
                #line_feature.setAttribute("rho", str(lines.Rho))
                #line_feature.setAttribute("seasonrating", str(lines.SeasonRating))
                #line_feature.setAttribute("xg", str(lines.Xg))
                #line_feature.setAttribute("linecode", str(lines.LineCode))
                #line_feature.setAttribute("geometry", str(lines.Geometry))
                #line_feature.setAttribute("spacing", str(lines.Spacing))
                #line_feature.setAttribute("normamps", str(lines.NormAmps))
                #******>Parametros***************
                line_layer.addFeature(line_feature)

            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

            if lines.Next == 0:
                break

    line_layer.commitChanges()    
    print(f"Cantidad de líneas importadas: {len(line_layer)}")

    # Importar transformadores
    messageLabel.setText("Importando Transformadores...")
    transformer_layer.startEditing()

    if transformers.First != 0:
        while True:
            transformer_name = transformers.Name  # Obtener el nombre del transformador actual
            dss_instance.activar_elemento(f"Transformer.{transformer_name}")  # Activar el transformador actual
            barra1, barra2 = dss_instance.obtener_barras_elemento()  # Obtener los nombres de las barras conectadas

            bus1 = barra1.split('.')[0]
            bus2 = barra2.split('.')[0]
            bus1_feature = find_node_by_uuid(node_mt_layer, node_equivalences[bus1])

            if bus1_feature:
                bus1_geom = bus1_feature.geometry().asPoint()
                #new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else transformer_name
                new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else generate_new_id(transformer_name, use_prefix)
                transformer_equivalences[transformer_name] = new_id
                transformer_feature = QgsFeature(transformer_layer.fields())
                transformer_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
                transformer_feature.setAttribute("id", new_id)
                transformer_feature.setAttribute("wdg1_node", node_equivalences[bus1])
                transformer_feature.setAttribute("wdg2_node", node_equivalences[bus2])
                #******<Parametros esenciales***************
                transformers.Wdg = 2
                transformer_feature.setAttribute("kv2", str(transformers.kV))
                transformer_feature.setAttribute("kva2", str(transformers.kva))
                transformers.Wdg = 1
                transformer_feature.setAttribute("kv1", str(transformers.kV))
                transformer_feature.setAttribute("kva1", str(transformers.kva))            
                transformer_feature.setAttribute("xhl", str(transformers.xhl))
                #******<Parametros esenciales no presentes en interfaz*****
                dss_instance.activar_elemento(f"Transformer.{transformer_name}")
                phases = dssCktElement.Properties("phases").Val
                transformer_feature.setAttribute("phases", phases)
                percent_imag = dssCktElement.Properties("%imag").Val
                transformer_feature.setAttribute("%imag", percent_imag)
                percent_loadloss = dssCktElement.Properties("%loadloss").Val
                transformer_feature.setAttribute("%loadloss", percent_loadloss)
                percent_noloadloss = dssCktElement.Properties("%noloadloss").Val
                transformer_feature.setAttribute("%nloadloss", percent_noloadloss)
                conns = dssCktElement.Properties("conns").Val
                transformer_feature.setAttribute("conns", conns)
                ppm_antifloat = dssCktElement.Properties("ppm_antifloat").Val
                transformer_feature.setAttribute("ppm_afloat", ppm_antifloat)
                #******<Parametros adicionales**************
                #transformer_feature.setAttribute("coretype", transformers.CoreType)
                #transformer_feature.setAttribute("isdelta", transformers.IsDelta)      
                #transformer_feature.setAttribute("maxtap", transformers.MaxTap)
                #transformer_feature.setAttribute("mintap", transformers.MinTap)
                #transformer_feature.setAttribute("numtaps", transformers.NumTaps)          
                #transformer_feature.setAttribute("numwindings", transformers.NumWindings)
                #transformer_feature.setAttribute("r", transformers.R)
                #transformers.Wdg = 2
                #transformer_feature.setAttribute("rdcohms2", transformers.RdcOhms)
                #transformers.Wdg = 1
                #transformer_feature.setAttribute("rdcohms1", transformers.RdcOhms)
                #transformer_feature.setAttribute("rneut", transformers.Rneut)
                #transformer_feature.setAttribute("tap", transformers.Tap)
                #transformer_feature.setAttribute("xfrmcode", transformers.XfrmCode)  
                #transformer_feature.setAttribute("xht", transformers.Xht)
                #transformer_feature.setAttribute("xlt", transformers.Xlt)
                #transformer_feature.setAttribute("xneut", transformers.Xneut)
                #******>Parametros***************
                transformer_layer.addFeature(transformer_feature)

            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()  

            if transformers.Next == 0:
                break

    transformer_layer.commitChanges()    
    print(f"Cantidad de transformadores importados: {len(transformer_layer)}")

    # Importar cargas
    messageLabel.setText("Importando Cargas...")
    load_layer.startEditing()

    if loads.First != 0:
        while True:
            load_name = loads.Name  # Obtener el nombre de la carga actual
            dss_instance.activar_elemento(f"Load.{load_name}")  # Activar la carga actual
            barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

            bus1 = barra1.split('.')[0]
            bus1_feature = find_node_by_uuid(node_mt_layer, node_equivalences[bus1])

            if bus1_feature:
                bus1_geom = bus1_feature.geometry().asPoint()
                #new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else load_name
                new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else generate_new_id(load_name, use_prefix)
                load_equivalences[load_name] = new_id
                load_feature = QgsFeature(load_layer.fields())
                load_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
                load_feature.setAttribute("id", new_id)
                load_feature.setAttribute("start_node", node_equivalences[bus1])
                #******<Parametros esenciales***************
                load_feature.setAttribute("kv", str(loads.kV))
                load_feature.setAttribute("kw", str(loads.kW))
                load_feature.setAttribute("pf", str(loads.PF))
                #load_feature.setAttribute("status", str(loads.Status)) #Lo toma mal
                load_feature.setAttribute("model", str(loads.Model))
                load_feature.setAttribute("cvrwatts", str(loads.CVRwatts))
                load_feature.setAttribute("cvrvars", str(loads.CVRvars))
                load_feature.setAttribute("class", str(loads.Class))
                load_feature.setAttribute("daily", str(loads.daily))
                #******<Parametros esenciales no presentes en interfaz*****
                dss_instance.activar_elemento(f"Load.{load_name}")
                phases = dssCktElement.Properties("phases").Val
                load_feature.setAttribute("phases", phases)
                conn = dssCktElement.Properties("conn").Val
                load_feature.setAttribute("conn", conn)
                status = dssCktElement.Properties("status").Val
                load_feature.setAttribute("status", status)
                #******<Parametros adicionales**************
                #...
                #...
                #******>Parametros***************
                load_layer.addFeature(load_feature)

            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

            if loads.Next == 0:
                break

    load_layer.commitChanges()
    print(f"Cantidad de cargas importadas: {len(load_layer)}")

    # Importar capacitores
    messageLabel.setText("Importando Capacitores...")
    capacitor_layer.startEditing()

    if Capacitors.First != 0:
        while True:
            capacitor_name = Capacitors.Name  # Obtener el nombre del capacitor actual
            dss_instance.activar_elemento(f"Capacitor.{capacitor_name}")  # Activar el capacitor actual
            barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

            bus1 = barra1.split('.')[0]
            bus1_feature = find_node_by_uuid(node_mt_layer, node_equivalences[bus1])

            if bus1_feature:
                bus1_geom = bus1_feature.geometry().asPoint()
                #new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else capacitor_name
                new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else generate_new_id(capacitor_name, use_prefix)
                capacitor_equivalences[capacitor_name] = new_id
                capacitor_feature = QgsFeature(capacitor_layer.fields())
                capacitor_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
                capacitor_feature.setAttribute("id", new_id)
                capacitor_feature.setAttribute("start_node", node_equivalences[bus1])
                #******<Parametros esenciales***************
                capacitor_feature.setAttribute("kv", str(Capacitors.kV))
                capacitor_feature.setAttribute("kvar", str(Capacitors.kvar))
                #******<Parametros esenciales no presentes en interfaz*****
                dss_instance.activar_elemento(f"Capacitor.{capacitor_name}")
                phases = dssCktElement.Properties("phases").Val
                capacitor_feature.setAttribute("phases", phases)
                #******<Parametros adicionales**************
                #...
                #...
                #******>Parametros***************
                capacitor_layer.addFeature(capacitor_feature)

            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

            if Capacitors.Next == 0:
                break

    capacitor_layer.commitChanges()
    print(f"Cantidad de capacitores importados: {len(capacitor_layer)}")

    # Importar generadores
    messageLabel.setText("Importando Generadores...")
    generator_layer.startEditing()

    if Generators.First != 0:
        while True:
            generator_name = Generators.Name  # Obtener el nombre del generador actual
            dss_instance.activar_elemento(f"Generator.{generator_name}")  # Activar el generador actual
            barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

            bus1 = barra1.split('.')[0]
            bus1_feature = find_node_by_uuid(node_mt_layer, node_equivalences[bus1])

            if bus1_feature:
                bus1_geom = bus1_feature.geometry().asPoint()
                #new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else generator_name
                new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else generate_new_id(generator_name, use_prefix)
                generator_equivalences[generator_name] = new_id
                generator_feature = QgsFeature(generator_layer.fields())
                generator_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
                generator_feature.setAttribute("id", new_id)
                generator_feature.setAttribute("start_node", node_equivalences[bus1])
                #******<Parametros esenciales***************
                generator_feature.setAttribute("Phases", str(Generators.Phases))
                generator_feature.setAttribute("kV", str(Generators.kV))
                generator_feature.setAttribute("kW", str(Generators.kW))
                generator_feature.setAttribute("PF", str(Generators.PF))
                #******<Parametros esenciales no presentes en interfaz*****
                dss_instance.activar_elemento(f"Generator.{generator_name}")
                daily = dssCktElement.Properties("daily").Val
                generator_feature.setAttribute("daily", daily)
                #******<Parametros adicionales**************
                #...
                #...
                #******>Parametros***************
                generator_layer.addFeature(generator_feature)

            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

            if Generators.Next == 0:
                break

    generator_layer.commitChanges()
    print(f"Cantidad de generadores importados: {len(generator_layer)}")

    # Importar sistemas fotovoltaicos
    messageLabel.setText("Importando Sistemas Fotovoltaicos...")
    pv_system_layer.startEditing()

    if PVSystems.First != 0:
        while True:
            pv_system_name = PVSystems.Name  # Obtener el nombre del sistema fotovoltaico actual
            dss_instance.activar_elemento(f"PVSystem.{pv_system_name}")  # Activar el sistema fotovoltaico actual
            barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

            bus1 = barra1.split('.')[0]
            bus1_feature = find_node_by_uuid(node_mt_layer, node_equivalences[bus1])

            if bus1_feature:
                bus1_geom = bus1_feature.geometry().asPoint()
                #new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else pv_system_name
                new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else generate_new_id(pv_name, use_prefix)
                pv_system_equivalences[pv_system_name] = new_id
                pv_system_feature = QgsFeature(pv_system_layer.fields())
                pv_system_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
                pv_system_feature.setAttribute("id", new_id)
                pv_system_feature.setAttribute("start_node", node_equivalences[bus1])
                #******<Parametros esenciales***************
                pv_system_feature.setAttribute("Irradiance", str(PVSystems.Irradiance))
                pv_system_feature.setAttribute("Pmpp", str(PVSystems.Pmpp))
                #******<Parametros esenciales no presentes en interfaz*****
                dss_instance.activar_elemento(f"PVSystem.{pv_system_name}")
                phases = dssCktElement.Properties("phases").Val
                pv_system_feature.setAttribute("phases", phases)
                kv = dssCktElement.Properties("kv").Val
                pv_system_feature.setAttribute("kv", kv)
                temperature = dssCktElement.Properties("Temperature").Val
                pv_system_feature.setAttribute("Temperatur", temperature)  # Ojo que el atributo en Opendss es Temperature, pero qgis permite solo 10 caracteres
                kva = dssCktElement.Properties("kVA").Val
                pv_system_feature.setAttribute("kVA", kva)
                effcurve = dssCktElement.Properties("EffCurve").Val
                pv_system_feature.setAttribute("EffCurve", effcurve)
                daily = dssCktElement.Properties("daily").Val
                pv_system_feature.setAttribute("daily", daily)
                tdaily = dssCktElement.Properties("Tdaily").Val
                pv_system_feature.setAttribute("Tdaily", tdaily)
                #******<Parametros adicionales**************
                #...
                #...
                #******>Parametros***************
                pv_system_layer.addFeature(pv_system_feature)

            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

            if PVSystems.Next == 0:
                break

    pv_system_layer.commitChanges()
    print(f"Cantidad de sistemas fotovoltaicos importados: {len(pv_system_layer)}")

    # Importar interruptores
    messageLabel.setText("Importando Relays...")
    switch_layer.startEditing()

    if relays.First != 0:
        while True:
            relay_name = relays.Name  # Obtener el nombre del relay actual
            monitored_obj = relays.MonitoredObj  # Obtener el MonitoredObj
            linea = monitored_obj.split(".")[1]
            monitored_term = str(relays.MonitoredTerm)  # Obtener el MonitoredTerm

            # Obtener la línea asociada al relay
            line_feat = find_line_by_uuid(line_layer, line_equivalences[linea])
            if line_feat:
                # Calcular la posición del interruptor en la línea
                switch_point = find_point_on_line(line_feat, monitored_term)
                if switch_point:
                    #new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else relay_name
                    new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else generate_new_id(relay_name, use_prefix)
                    switch_equivalences[relay_name] = new_id
                    switch_feature = QgsFeature(switch_layer.fields())
                    switch_feature.setGeometry(switch_point)
                    switch_feature.setAttribute("id", new_id)
                    switch_feature.setAttribute("line", line_equivalences[linea])
                    switch_feature.setAttribute("terminal", monitored_term)
                    #******<Parametros esenciales no presentes en interfaz*****
                    dss_instance.activar_elemento(f"Relay.{relay_name}")
                    State = dssCktElement.Properties("State").Val
                    switch_feature.setAttribute("State", State)
                    #******<Parametros adicionales**************
                    #...
                    #...
                    #******>Parametros***************
                    switch_layer.addFeature(switch_feature)

            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

            if relays.Next == 0:
                break

    switch_layer.commitChanges()
    print(f"Cantidad de relays importados: {len(switch_layer)}")

    # Importar Vsources
    messageLabel.setText("Importando Vsources...")
    et_layer.startEditing()

    if vsources.First != 0:
        while True:
            vsource_name = vsources.Name  # Obtener el nombre del Vsource actual
            dss_instance.activar_elemento(f"Vsource.{vsource_name}")  # Activar el Vsource actual
            barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

            bus1 = barra1.split('.')[0]
            bus1_feature = find_node_by_uuid(node_mt_layer, node_equivalences[bus1])

            if bus1_feature:
                bus1_geom = bus1_feature.geometry().asPoint()
                #new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else vsource_name
                new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else generate_new_id(vsource_name, use_prefix)
                et_equivalences[vsource_name] = new_id
                et_feature = QgsFeature(et_layer.fields())
                et_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
                et_feature.setAttribute("id", new_id)
                et_feature.setAttribute("start_node", node_equivalences[bus1])
                #******<Parametros esenciales***************
                et_feature.setAttribute("pu", str(vsources.pu))
                et_feature.setAttribute("basekv", str(vsources.BasekV))
                #******<Parametros esenciales no presentes en interfaz*****
                dss_instance.activar_elemento(f"Vsource.{vsource_name}")
                r1 = dssCktElement.Properties("r1").Val
                et_feature.setAttribute("r1", r1)
                r0 = dssCktElement.Properties("r0").Val
                et_feature.setAttribute("r0", r0 )
                x1 = dssCktElement.Properties("x1").Val
                et_feature.setAttribute("x1", x1 )
                x0 = dssCktElement.Properties("x0").Val
                et_feature.setAttribute("x0", x0 )
                #******<Parametros adicionales**************
                #...
                #...
                #******>Parametros***************
                et_layer.addFeature(et_feature)

            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

            if vsources.Next == 0:
                break

    et_layer.commitChanges()
    print(f"Cantidad de Vsources importados: {len(et_layer)}")

    # Finalización
    iface.messageBar().clearWidgets()  # Limpiar la barra de mensajes

    print("Importación desde OpenDSS completada.")


def generate_new_id(old_id, prefix):
    """
    Genera un nuevo ID concatenando un prefijo con el ID original.
    
    :param old_id: El ID original del elemento.
    :param prefix: El prefijo proporcionado por el usuario.
    :return: Un nuevo ID con el prefijo concatenado.
    """
    return f"{prefix}_{old_id}" if prefix else old_id


#*************VERSION DE IMPORTACION CON REDEFINICION DE CODIGOS*************

# def import_dss(node_mt_layer, line_layer, transformer_layer, generator_layer, pv_system_layer, et_layer, load_layer, switch_layer, capacitor_layer):
#     # Preguntar al usuario si desea recodificar los elementos
#     recodificar = QMessageBox.question(None, "Recodificar elementos", "¿Desea recodificar los elementos con nuevos UUIDs?",
#                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

#     # Abrir un cuadro de diálogo para seleccionar el archivo DSS
#     options = QFileDialog.Options()
#     options |= QFileDialog.ReadOnly
#     dss_path, _ = QFileDialog.getOpenFileName(None, "Seleccionar archivo DSS", "", "Archivos DSS (*.dss);;Todos los archivos (*)", options=options)

#     if not dss_path:
#         print("No se seleccionó ningún archivo DSS.")
#         return
#     dss_instance = DSS(dss_path)

#     # Inicializar la barra de progreso
#     progressMessageBar = iface.messageBar().createMessage("Importando elementos DSS...")
#     progress = QProgressBar()
#     progress.setMaximum(100)  # Establecer el valor máximo según las etapas esperadas
#     progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
#     messageLabel = QLabel("Iniciando importación...")  # Inicializar con un mensaje
#     progressMessageBar.layout().addWidget(messageLabel)
#     progressMessageBar.layout().addWidget(progress)
#     iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)
#     progress_level = 0
    
#     dss_instance.compilar_DSS()
#     dss_instance.resolver_DSS_snapshot(1.0)

#     dssCktElement =  dss_instance.dssCktElement
#     nodes = dss_instance.dssCircuit.AllBusNames
#     lines = dss_instance.dssLines
#     transformers = dss_instance.dssTransformers
#     loads = dss_instance.dssLoads
#     relays = dss_instance.dssRelays
#     vsources = dss_instance.dssVsources
#     Capacitors = dss_instance.dssCapacitors
#     Generators = dss_instance.dssGenerators
#     PVSystems = dss_instance.dssPVSystems
#     Settings = dss_instance.dssSettings

#     node_count = len(nodes)
#     line_count = len(lines)
#     transformer_count = len(transformers)
#     load_count = loads.Count
#     relay_count = relays.Count
#     vsource_count = vsources.Count
#     capacitor_count = Capacitors.Count
#     generator_count = Generators.Count
#     pvsystem_count = PVSystems.Count
#     myVBases = Settings.VoltageBases

#     print(f"Cantidad de nodos en la red: {node_count}")
#     print(f"Cantidad de líneas en la red: {line_count}")
#     print(f"Cantidad de transformadores en la red: {transformer_count}")
#     print(f"Cantidad de cargas en la red: {load_count}")
#     print(f"Cantidad de relays en la red: {relay_count}")
#     print(f"Cantidad de Vsource en la red: {vsource_count}")
#     print(f"Cantidad de Capacitores en la red: {capacitor_count}")
#     print(f"Cantidad de Generadores en la red: {generator_count}")
#     print(f"Cantidad de PVSystems en la red: {pvsystem_count}")
#     print(f"Los Voltaje Base son: {myVBases}")

#     # Tablas de equivalencias
#     node_equivalences = {}
#     line_equivalences = {}
#     transformer_equivalences = {}
#     load_equivalences = {}
#     capacitor_equivalences = {}
#     generator_equivalences = {}
#     pv_system_equivalences = {}
#     switch_equivalences = {}
#     et_equivalences = {}

#     total_elements = node_count + line_count + transformer_count + load_count + relay_count + vsource_count + capacitor_count + generator_count + pvsystem_count
#     increment_per_element = 100 / total_elements
#     messageLabel.setText("Importando nodos...")
#     progress.setValue(int(progress_level))
#     QApplication.processEvents()
#     # Importar nodos MT
#     node_mt_layer.startEditing()
#     for node in nodes:
#         dss_instance.activar_barra(node)
#         x, y = dss_instance.dssBus.x, dss_instance.dssBus.y
#         if x != 0 and y != 0:
#             new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else node
#             #new_id = str(uuid.uuid4())
#             node_equivalences[node] = new_id
#             node_feature = QgsFeature(node_mt_layer.fields())
#             node_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
#             node_feature.setAttribute("id", new_id)
#             node_mt_layer.addFeature(node_feature)

#         progress_level += increment_per_element
#         progress.setValue(int(progress_level))
#         QApplication.processEvents()

#     node_mt_layer.commitChanges()
#     print(f"Cantidad de nodos importados: {len(node_mt_layer)}")

#     #print(f"Tabla de Nodos: {node_equivalences}")

#     # Importar líneas MT
#     messageLabel.setText("Importando lineas...")
#     line_layer.startEditing()

#     if lines.First != 0:
#         while True:
#             line_name = lines.Name
#             bus1 = lines.Bus1.split('.')[0]
#             bus2 = lines.Bus2.split('.')[0]

#             # Verificar si las claves existen en node_equivalences
#             bus1_new_id = node_equivalences.get(bus1, None)
#             bus2_new_id = node_equivalences.get(bus2, None)

#             if bus1_new_id is None or bus2_new_id is None:
#                 print(f"Clave {bus1} o {bus2} no encontrada en node_equivalences")
#                 # Manejar el caso donde la clave no existe
#                 iface.messageBar().clearWidgets()  # Limpiar la barra de mensajes
#                 return

#             bus1_feature = find_node_by_uuid(node_mt_layer, bus1_new_id)
#             bus2_feature = find_node_by_uuid(node_mt_layer, bus2_new_id)


#             if bus1_feature and bus2_feature:
#                 bus1_geom = bus1_feature.geometry().asPoint()
#                 bus2_geom = bus2_feature.geometry().asPoint()
#                 new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else line_name
#                 line_equivalences[line_name] = new_id
#                 line_feature = QgsFeature(line_layer.fields())
#                 line_feature.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(bus1_geom), QgsPointXY(bus2_geom)]))
#                 line_feature.setAttribute("id", new_id)
#                 line_feature.setAttribute("start_node", node_equivalences[bus1])
#                 line_feature.setAttribute("end_node", node_equivalences[bus2])
#                 #******<Parametros esenciales***************
#                 line_feature.setAttribute("length", str(lines.Length))
#                 line_feature.setAttribute("units", str(lines.Units)) # Ocurre que viene en none porque no toma el atributo units=m en el .dss
#                 line_feature.setAttribute("r1", str(lines.R1))
#                 line_feature.setAttribute("r0", str(lines.R0))
#                 line_feature.setAttribute("x1", str(lines.X1))
#                 line_feature.setAttribute("x0", str(lines.X0))
#                 line_feature.setAttribute("c1", str(lines.C1))
#                 line_feature.setAttribute("c0", str(lines.C0))                
#                 line_feature.setAttribute("phases", str(lines.Phases))
#                 #line_feature.setAttribute("enabled", lines.Units)
#                 dss_instance.activar_elemento(f"Line.{line_name}")
#                 Enabled = dssCktElement.Properties("enabled").Val
#                 line_feature.setAttribute("enabled", Enabled)
#                 #******<Parametros adicionales**************
#                 #line_feature.setAttribute("rg", str(lines.Rg))
#                 #line_feature.setAttribute("rho", str(lines.Rho))
#                 #line_feature.setAttribute("seasonrating", str(lines.SeasonRating))
#                 #line_feature.setAttribute("xg", str(lines.Xg))
#                 #line_feature.setAttribute("linecode", str(lines.LineCode))
#                 #line_feature.setAttribute("geometry", str(lines.Geometry))
#                 #line_feature.setAttribute("spacing", str(lines.Spacing))
#                 #line_feature.setAttribute("normamps", str(lines.NormAmps))
#                 #******>Parametros***************
#                 line_layer.addFeature(line_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()

#             if lines.Next == 0:
#                 break

#     line_layer.commitChanges()    
#     print(f"Cantidad de líneas importadas: {len(line_layer)}")

#     # Importar transformadores
#     messageLabel.setText("Importando Transformadores...")
#     transformer_layer.startEditing()

#     if transformers.First != 0:
#         while True:
#             transformer_name = transformers.Name  # Obtener el nombre del transformador actual
#             dss_instance.activar_elemento(f"Transformer.{transformer_name}")  # Activar el transformador actual
#             barra1, barra2 = dss_instance.obtener_barras_elemento()  # Obtener los nombres de las barras conectadas

#             bus1 = barra1.split('.')[0]
#             bus2 = barra2.split('.')[0]
#             bus1_feature = find_node_by_uuid(node_mt_layer, node_equivalences[bus1])

#             if bus1_feature:
#                 bus1_geom = bus1_feature.geometry().asPoint()
#                 new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else transformer_name
#                 transformer_equivalences[transformer_name] = new_id
#                 transformer_feature = QgsFeature(transformer_layer.fields())
#                 transformer_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
#                 transformer_feature.setAttribute("id", new_id)
#                 transformer_feature.setAttribute("wdg1_node", node_equivalences[bus1])
#                 transformer_feature.setAttribute("wdg2_node", node_equivalences[bus2])
#                 #******<Parametros esenciales***************
#                 transformers.Wdg = 2
#                 transformer_feature.setAttribute("kv2", str(transformers.kV))
#                 transformer_feature.setAttribute("kva2", str(transformers.kva))
#                 transformers.Wdg = 1
#                 transformer_feature.setAttribute("kv1", str(transformers.kV))
#                 transformer_feature.setAttribute("kva1", str(transformers.kva))            
#                 transformer_feature.setAttribute("xhl", str(transformers.xhl))
#                 #******<Parametros esenciales no presentes en interfaz*****
#                 dss_instance.activar_elemento(f"Transformer.{transformer_name}")
#                 phases = dssCktElement.Properties("phases").Val
#                 transformer_feature.setAttribute("phases", phases)
#                 percent_imag = dssCktElement.Properties("%imag").Val
#                 transformer_feature.setAttribute("%imag", percent_imag)
#                 percent_loadloss = dssCktElement.Properties("%loadloss").Val
#                 transformer_feature.setAttribute("%loadloss", percent_loadloss)
#                 percent_noloadloss = dssCktElement.Properties("%noloadloss").Val
#                 transformer_feature.setAttribute("%nloadloss", percent_noloadloss)
#                 conns = dssCktElement.Properties("conns").Val
#                 transformer_feature.setAttribute("conns", conns)
#                 ppm_antifloat = dssCktElement.Properties("ppm_antifloat").Val
#                 transformer_feature.setAttribute("ppm_afloat", ppm_antifloat)
#                 #******<Parametros adicionales**************
#                 #transformer_feature.setAttribute("coretype", transformers.CoreType)
#                 #transformer_feature.setAttribute("isdelta", transformers.IsDelta)      
#                 #transformer_feature.setAttribute("maxtap", transformers.MaxTap)
#                 #transformer_feature.setAttribute("mintap", transformers.MinTap)
#                 #transformer_feature.setAttribute("numtaps", transformers.NumTaps)          
#                 #transformer_feature.setAttribute("numwindings", transformers.NumWindings)
#                 #transformer_feature.setAttribute("r", transformers.R)
#                 #transformers.Wdg = 2
#                 #transformer_feature.setAttribute("rdcohms2", transformers.RdcOhms)
#                 #transformers.Wdg = 1
#                 #transformer_feature.setAttribute("rdcohms1", transformers.RdcOhms)
#                 #transformer_feature.setAttribute("rneut", transformers.Rneut)
#                 #transformer_feature.setAttribute("tap", transformers.Tap)
#                 #transformer_feature.setAttribute("xfrmcode", transformers.XfrmCode)  
#                 #transformer_feature.setAttribute("xht", transformers.Xht)
#                 #transformer_feature.setAttribute("xlt", transformers.Xlt)
#                 #transformer_feature.setAttribute("xneut", transformers.Xneut)
#                 #******>Parametros***************
#                 transformer_layer.addFeature(transformer_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()  

#             if transformers.Next == 0:
#                 break

#     transformer_layer.commitChanges()    
#     print(f"Cantidad de transformadores importados: {len(transformer_layer)}")

#     # Importar cargas
#     messageLabel.setText("Importando Cargas...")
#     load_layer.startEditing()

#     if loads.First != 0:
#         while True:
#             load_name = loads.Name  # Obtener el nombre de la carga actual
#             dss_instance.activar_elemento(f"Load.{load_name}")  # Activar la carga actual
#             barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

#             bus1 = barra1.split('.')[0]
#             bus1_feature = find_node_by_uuid(node_mt_layer, node_equivalences[bus1])

#             if bus1_feature:
#                 bus1_geom = bus1_feature.geometry().asPoint()
#                 new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else load_name
#                 load_equivalences[load_name] = new_id
#                 load_feature = QgsFeature(load_layer.fields())
#                 load_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
#                 load_feature.setAttribute("id", new_id)
#                 load_feature.setAttribute("start_node", node_equivalences[bus1])
#                 #******<Parametros esenciales***************
#                 load_feature.setAttribute("kv", str(loads.kV))
#                 load_feature.setAttribute("kw", str(loads.kW))
#                 load_feature.setAttribute("pf", str(loads.PF))
#                 #load_feature.setAttribute("status", str(loads.Status)) #Lo toma mal
#                 load_feature.setAttribute("model", str(loads.Model))
#                 load_feature.setAttribute("cvrwatts", str(loads.CVRwatts))
#                 load_feature.setAttribute("cvrvars", str(loads.CVRvars))
#                 load_feature.setAttribute("class", str(loads.Class))
#                 load_feature.setAttribute("daily", str(loads.daily))
#                 #******<Parametros esenciales no presentes en interfaz*****
#                 dss_instance.activar_elemento(f"Load.{load_name}")
#                 phases = dssCktElement.Properties("phases").Val
#                 load_feature.setAttribute("phases", phases)
#                 conn = dssCktElement.Properties("conn").Val
#                 load_feature.setAttribute("conn", conn)
#                 status = dssCktElement.Properties("status").Val
#                 load_feature.setAttribute("status", status)
#                 #******<Parametros adicionales**************
#                 #...
#                 #...
#                 #******>Parametros***************
#                 load_layer.addFeature(load_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()

#             if loads.Next == 0:
#                 break

#     load_layer.commitChanges()
#     print(f"Cantidad de cargas importadas: {len(load_layer)}")

#     # Importar capacitores
#     messageLabel.setText("Importando Capacitores...")
#     capacitor_layer.startEditing()

#     if Capacitors.First != 0:
#         while True:
#             capacitor_name = Capacitors.Name  # Obtener el nombre del capacitor actual
#             dss_instance.activar_elemento(f"Capacitor.{capacitor_name}")  # Activar el capacitor actual
#             barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

#             bus1 = barra1.split('.')[0]
#             bus1_feature = find_node_by_uuid(node_mt_layer, node_equivalences[bus1])

#             if bus1_feature:
#                 bus1_geom = bus1_feature.geometry().asPoint()
#                 new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else capacitor_name
#                 capacitor_equivalences[capacitor_name] = new_id
#                 capacitor_feature = QgsFeature(capacitor_layer.fields())
#                 capacitor_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
#                 capacitor_feature.setAttribute("id", new_id)
#                 capacitor_feature.setAttribute("start_node", node_equivalences[bus1])
#                 #******<Parametros esenciales***************
#                 capacitor_feature.setAttribute("kv", str(Capacitors.kV))
#                 capacitor_feature.setAttribute("kvar", str(Capacitors.kvar))
#                 #******<Parametros esenciales no presentes en interfaz*****
#                 dss_instance.activar_elemento(f"Capacitor.{capacitor_name}")
#                 phases = dssCktElement.Properties("phases").Val
#                 capacitor_feature.setAttribute("phases", phases)
#                 #******<Parametros adicionales**************
#                 #...
#                 #...
#                 #******>Parametros***************
#                 capacitor_layer.addFeature(capacitor_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()

#             if Capacitors.Next == 0:
#                 break

#     capacitor_layer.commitChanges()
#     print(f"Cantidad de capacitores importados: {len(capacitor_layer)}")

#     # Importar generadores
#     messageLabel.setText("Importando Generadores...")
#     generator_layer.startEditing()

#     if Generators.First != 0:
#         while True:
#             generator_name = Generators.Name  # Obtener el nombre del generador actual
#             dss_instance.activar_elemento(f"Generator.{generator_name}")  # Activar el generador actual
#             barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

#             bus1 = barra1.split('.')[0]
#             bus1_feature = find_node_by_uuid(node_mt_layer, node_equivalences[bus1])

#             if bus1_feature:
#                 bus1_geom = bus1_feature.geometry().asPoint()
#                 new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else generator_name
#                 generator_equivalences[generator_name] = new_id
#                 generator_feature = QgsFeature(generator_layer.fields())
#                 generator_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
#                 generator_feature.setAttribute("id", new_id)
#                 generator_feature.setAttribute("start_node", node_equivalences[bus1])
#                 #******<Parametros esenciales***************
#                 generator_feature.setAttribute("Phases", str(Generators.Phases))
#                 generator_feature.setAttribute("kV", str(Generators.kV))
#                 generator_feature.setAttribute("kW", str(Generators.kW))
#                 generator_feature.setAttribute("PF", str(Generators.PF))
#                 #******<Parametros esenciales no presentes en interfaz*****
#                 dss_instance.activar_elemento(f"Generator.{generator_name}")
#                 daily = dssCktElement.Properties("daily").Val
#                 generator_feature.setAttribute("daily", daily)
#                 #******<Parametros adicionales**************
#                 #...
#                 #...
#                 #******>Parametros***************
#                 generator_layer.addFeature(generator_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()

#             if Generators.Next == 0:
#                 break

#     generator_layer.commitChanges()
#     print(f"Cantidad de generadores importados: {len(generator_layer)}")

#     # Importar sistemas fotovoltaicos
#     messageLabel.setText("Importando Sistemas Fotovoltaicos...")
#     pv_system_layer.startEditing()

#     if PVSystems.First != 0:
#         while True:
#             pv_system_name = PVSystems.Name  # Obtener el nombre del sistema fotovoltaico actual
#             dss_instance.activar_elemento(f"PVSystem.{pv_system_name}")  # Activar el sistema fotovoltaico actual
#             barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

#             bus1 = barra1.split('.')[0]
#             bus1_feature = find_node_by_uuid(node_mt_layer, node_equivalences[bus1])

#             if bus1_feature:
#                 bus1_geom = bus1_feature.geometry().asPoint()
#                 new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else pv_system_name
#                 pv_system_equivalences[pv_system_name] = new_id
#                 pv_system_feature = QgsFeature(pv_system_layer.fields())
#                 pv_system_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
#                 pv_system_feature.setAttribute("id", new_id)
#                 pv_system_feature.setAttribute("start_node", node_equivalences[bus1])
#                 #******<Parametros esenciales***************
#                 pv_system_feature.setAttribute("Irradiance", str(PVSystems.Irradiance))
#                 pv_system_feature.setAttribute("Pmpp", str(PVSystems.Pmpp))
#                 #******<Parametros esenciales no presentes en interfaz*****
#                 dss_instance.activar_elemento(f"PVSystem.{pv_system_name}")
#                 phases = dssCktElement.Properties("phases").Val
#                 pv_system_feature.setAttribute("phases", phases)
#                 kv = dssCktElement.Properties("kv").Val
#                 pv_system_feature.setAttribute("kv", kv)
#                 temperature = dssCktElement.Properties("Temperature").Val
#                 pv_system_feature.setAttribute("Temperatur", temperature)  # Ojo que el atributo en Opendss es Temperature, pero qgis permite solo 10 caracteres
#                 kva = dssCktElement.Properties("kVA").Val
#                 pv_system_feature.setAttribute("kVA", kva)
#                 effcurve = dssCktElement.Properties("EffCurve").Val
#                 pv_system_feature.setAttribute("EffCurve", effcurve)
#                 daily = dssCktElement.Properties("daily").Val
#                 pv_system_feature.setAttribute("daily", daily)
#                 tdaily = dssCktElement.Properties("Tdaily").Val
#                 pv_system_feature.setAttribute("Tdaily", tdaily)
#                 #******<Parametros adicionales**************
#                 #...
#                 #...
#                 #******>Parametros***************
#                 pv_system_layer.addFeature(pv_system_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()

#             if PVSystems.Next == 0:
#                 break

#     pv_system_layer.commitChanges()
#     print(f"Cantidad de sistemas fotovoltaicos importados: {len(pv_system_layer)}")

#     # Importar interruptores
#     messageLabel.setText("Importando Relays...")
#     switch_layer.startEditing()

#     if relays.First != 0:
#         while True:
#             relay_name = relays.Name  # Obtener el nombre del relay actual
#             monitored_obj = relays.MonitoredObj  # Obtener el MonitoredObj
#             linea = monitored_obj.split(".")[1]
#             monitored_term = str(relays.MonitoredTerm)  # Obtener el MonitoredTerm

#             # Obtener la línea asociada al relay
#             line_feat = find_line_by_uuid(line_layer, line_equivalences[linea])
#             if line_feat:
#                 # Calcular la posición del interruptor en la línea
#                 switch_point = find_point_on_line(line_feat, monitored_term)
#                 if switch_point:
#                     new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else relay_name
#                     switch_equivalences[relay_name] = new_id
#                     switch_feature = QgsFeature(switch_layer.fields())
#                     switch_feature.setGeometry(switch_point)
#                     switch_feature.setAttribute("id", new_id)
#                     switch_feature.setAttribute("line", line_equivalences[linea])
#                     switch_feature.setAttribute("terminal", monitored_term)
#                     #******<Parametros esenciales no presentes en interfaz*****
#                     dss_instance.activar_elemento(f"Relay.{relay_name}")
#                     State = dssCktElement.Properties("State").Val
#                     switch_feature.setAttribute("State", State)
#                     #******<Parametros adicionales**************
#                     #...
#                     #...
#                     #******>Parametros***************
#                     switch_layer.addFeature(switch_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()

#             if relays.Next == 0:
#                 break

#     switch_layer.commitChanges()
#     print(f"Cantidad de relays importados: {len(switch_layer)}")

#     # Importar Vsources
#     messageLabel.setText("Importando Vsources...")
#     et_layer.startEditing()

#     if vsources.First != 0:
#         while True:
#             vsource_name = vsources.Name  # Obtener el nombre del Vsource actual
#             dss_instance.activar_elemento(f"Vsource.{vsource_name}")  # Activar el Vsource actual
#             barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

#             bus1 = barra1.split('.')[0]
#             bus1_feature = find_node_by_uuid(node_mt_layer, node_equivalences[bus1])

#             if bus1_feature:
#                 bus1_geom = bus1_feature.geometry().asPoint()
#                 new_id = str(uuid.uuid4()) if recodificar == QMessageBox.Yes else vsource_name
#                 et_equivalences[vsource_name] = new_id
#                 et_feature = QgsFeature(et_layer.fields())
#                 et_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
#                 et_feature.setAttribute("id", new_id)
#                 et_feature.setAttribute("start_node", node_equivalences[bus1])
#                 #******<Parametros esenciales***************
#                 et_feature.setAttribute("pu", str(vsources.pu))
#                 et_feature.setAttribute("basekv", str(vsources.BasekV))
#                 #******<Parametros esenciales no presentes en interfaz*****
#                 dss_instance.activar_elemento(f"Vsource.{vsource_name}")
#                 r1 = dssCktElement.Properties("r1").Val
#                 et_feature.setAttribute("r1", r1)
#                 r0 = dssCktElement.Properties("r0").Val
#                 et_feature.setAttribute("r0", r0 )
#                 x1 = dssCktElement.Properties("x1").Val
#                 et_feature.setAttribute("x1", x1 )
#                 x0 = dssCktElement.Properties("x0").Val
#                 et_feature.setAttribute("x0", x0 )
#                 #******<Parametros adicionales**************
#                 #...
#                 #...
#                 #******>Parametros***************
#                 et_layer.addFeature(et_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()

#             if vsources.Next == 0:
#                 break

#     et_layer.commitChanges()
#     print(f"Cantidad de Vsources importados: {len(et_layer)}")

#     # Finalización
#     iface.messageBar().clearWidgets()  # Limpiar la barra de mensajes

#     print("Importación desde OpenDSS completada.")






#************* VERSION DE IMPORTACION ORIGINAL *************

# def import_dss(node_mt_layer, line_layer, transformer_layer, generator_layer, pv_system_layer, et_layer, load_layer, switch_layer, capacitor_layer):
# #def import_dss(node_mt_layer, node_bt_layer, line_mt_layer, line_bt_layer, generator_layer, pv_system_layer, load_layer, switch_layer, transformer_layer, et_layer, seta_layer, capacitor_layer):
#     # Abrir un cuadro de diálogo para seleccionar el archivo DSS
#     options = QFileDialog.Options()
#     options |= QFileDialog.ReadOnly
#     dss_path, _ = QFileDialog.getOpenFileName(None, "Seleccionar archivo DSS", "", "Archivos DSS (*.dss);;Todos los archivos (*)", options=options)

#     if not dss_path:
#         print("No se seleccionó ningún archivo DSS.")
#         return
#     dss_instance = DSS(dss_path)

#     # Inicializar la barra de progreso
#     progressMessageBar = iface.messageBar().createMessage("Importando elementos DSS...")
#     progress = QProgressBar()
#     progress.setMaximum(100)  # Establecer el valor máximo según las etapas esperadas
#     progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
#     messageLabel = QLabel("Iniciando importación...")  # Inicializar con un mensaje
#     progressMessageBar.layout().addWidget(messageLabel)
#     progressMessageBar.layout().addWidget(progress)
#     iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)
#     progress_level = 0
    
#     dss_instance.compilar_DSS()
#     dss_instance.resolver_DSS_snapshot(1.0)

#     dssCktElement =  dss_instance.dssCktElement
#     nodes = dss_instance.dssCircuit.AllBusNames
#     lines = dss_instance.dssLines
#     transformers = dss_instance.dssTransformers
#     loads = dss_instance.dssLoads
#     relays = dss_instance.dssRelays
#     vsources = dss_instance.dssVsources
#     Capacitors = dss_instance.dssCapacitors
#     Generators = dss_instance.dssGenerators
#     PVSystems = dss_instance.dssPVSystems
#     Settings = dss_instance.dssSettings

#     node_count = len(nodes)
#     line_count = len(lines)
#     transformer_count = len(transformers)
#     load_count = loads.Count
#     relay_count = relays.Count
#     vsource_count = vsources.Count
#     capacitor_count = Capacitors.Count
#     generator_count = Generators.Count
#     pvsystem_count = PVSystems.Count
#     myVBases = Settings.VoltageBases

#     print(f"Cantidad de nodos en la red: {node_count}")
#     print(f"Cantidad de líneas en la red: {line_count}")
#     print(f"Cantidad de transformadores en la red: {transformer_count}")
#     print(f"Cantidad de cargas en la red: {load_count}")
#     print(f"Cantidad de relays en la red: {relay_count}")
#     print(f"Cantidad de Vsource en la red: {vsource_count}")
#     print(f"Cantidad de Capacitores en la red: {capacitor_count}")
#     print(f"Cantidad de Generadores en la red: {generator_count}")
#     print(f"Cantidad de PVSystems en la red: {pvsystem_count}")
#     print(f"Los Voltaje Base son: {myVBases}")


#     total_elements = node_count + line_count + transformer_count + load_count + relay_count + vsource_count + capacitor_count + generator_count + pvsystem_count
#     increment_per_element = 100 / total_elements
#     messageLabel.setText("Importando nodos...")
#     progress.setValue(int(progress_level))
#     QApplication.processEvents()
#     # Importar nodos MT
#     node_mt_layer.startEditing()
#     for node in nodes:
#         dss_instance.activar_barra(node)
#         x, y = dss_instance.dssBus.x, dss_instance.dssBus.y
#         if x != 0 and y != 0:
#             node_feature = QgsFeature(node_mt_layer.fields())
#             node_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
#             node_feature.setAttribute("id", node)
#             node_mt_layer.addFeature(node_feature)

#         progress_level += increment_per_element
#         progress.setValue(int(progress_level))
#         QApplication.processEvents()

#     node_mt_layer.commitChanges()
#     print(f"Cantidad de nodos importados: {len(node_mt_layer)}")


#     # Importar líneas MT
#     messageLabel.setText("Importando lineas...")
#     line_layer.startEditing()

#     if lines.First != 0:
#         while True:
#             line_name = lines.Name
#             bus1 = lines.Bus1.split('.')[0]
#             bus2 = lines.Bus2.split('.')[0]
#             bus1_feature = find_node_by_uuid(node_mt_layer, bus1)
#             bus2_feature = find_node_by_uuid(node_mt_layer, bus2)
#             if bus1_feature and bus2_feature:
#                 bus1_geom = bus1_feature.geometry().asPoint()
#                 bus2_geom = bus2_feature.geometry().asPoint()
#                 line_feature = QgsFeature(line_layer.fields())
#                 line_feature.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(bus1_geom), QgsPointXY(bus2_geom)]))
#                 line_feature.setAttribute("id", line_name)
#                 line_feature.setAttribute("start_node", bus1)
#                 line_feature.setAttribute("end_node", bus2)
#                 #******<Parametros esenciales***************
#                 line_feature.setAttribute("length", str(lines.Length))
#                 line_feature.setAttribute("units", str(lines.Units)) # Ocurre que viene en none porque no toma el atributo units=m en el .dss
#                 line_feature.setAttribute("r1", str(lines.R1))
#                 line_feature.setAttribute("r0", str(lines.R0))
#                 line_feature.setAttribute("x1", str(lines.X1))
#                 line_feature.setAttribute("x0", str(lines.X0))
#                 line_feature.setAttribute("c1", str(lines.C1))
#                 line_feature.setAttribute("c0", str(lines.C0))                
#                 line_feature.setAttribute("phases", str(lines.Phases))
#                 #line_feature.setAttribute("enabled", lines.Units)
#                 dss_instance.activar_elemento(f"Line.{line_name}")
#                 Enabled = dssCktElement.Properties("enabled").Val
#                 line_feature.setAttribute("enabled", Enabled)
#                 #******<Parametros adicionales**************
#                 #line_feature.setAttribute("rg", str(lines.Rg))
#                 #line_feature.setAttribute("rho", str(lines.Rho))
#                 #line_feature.setAttribute("seasonrating", str(lines.SeasonRating))
#                 #line_feature.setAttribute("xg", str(lines.Xg))
#                 #line_feature.setAttribute("linecode", str(lines.LineCode))
#                 #line_feature.setAttribute("geometry", str(lines.Geometry))
#                 #line_feature.setAttribute("spacing", str(lines.Spacing))
#                 #line_feature.setAttribute("normamps", str(lines.NormAmps))
#                 #******>Parametros***************
#                 line_layer.addFeature(line_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()

#             if lines.Next == 0:
#                 break

#     line_layer.commitChanges()    
#     print(f"Cantidad de líneas importadas: {len(line_layer)}")


#     # Importar transformadores
#     messageLabel.setText("Importando Transformadores...")
#     transformer_layer.startEditing()

#     if transformers.First != 0:
#         while True:
#             transformer_name = transformers.Name  # Obtener el nombre del transformador actual
#             dss_instance.activar_elemento(f"Transformer.{transformer_name}")  # Activar el transformador actual
#             barra1, barra2 = dss_instance.obtener_barras_elemento()  # Obtener los nombres de las barras conectadas

#             bus1 = barra1.split('.')[0]
#             bus2 = barra2.split('.')[0]
#             bus1_feature = find_node_by_uuid(node_mt_layer, bus1)

#             if bus1_feature:
#                 bus1_geom = bus1_feature.geometry().asPoint()      
#                 transformer_feature = QgsFeature(transformer_layer.fields())
#                 transformer_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
#                 transformer_feature.setAttribute("id", transformer_name)
#                 transformer_feature.setAttribute("wdg1_node", bus1)
#                 transformer_feature.setAttribute("wdg2_node", bus2)
#                 #******<Parametros esenciales***************
#                 transformers.Wdg = 2
#                 transformer_feature.setAttribute("kv2", str(transformers.kV))
#                 transformer_feature.setAttribute("kva2", str(transformers.kva))
#                 transformers.Wdg = 1
#                 transformer_feature.setAttribute("kv1", str(transformers.kV))
#                 transformer_feature.setAttribute("kva1", str(transformers.kva))            
#                 transformer_feature.setAttribute("xhl", str(transformers.xhl))
#                 #******<Parametros esenciales no presentes en interfaz*****
#                 dss_instance.activar_elemento(f"Transformer.{transformer_name}")
#                 phases = dssCktElement.Properties("phases").Val
#                 transformer_feature.setAttribute("phases", phases)
#                 percent_imag = dssCktElement.Properties("%imag").Val
#                 transformer_feature.setAttribute("%imag", percent_imag)
#                 percent_loadloss = dssCktElement.Properties("%loadloss").Val
#                 transformer_feature.setAttribute("%loadloss", percent_loadloss)
#                 percent_noloadloss = dssCktElement.Properties("%noloadloss").Val
#                 transformer_feature.setAttribute("%nloadloss", percent_noloadloss)
#                 conns = dssCktElement.Properties("conns").Val
#                 transformer_feature.setAttribute("conns", conns)
#                 ppm_antifloat = dssCktElement.Properties("ppm_antifloat").Val
#                 transformer_feature.setAttribute("ppm_afloat", ppm_antifloat)
#                 #******<Parametros adicionales**************
#                 #transformer_feature.setAttribute("coretype", transformers.CoreType)
#                 #transformer_feature.setAttribute("isdelta", transformers.IsDelta)      
#                 #transformer_feature.setAttribute("maxtap", transformers.MaxTap)
#                 #transformer_feature.setAttribute("mintap", transformers.MinTap)
#                 #transformer_feature.setAttribute("numtaps", transformers.NumTaps)          
#                 #transformer_feature.setAttribute("numwindings", transformers.NumWindings)
#                 #transformer_feature.setAttribute("r", transformers.R)
#                 #transformers.Wdg = 2
#                 #transformer_feature.setAttribute("rdcohms2", transformers.RdcOhms)
#                 #transformers.Wdg = 1
#                 #transformer_feature.setAttribute("rdcohms1", transformers.RdcOhms)
#                 #transformer_feature.setAttribute("rneut", transformers.Rneut)
#                 #transformer_feature.setAttribute("tap", transformers.Tap)
#                 #transformer_feature.setAttribute("xfrmcode", transformers.XfrmCode)  
#                 #transformer_feature.setAttribute("xht", transformers.Xht)
#                 #transformer_feature.setAttribute("xlt", transformers.Xlt)
#                 #transformer_feature.setAttribute("xneut", transformers.Xneut)
#                 #******>Parametros***************
#                 transformer_layer.addFeature(transformer_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()  

#             if transformers.Next == 0:
#                 break

#     transformer_layer.commitChanges()    
#     print(f"Cantidad de transformadores importados: {len(transformer_layer)}")


#     # Importar cargas
#     messageLabel.setText("Importando Cargas...")
#     load_layer.startEditing()

#     if loads.First != 0:
#         while True:
#             load_name = loads.Name  # Obtener el nombre de la carga actual
#             dss_instance.activar_elemento(f"Load.{load_name}")  # Activar la carga actual
#             barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

#             bus1 = barra1.split('.')[0]
#             bus1_feature = find_node_by_uuid(node_mt_layer, bus1)

#             if bus1_feature:
#                 bus1_geom = bus1_feature.geometry().asPoint()  
#                 load_feature = QgsFeature(load_layer.fields())
#                 load_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
#                 load_feature.setAttribute("id", load_name)
#                 load_feature.setAttribute("start_node", bus1)
#                 #******<Parametros esenciales***************
#                 load_feature.setAttribute("kv", str(loads.kV))
#                 load_feature.setAttribute("kw", str(loads.kW))
#                 load_feature.setAttribute("pf", str(loads.PF))
#                 #load_feature.setAttribute("status", str(loads.Status)) #Lo toma mal
#                 load_feature.setAttribute("model", str(loads.Model))
#                 load_feature.setAttribute("cvrwatts", str(loads.CVRwatts))
#                 load_feature.setAttribute("cvrvars", str(loads.CVRvars))
#                 load_feature.setAttribute("class", str(loads.Class))
#                 load_feature.setAttribute("daily", str(loads.daily))
#                 #******<Parametros esenciales no presentes en interfaz*****
#                 dss_instance.activar_elemento(f"Load.{load_name}")
#                 phases = dssCktElement.Properties("phases").Val
#                 load_feature.setAttribute("phases", phases)
#                 conn = dssCktElement.Properties("conn").Val
#                 load_feature.setAttribute("conn", conn)
#                 status = dssCktElement.Properties("status").Val
#                 load_feature.setAttribute("status", status)
#                 #******<Parametros adicionales**************
#                 #...
#                 #...
#                 #******>Parametros***************
#                 load_layer.addFeature(load_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()

#             if loads.Next == 0:
#                 break

#     load_layer.commitChanges()
#     print(f"Cantidad de cargas importadas: {len(load_layer)}")


#     # Importar capacitores
#     messageLabel.setText("Importando Capacitores...")
#     capacitor_layer.startEditing()

#     if Capacitors.First != 0:
#         while True:
#             capacitor_name = Capacitors.Name  # Obtener el nombre del capacitor actual
#             dss_instance.activar_elemento(f"Capacitor.{capacitor_name}")  # Activar el capacitor actual
#             barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

#             bus1 = barra1.split('.')[0]
#             bus1_feature = find_node_by_uuid(node_mt_layer, bus1)

#             if bus1_feature:
#                 bus1_geom = bus1_feature.geometry().asPoint()  
#                 capacitor_feature = QgsFeature(capacitor_layer.fields())
#                 capacitor_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
#                 capacitor_feature.setAttribute("id", capacitor_name)
#                 capacitor_feature.setAttribute("start_node", bus1)
#                 #******<Parametros esenciales***************
#                 capacitor_feature.setAttribute("kv", str(Capacitors.kV))
#                 capacitor_feature.setAttribute("kvar", str(Capacitors.kvar))
#                 #******<Parametros esenciales no presentes en interfaz*****
#                 dss_instance.activar_elemento(f"Capacitor.{capacitor_name}")
#                 phases = dssCktElement.Properties("phases").Val
#                 capacitor_feature.setAttribute("phases", phases)
#                 #******<Parametros adicionales**************
#                 #...
#                 #...
#                 #******>Parametros***************
#                 capacitor_layer.addFeature(capacitor_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()

#             if Capacitors.Next == 0:
#                 break

#     capacitor_layer.commitChanges()
#     print(f"Cantidad de capacitores importados: {len(capacitor_layer)}")


#     # Importar generadores
#     messageLabel.setText("Importando Generadores...")
#     generator_layer.startEditing()

#     if Generators.First != 0:
#         while True:
#             generator_name = Generators.Name  # Obtener el nombre del generador actual
#             dss_instance.activar_elemento(f"Generator.{generator_name}")  # Activar el generador actual
#             barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

#             bus1 = barra1.split('.')[0]
#             bus1_feature = find_node_by_uuid(node_mt_layer, bus1)

#             if bus1_feature:
#                 bus1_geom = bus1_feature.geometry().asPoint()  
#                 generator_feature = QgsFeature(generator_layer.fields())
#                 generator_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
#                 generator_feature.setAttribute("id", generator_name)
#                 generator_feature.setAttribute("start_node", bus1)
#                 #******<Parametros esenciales***************
#                 generator_feature.setAttribute("Phases", str(Generators.Phases))
#                 generator_feature.setAttribute("kV", str(Generators.kV))
#                 generator_feature.setAttribute("kW", str(Generators.kW))
#                 generator_feature.setAttribute("PF", str(Generators.PF))
#                 #******<Parametros esenciales no presentes en interfaz*****
#                 dss_instance.activar_elemento(f"Generator.{generator_name}")
#                 daily = dssCktElement.Properties("daily").Val
#                 generator_feature.setAttribute("daily", daily)
#                 #******<Parametros adicionales**************
#                 #...
#                 #...
#                 #******>Parametros***************
#                 generator_layer.addFeature(generator_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()

#             if Generators.Next == 0:
#                 break

#     generator_layer.commitChanges()
#     print(f"Cantidad de generadores importados: {len(generator_layer)}")


#     # Importar sistemas fotovoltaicos
#     messageLabel.setText("Importando Sistemas Fotovoltaicos...")
#     pv_system_layer.startEditing()

#     if PVSystems.First != 0:
#         while True:
#             pv_system_name = PVSystems.Name  # Obtener el nombre del sistema fotovoltaico actual
#             dss_instance.activar_elemento(f"PVSystem.{pv_system_name}")  # Activar el sistema fotovoltaico actual
#             barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

#             bus1 = barra1.split('.')[0]
#             bus1_feature = find_node_by_uuid(node_mt_layer, bus1)

#             if bus1_feature:
#                 bus1_geom = bus1_feature.geometry().asPoint()  
#                 pv_system_feature = QgsFeature(pv_system_layer.fields())
#                 pv_system_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
#                 pv_system_feature.setAttribute("id", pv_system_name)
#                 pv_system_feature.setAttribute("start_node", bus1)
#                 #******<Parametros esenciales***************
#                 pv_system_feature.setAttribute("Irradiance", str(PVSystems.Irradiance))
#                 pv_system_feature.setAttribute("Pmpp", str(PVSystems.Pmpp))
#                 #******<Parametros esenciales no presentes en interfaz*****
#                 dss_instance.activar_elemento(f"PVSystem.{pv_system_name}")
#                 phases = dssCktElement.Properties("phases").Val
#                 pv_system_feature.setAttribute("phases", phases)
#                 kv = dssCktElement.Properties("kv").Val
#                 pv_system_feature.setAttribute("kv", kv)
#                 temperature = dssCktElement.Properties("Temperature").Val
#                 pv_system_feature.setAttribute("Temperatur", temperature)  # Ojo que el atributo en Opendss es Temperature, pero qgis permite solo 10 caracteres
#                 kva = dssCktElement.Properties("kVA").Val
#                 pv_system_feature.setAttribute("kVA", kva)
#                 effcurve = dssCktElement.Properties("EffCurve").Val
#                 pv_system_feature.setAttribute("EffCurve", effcurve)
#                 daily = dssCktElement.Properties("daily").Val
#                 pv_system_feature.setAttribute("daily", daily)
#                 tdaily = dssCktElement.Properties("Tdaily").Val
#                 pv_system_feature.setAttribute("Tdaily", tdaily)
#                 #******<Parametros adicionales**************
#                 #...
#                 #...
#                 #******>Parametros***************
#                 pv_system_layer.addFeature(pv_system_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()

#             if PVSystems.Next == 0:
#                 break

#     pv_system_layer.commitChanges()
#     print(f"Cantidad de sistemas fotovoltaicos importados: {len(pv_system_layer)}")


#     # Importar interruptores
#     messageLabel.setText("Importando Relays...")
#     switch_layer.startEditing()

#     if relays.First != 0:
#         while True:
#             relay_name = relays.Name  # Obtener el nombre del relay actual
#             monitored_obj = relays.MonitoredObj  # Obtener el MonitoredObj
#             linea = monitored_obj.split(".")[1]
#             monitored_term = str(relays.MonitoredTerm)  # Obtener el MonitoredTerm

#             # Obtener la línea asociada al relay
#             line_feat = find_line_by_uuid(line_layer, linea)
#             if line_feat:
#                 # Calcular la posición del interruptor en la línea
#                 switch_point = find_point_on_line(line_feat, monitored_term)
#                 if switch_point:
#                     switch_feature = QgsFeature(switch_layer.fields())
#                     switch_feature.setGeometry(switch_point)
#                     switch_feature.setAttribute("id", relay_name)
#                     switch_feature.setAttribute("line", linea)
#                     switch_feature.setAttribute("terminal", monitored_term)
#                     #******<Parametros esenciales no presentes en interfaz*****
#                     dss_instance.activar_elemento(f"Relay.{relay_name}")
#                     State = dssCktElement.Properties("State").Val
#                     switch_feature.setAttribute("State", State)
#                     #******<Parametros adicionales**************
#                     #...
#                     #...
#                     #******>Parametros***************
#                     switch_layer.addFeature(switch_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()

#             if relays.Next == 0:
#                 break

#     switch_layer.commitChanges()
#     print(f"Cantidad de relays importados: {len(switch_layer)}")


#     # Importar Vsources
#     messageLabel.setText("Importando Vsources...")
#     et_layer.startEditing()

#     if vsources.First != 0:
#         while True:
#             vsource_name = vsources.Name  # Obtener el nombre del Vsource actual
#             dss_instance.activar_elemento(f"Vsource.{vsource_name}")  # Activar el Vsource actual
#             barra1 = dss_instance.obtener_barra_elemento()  # Obtener el nombre de la barra conectada

#             bus1 = barra1.split('.')[0]
#             bus1_feature = find_node_by_uuid(node_mt_layer, bus1)

#             if bus1_feature:
#                 bus1_geom = bus1_feature.geometry().asPoint()  
#                 et_feature = QgsFeature(et_layer.fields())
#                 et_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
#                 et_feature.setAttribute("id", vsource_name)
#                 et_feature.setAttribute("start_node", bus1)
#                 #******<Parametros esenciales***************
#                 et_feature.setAttribute("pu", str(vsources.pu))
#                 et_feature.setAttribute("basekv", str(vsources.BasekV))
#                 #******<Parametros esenciales no presentes en interfaz*****
#                 dss_instance.activar_elemento(f"Vsource.{vsource_name}")
#                 r1 = dssCktElement.Properties("r1").Val
#                 et_feature.setAttribute("r1", r1)
#                 r0 = dssCktElement.Properties("r0").Val
#                 et_feature.setAttribute("r0", r0 )
#                 x1 = dssCktElement.Properties("x1").Val
#                 et_feature.setAttribute("x1", x1 )
#                 x0 = dssCktElement.Properties("x0").Val
#                 et_feature.setAttribute("x0", x0 )
#                 #******<Parametros adicionales**************
#                 #...
#                 #...
#                 #******>Parametros***************
#                 et_layer.addFeature(et_feature)

#             progress_level += increment_per_element
#             progress.setValue(int(progress_level))
#             QApplication.processEvents()

#             if vsources.Next == 0:
#                 break

#     et_layer.commitChanges()
#     print(f"Cantidad de Vsources importados: {len(et_layer)}")


#     # Finalización
#     iface.messageBar().clearWidgets()  # Limpiar la barra de mensajes

#     print("Importación desde OpenDSS completada.")







def export_dss(node_mt_layer, line_layer, transformer_layer, generator_layer, pv_system_layer, et_layer, load_layer, switch_layer, capacitor_layer):
    # Abrir un cuadro de diálogo para seleccionar la ubicación del archivo master.dss
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    folder_path = QFileDialog.getExistingDirectory(None, "Seleccionar ubicación para guardar archivos DSS", "", options=options)

    if not folder_path:
        print("No se seleccionó ninguna ubicación.")
        return

    # Inicializar la barra de progreso
    progressMessageBar = iface.messageBar().createMessage("Exportando elementos DSS...")
    progress = QProgressBar()
    progress.setMaximum(100)  # Establecer el valor máximo según las etapas esperadas
    progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    messageLabel = QLabel("Iniciando exportación...")  # Inicializar con un mensaje
    progressMessageBar.layout().addWidget(messageLabel)
    progressMessageBar.layout().addWidget(progress)
    iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)
    progress_level = 0

    # Calcular el total de elementos a exportar
    total_elements = node_mt_layer.featureCount() + line_layer.featureCount() + transformer_layer.featureCount() + et_layer.featureCount() + load_layer.featureCount() + switch_layer.featureCount()

    total_elements = (node_mt_layer.featureCount() + line_layer.featureCount() + transformer_layer.featureCount() +
                      et_layer.featureCount() + load_layer.featureCount() + switch_layer.featureCount() +
                      capacitor_layer.featureCount() + pv_system_layer.featureCount() + generator_layer.featureCount())

    increment_per_element = 100 / total_elements

    # Crear el archivo master.dss
    master_dss_path = os.path.join(folder_path, "Master.dss")
    with open(master_dss_path, 'w') as master_file:
        master_file.write("Clear\n")
        master_file.write("Set DefaultBaseFrequency=50\n")
        master_file.write("Redirect Vsource.dss\n")
        #master_file.write("Redirect WireData.dss\n") #Comentar si el modelo no lo contempla
        master_file.write("Redirect Line.dss\n")
        #master_file.write("Redirect XfmrCode.dss\n") #Comentar si el modelo no lo contempla
        master_file.write("Redirect Transformer.dss\n")
        master_file.write("Redirect Switch.dss\n")
        master_file.write("Redirect LoadShape.dss\n")
        #master_file.write("Redirect TShape.dss\n") #Comentar si el modelo no lo contempla
        #master_file.write("Redirect XYcurve.dss\n") #Comentar si el modelo no lo contempla
        master_file.write("Redirect Load.dss\n")
        master_file.write("Redirect Capacitor.dss\n")
        master_file.write("Redirect PVSystem.dss\n")
        master_file.write("Redirect Generator.dss\n")
        master_file.write("Redirect Voltagebases.dss\n")
        master_file.write("Calcvoltagebases\n")
        master_file.write("set mode=Snapshot\n")
        master_file.write("solve\n")
        master_file.write("LatLongCoords Buscoords.csv\n")

    # Crear los archivos DSS para los distintos elementos eléctricos
    messageLabel.setText("Exportando Vsources...")
    create_vsource_dss(et_layer, folder_path, progress, progress_level, increment_per_element)
    messageLabel.setText("Exportando líneas...")
    create_line_dss(line_layer, folder_path, progress, progress_level, increment_per_element)
    messageLabel.setText("Exportando transformadores...")
    create_transformer_dss(transformer_layer, folder_path, progress, progress_level, increment_per_element)
    messageLabel.setText("Exportando cargas...")
    create_load_dss(load_layer, folder_path, progress, progress_level, increment_per_element)
    messageLabel.setText("Exportando interruptores...")
    create_switch_dss(switch_layer, folder_path, progress, progress_level, increment_per_element)
    messageLabel.setText("Exportando capacitores...")
    create_capacitor_dss(capacitor_layer, folder_path, progress, progress_level, increment_per_element)
    messageLabel.setText("Exportando sistemas fotovoltaicos...")
    create_pv_system_dss(pv_system_layer, folder_path, progress, progress_level, increment_per_element)
    messageLabel.setText("Exportando generadores...")
    create_generator_dss(generator_layer, folder_path, progress, progress_level, increment_per_element)
    messageLabel.setText("Exportando coordenadas de nodos...")
    create_buscoords_csv(node_mt_layer, folder_path, progress, progress_level, increment_per_element)

    iface.messageBar().clearWidgets()  # Limpiar la barra de mensajes
    print("Exportación a OpenDSS completada.")

def create_vsource_dss(et_layer, folder_path, progress, progress_level, increment_per_element):
    vsource_dss_path = os.path.join(folder_path, "Vsource.dss")
    with open(vsource_dss_path, 'w') as file:
        for feature in et_layer.getFeatures():
            id = feature["id"]
            start_node = feature["start_node"]
            pu = feature["pu"]
            basekv = feature["basekv"]
            r1 = feature["r1"]
            r0 = feature["r0"]
            x1 = feature["x1"]
            x0 = feature["x0"]
            file.write(f"New Circuit.{id} pu={pu} r1={r1} x1={x1} r0={r0} x0={x0} basekv={basekv} bus1={start_node}.1.2.3.0\n")
            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

def create_line_dss(line_layer, folder_path, progress, progress_level, increment_per_element):
    line_dss_path = os.path.join(folder_path, "Line.dss")
    with open(line_dss_path, 'w') as file:
        for feature in line_layer.getFeatures():
            id = feature["id"]
            start_node = feature["start_node"]
            end_node = feature["end_node"]
            length = feature["length"]
            units = feature["units"]
            r1 = feature["r1"]
            r0 = feature["r0"]
            x1 = feature["x1"]
            x0 = feature["x0"]
            c1 = feature["c1"]
            c0 = feature["c0"]
            phases = feature["phases"]
            enabled = feature["enabled"]
            file.write(f"New Line.{id} bus1={start_node} bus2={end_node} length={length} units={units} r1={r1} r0={r0} x1={x1} x0={x0} c1={c1} c0={c0} enabled={enabled} phases={phases}\n")
            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

def create_transformer_dss(transformer_layer, folder_path, progress, progress_level, increment_per_element):
    transformer_dss_path = os.path.join(folder_path, "Transformer.dss")
    with open(transformer_dss_path, 'w') as file:
        for feature in transformer_layer.getFeatures():
            id = feature["id"]
            wdg1_node = feature["wdg1_node"]
            wdg2_node = feature["wdg2_node"]
            phases = feature["phases"]
            kv1 = feature["kv1"]
            kva1 = feature["kva1"]
            kv2 = feature["kv2"]
            kva2 = feature["kva2"]
            xhl = feature["xhl"]
            percent_imag = feature["%imag"]
            percent_loadloss = feature["%loadloss"]
            percent_noloadloss = feature["%nloadloss"]
            conns = feature["conns"]
            ppm_antifloat = feature["ppm_afloat"]
            file.write(f"New Transformer.{id} phases={phases} wdg=1 bus={wdg1_node}.1.2.3 kv={kv1} kVA={kva1} wdg=2 bus={wdg2_node}.1.2.3 kv={kv2} kVA={kva2} %imag={percent_imag} %loadloss={percent_loadloss} %noloadloss={percent_noloadloss} XHL={xhl} conns={conns} ppm_antifloat={ppm_antifloat}\n")
            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

def create_load_dss(load_layer, folder_path, progress, progress_level, increment_per_element):
    load_dss_path = os.path.join(folder_path, "Load.dss")
    with open(load_dss_path, 'w') as file:
        for feature in load_layer.getFeatures():
            id = feature["id"]
            start_node = feature["start_node"]
            kv = feature["kv"]
            kw = feature["kw"]
            pf = feature["pf"]
            status = feature["status"]
            model = feature["model"]
            cvrwatts = feature["cvrwatts"]
            cvrvars = feature["cvrvars"]
            class_type = feature["class"]
            daily = feature["daily"]
            phases = feature["phases"]
            conn = feature["conn"]
            file.write(f"New Load.{id} phases={phases} bus1={start_node}.1.2.3.0 kv={kv} kw={kw} pf={pf} status={status} model={model} CVRwatts={cvrwatts} CVRvars={cvrvars} class={class_type} daily={daily} conn={conn}\n")
            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

def create_capacitor_dss(capacitor_layer, folder_path, progress, progress_level, increment_per_element):
    capacitor_dss_path = os.path.join(folder_path, "Capacitor.dss")
    with open(capacitor_dss_path, 'w') as file:
        for feature in capacitor_layer.getFeatures():
            id = feature["id"]
            start_node = feature["start_node"]
            kv = feature["kv"]
            kvar = feature["kvar"]
            phases = feature["phases"]
            file.write(f"New Capacitor.{id} bus1={start_node}.1.2.3 kv={kv} kvar={kvar} phases={phases}\n")
            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

def create_generator_dss(generator_layer, folder_path, progress, progress_level, increment_per_element):
    generator_dss_path = os.path.join(folder_path, "Generator.dss")
    with open(generator_dss_path, 'w') as file:
        for feature in generator_layer.getFeatures():
            id = feature["id"]
            start_node = feature["start_node"]
            phases = feature["Phases"]
            kv = feature["kV"]
            kw = feature["kW"]
            pf = feature["PF"]
            daily = feature["daily"]
            file.write(f"New Generator.{id} bus1={start_node}.1.2.3 phases={phases} kv={kv} kw={kw} pf={pf} daily={daily}\n")
            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

def create_pv_system_dss(pv_system_layer, folder_path, progress, progress_level, increment_per_element):
    pv_system_dss_path = os.path.join(folder_path, "PVSystem.dss")
    with open(pv_system_dss_path, 'w') as file:
        for feature in pv_system_layer.getFeatures():
            id = feature["id"]
            start_node = feature["start_node"]
            irradiance = feature["Irradiance"]
            pmpp = feature["Pmpp"]
            phases = feature["phases"]
            kv = feature["kv"]
            temperature = feature["Temperatur"]
            kva = feature["kVA"]
            effcurve = feature["EffCurve"]
            daily = feature["daily"]
            tdaily = feature["Tdaily"]
            file.write(f"New PVSystem.{id} bus1={start_node}.1.2.3 irradiance={irradiance} pmpp={pmpp} phases={phases} kv={kv} temperature={temperature} kva={kva} effcurve={effcurve} daily={daily} tdaily={tdaily}\n")
            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

def create_switch_dss(switch_layer, folder_path, progress, progress_level, increment_per_element):
    switch_dss_path = os.path.join(folder_path, "Switch.dss")
    with open(switch_dss_path, 'w') as file:
        for feature in switch_layer.getFeatures():
            id = feature["id"]
            line = feature["line"]
            terminal = feature["terminal"]
            state = feature["State"]
            file.write(f"New Relay.{id} MonitoredObj=Line.{line} MonitoredTerm={terminal} State={state}\n")
            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

def create_buscoords_csv(node_mt_layer, folder_path, progress, progress_level, increment_per_element):
    buscoords_csv_path = os.path.join(folder_path, "Buscoords.csv")
    with open(buscoords_csv_path, 'w') as file:
        for feature in node_mt_layer.getFeatures():
            node_id = feature["id"]
            geom = feature.geometry().asPoint()
            x, y = geom.x(), geom.y()
            file.write(f"{node_id},{y},{x}\n")
            progress_level += increment_per_element
            progress.setValue(int(progress_level))
            QApplication.processEvents()

# ********** Funciones para limpieza de capas *************

def clear_all_layers():
    clear_node_mt_layer()
    clear_node_bt_layer()
    clear_line_mt_layer()
    clear_line_bt_layer()
    clear_generator_layer()
    clear_pv_system_layer()
    clear_load_layer()
    clear_capacitor_layer()
    clear_switch_layer()
    clear_transformer_layer()
    clear_et_layer()
    clear_seta_layer()

def clear_node_mt_layer():
    node_mt_layer.startEditing()
    node_mt_layer.dataProvider().truncate()
    node_mt_layer.commitChanges()

def clear_node_bt_layer():
    node_bt_layer.startEditing()
    node_bt_layer.dataProvider().truncate()
    node_bt_layer.commitChanges()

def clear_line_mt_layer():
    line_mt_layer.startEditing()
    line_mt_layer.dataProvider().truncate()
    line_mt_layer.commitChanges()

def clear_line_bt_layer():
    line_bt_layer.startEditing()
    line_bt_layer.dataProvider().truncate()
    line_bt_layer.commitChanges()

def clear_generator_layer():
    generator_layer.startEditing()
    generator_layer.dataProvider().truncate()
    generator_layer.commitChanges()

def clear_pv_system_layer():
    pv_system_layer.startEditing()
    pv_system_layer.dataProvider().truncate()
    pv_system_layer.commitChanges()

def clear_load_layer():
    load_layer.startEditing()
    load_layer.dataProvider().truncate()
    load_layer.commitChanges()

def clear_capacitor_layer():
    capacitor_layer.startEditing()
    capacitor_layer.dataProvider().truncate()
    capacitor_layer.commitChanges()

def clear_switch_layer():
    switch_layer.startEditing()
    switch_layer.dataProvider().truncate()
    switch_layer.commitChanges()

def clear_transformer_layer():
    transformer_layer.startEditing()
    transformer_layer.dataProvider().truncate()
    transformer_layer.commitChanges()

def clear_et_layer():
    et_layer.startEditing()
    et_layer.dataProvider().truncate()
    et_layer.commitChanges()

def clear_seta_layer():
    seta_layer.startEditing()
    seta_layer.dataProvider().truncate()
    seta_layer.commitChanges()




# *************INICIO DEL PROGRAMA PRINCIPAL *********************
# Obtener la capa de nodos y la capa de líneas del proyecto
node_mt_layer_name = "nodos_mt"
node_bt_layer_name = "nodos_bt"
line_mt_layer_name = "lineas_mt"
line_bt_layer_name = "lineas_bt"
generator_layer_name = "generadores"
pv_system_layer_name = "sistemas_fotovoltaicos"
load_layer_name = "cargas"
capacitor_layer_name = "capacitores"
switch_layer_name = "interruptores"
transformer_layer_name = "transformadores"
et_layer_name = "estacion_transformadora"
seta_layer_name = "setas"

node_mt_layer = QgsProject.instance().mapLayersByName(node_mt_layer_name)[0]
node_bt_layer = QgsProject.instance().mapLayersByName(node_bt_layer_name)[0]
line_mt_layer = QgsProject.instance().mapLayersByName(line_mt_layer_name)[0]
line_bt_layer = QgsProject.instance().mapLayersByName(line_bt_layer_name)[0]
generator_layer = QgsProject.instance().mapLayersByName(generator_layer_name)[0]
pv_system_layer = QgsProject.instance().mapLayersByName(pv_system_layer_name)[0]
load_layer = QgsProject.instance().mapLayersByName(load_layer_name)[0]
capacitor_layer = QgsProject.instance().mapLayersByName(capacitor_layer_name)[0]
switch_layer = QgsProject.instance().mapLayersByName(switch_layer_name)[0]
transformer_layer = QgsProject.instance().mapLayersByName(transformer_layer_name)[0]
et_layer = QgsProject.instance().mapLayersByName(et_layer_name)[0]
seta_layer = QgsProject.instance().mapLayersByName(seta_layer_name)[0]


# Crear una instancia de la herramienta personalizada
custom_map_tool = CustomMapTool(iface.mapCanvas(), node_mt_layer, node_bt_layer, line_mt_layer, line_bt_layer, generator_layer, pv_system_layer, load_layer, switch_layer, transformer_layer, et_layer, seta_layer, capacitor_layer)
iface.mapCanvas().setMapTool(custom_map_tool)

# Crear una instancia de la clase y mostrar la caja de herramientas
custom_toolbar_panel = CustomToolbarPanel(custom_map_tool, node_mt_layer, node_bt_layer, line_mt_layer, line_bt_layer, generator_layer,pv_system_layer, load_layer, switch_layer, transformer_layer, et_layer, seta_layer, capacitor_layer)
custom_toolbar_panel.init_panel()

# Agregar la caja de herramientas a la barra de herramientas principal
iface.addToolBar(custom_toolbar_panel.toolbox)

