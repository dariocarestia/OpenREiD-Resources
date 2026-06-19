import os
import uuid
import shutil
import zipfile
import json
import time
import tempfile
from PyQt5.QtGui import QIcon, QCursor, QPixmap, QFont, QColor, QDoubleValidator
from PyQt5.QtWidgets import QToolBar, QToolButton, QButtonGroup, QAction, QActionGroup, QFileDialog, QComboBox, QDialog, QVBoxLayout, QDialogButtonBox, QMenu, QFormLayout, QLineEdit, QPushButton, QInputDialog, QHBoxLayout, QGroupBox, QRadioButton
from qgis.utils import iface
from qgis.PyQt.QtCore import QSize, Qt, QVariant, QTimer
from qgis.PyQt.QtWidgets import QProgressBar, QApplication, QLabel
from qgis.core import Qgis, QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsPoint, QgsSingleSymbolRenderer, QgsLineSymbol, QgsRectangle, QgsGeometry, QgsPointXY, QgsPalLayerSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling, QgsDistanceArea
from qgis.gui import QgsMapTool
#from math import radians, sin, cos, sqrt, atan2
import win32com.client
import math


# Variables de Estado Edición General:
estado_edicion = "Selec_None"  # puede ser cualquira de ["Selec_None", "Insertando", "Moviendo_Nodo"]
# Selec_None -> Estado Inicial
# Insertando -> Al hacer clic en un botón de la barra de herramientas
# Moviendo_Nodo -> clic en botón Selección -> clic sobre un nodo

estado_flujo_trabajo = None # puede ser cualquira de ["Seleccion", "Nodo", "Linea", "Interruptor", "Carga", "Generador"]

# Variables Estado Edición por Elemento:
estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
estado_seleccion_pvsystem = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["T_Selec", "T_Pre_Selec", "Selec_None"]
estado_seleccion_et = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]

def action_nueva():
    global current_doc_path, is_dirty
    from PyQt5.QtWidgets import QMessageBox, QFileDialog
    try:
        # Asegurar carpeta de trabajo limpia
        _ensure_workdirs()

        template_path = DEFAULT_TEMPLATE_PATH
        if not os.path.isfile(template_path):
            # pedir ubicación de la plantilla
            template_path, _ = QFileDialog.getOpenFileName(None, "Seleccionar plantilla .greid", "", "GeoREID (*.greid)")
            if not template_path:
                print("Operación cancelada (sin plantilla).")
                return

        # Descomprimir plantilla a WORKDIR
        _unzip_to(template_path, WORKDIR)

        # Abrir proyecto
        _open_project_from_workdir()

        # Reset estado documento
        current_doc_path = None
        is_dirty = False
        print("Nueva red inicializada desde plantilla.")
    except Exception as e:
        QMessageBox.critical(None, "GeoREID", f"Error al crear nueva red:\n{e}")

def action_abrir():
    global current_doc_path, is_dirty
    from PyQt5.QtWidgets import QMessageBox, QFileDialog
    path, _ = QFileDialog.getOpenFileName(None, "Abrir red GeoREID", "", "GeoREID (*.greid)")
    if not path:
        return
    try:
        _ensure_workdirs()
        _unzip_to(path, WORKDIR)

        # Validar que haya proyecto
        project_file = _find_project_file(WORKDIR)
        if not project_file:
            QMessageBox.critical(None, "GeoREID", "Documento inválido (.greid sin project_file ni red.qgz/red.qgs).")
            return

        _open_project_from_workdir(project_file)
        current_doc_path = path
        is_dirty = False
        print(f"Red abierta: {path}")
    except Exception as e:
        QMessageBox.critical(None, "GeoREID", f"Error al abrir red:\n{e}")

def action_guardar():
    global current_doc_path, is_dirty
    if current_doc_path is None:
        # si nunca fue guardado, actuar como Guardar como
        return action_guardar_como()
    try:
        _touch_modified(WORKDIR)
        _zip_dir(WORKDIR, current_doc_path)
        is_dirty = False
        print(f"Guardado: {current_doc_path}")
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "GeoREID", f"Error al guardar:\n{e}")

def action_guardar_como():
    global current_doc_path, is_dirty
    from PyQt5.QtWidgets import QFileDialog, QMessageBox
    path, _ = QFileDialog.getSaveFileName(None, "Guardar red como", "", "GeoREID (*.greid)")
    if not path:
        return
    if not path.lower().endswith(".greid"):
        path += ".greid"
    try:
        _touch_modified(WORKDIR)
        _zip_dir(WORKDIR, path)
        current_doc_path = path
        is_dirty = False
        print(f"Guardado como: {current_doc_path}")
    except Exception as e:
        QMessageBox.critical(None, "GeoREID", f"Error al guardar como:\n{e}")

# Funciones de utilidad para manejo de documentos .greid
def _ensure_workdirs():
    os.makedirs(BASE_WORKDIR, exist_ok=True)
    # Limpia el temp completamente antes de usar
    if os.path.isdir(WORKDIR):
        shutil.rmtree(WORKDIR)
    os.makedirs(WORKDIR, exist_ok=True)

def _unzip_to(zip_path, dst_dir):
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dst_dir)

def _zip_dir(src_dir, zip_path, exclude_exts=(".qgs~", ".qgd", ".aux.xml", ".lock", ".DS_Store", "thumbs.db")):
    tmp_zip = zip_path + ".tmp"
    if os.path.exists(tmp_zip):
        os.remove(tmp_zip)
    with zipfile.ZipFile(tmp_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(src_dir):
            # excluir autosaves si existieran
            dirs[:] = [d for d in dirs if d.lower() not in (".git", "__pycache__", "autosave")]
            for f in files:
                if f.lower().endswith(exclude_exts):
                    continue
                full = os.path.join(root, f)
                rel = os.path.relpath(full, src_dir)
                z.write(full, rel)
    # reemplazo atómico + backup
    if os.path.exists(zip_path):
        backup = zip_path + ".bak"
        try:
            if os.path.exists(backup): os.remove(backup)
            shutil.copy2(zip_path, backup)
        except Exception:
            pass
        os.replace(tmp_zip, zip_path)
    else:
        os.replace(tmp_zip, zip_path)

def _load_manifest(base_dir):
    man_path = os.path.join(base_dir, "manifest.json")
    if not os.path.isfile(man_path):
        return None
    try:
        with open(man_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _touch_modified(base_dir):
    man = _load_manifest(base_dir) or {}
    man["modified_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(base_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)

def _find_project_file(base_dir):
    """
    Retorna el nombre de archivo de proyecto a abrir desde el WORKDIR.
    Orden de preferencia:
    1) manifest.json -> project_file
    2) red.qgz
    3) red.qgs
    """
    man = _load_manifest(base_dir)
    if man and isinstance(man, dict):
        pf = man.get("project_file")
        if pf and os.path.isfile(os.path.join(base_dir, pf)):
            return pf
    # fallback comunes
    for pf in ("red.qgz", "red.qgs"):
        if os.path.isfile(os.path.join(base_dir, pf)):
            return pf
    return None

def _open_project_from_workdir(project_file=None):
    if project_file is None:
        project_file = _find_project_file(WORKDIR)
    if not project_file:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "GeoREID", "No se encontró un archivo de proyecto para abrir (red.qgz/red.qgs).")
        return
    proj_path = os.path.join(WORKDIR, project_file)
    prj = QgsProject.instance()
    prj.read(proj_path)
    prj.setHomePath(WORKDIR)  # rutas relativas coherentes

# Helper para buscar capas por nombre
def get_layer(name: str):
    lst = QgsProject.instance().mapLayersByName(name)
    return lst[0] if lst else None

def _safe_print_added_ids(added_list, label="Feature.id"):
    """
    added_list puede ser [] o una lista de QgsFeature o ints (IDs).
    Imprime de forma segura el primer id si está disponible.
    """
    if not added_list:
        print(f"{label}: <no devuelto por el provider>")
        return
    first = added_list[0]
    try:
        fid = first.id()  # QgsFeature
    except AttributeError:
        fid = first       # entero (id)
    print(f"{label}: {fid}")

# Verificación liviana de capas (sin crearlas)
def ensure_layers():
    missing = [n for n in REQUIRED_LAYERS if not get_layer(n)]
    ok = len(missing) == 0
    return ok, missing

# Inicialización de barra y herramientas bajo demanda
def init_toolbar_and_tools():
    ok, missing = ensure_layers()
    if not ok:
        QMessageBox.warning(None, "GeoREID", "Faltan capas requeridas:\n- " + "\n- ".join(missing))
        return False
    try:
        if 'CustomToolbarPanel' in globals():
            try:
                # Obtener referencias a las capas por nombre
                node_layer = get_layer("nodos")
                line_layer = get_layer("lineas")
                generator_layer = get_layer("generadores")
                pv_system_layer = get_layer("sistemas_fotovoltaicos")
                load_layer = get_layer("cargas")
                switch_layer = get_layer("interruptores")
                transformer_layer = get_layer("transformadores")
                et_layer = get_layer("estacion_transformadora")
                capacitor_layer = get_layer("capacitores")
                
                # Crear instancia del panel de herramientas
                panel = CustomToolbarPanel(
                    map_tool=None,  # Se configurará después
                    node_layer=node_layer,
                    line_layer=line_layer,
                    generator_layer=generator_layer,
                    pv_system_layer=pv_system_layer,
                    load_layer=load_layer,
                    switch_layer=switch_layer,
                    transformer_layer=transformer_layer,
                    et_layer=et_layer,
                    capacitor_layer=capacitor_layer
                )
                
                if hasattr(panel, "init_panel"):
                    panel.init_panel()
                    print("Panel de herramientas inicializado correctamente")
                return True
            except Exception as e:
                QMessageBox.critical(None, "GeoREID", f"Error al inicializar panel:\n{e}")
                return False
        return True
    except Exception as e:
        QMessageBox.critical(None, "GeoREID", f"Error al inicializar herramientas:\n{e}")
        return False

def on_project_loaded():
    try:
        ok = init_toolbar_and_tools()
        if ok:
            print("GeoREID: herramientas inicializadas.")
        return ok
    except Exception as e:
        QMessageBox.critical(None, "GeoREID", f"on_project_loaded error:\n{e}")
        return False

class StartDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GeoREID - Asistente de inicio")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Selecciona cómo querés iniciar:"))

        btns = QHBoxLayout()
        self.btn_new = QPushButton("Nueva Red")
        self.btn_open = QPushButton("Abrir")
        self.btn_use = QPushButton("Usar proyecto actual")
        btns.addWidget(self.btn_new)
        btns.addWidget(self.btn_open)
        btns.addWidget(self.btn_use)
        layout.addLayout(btns)

def bootstrap(iface):
    dlg = StartDialog(parent=iface.mainWindow())

    def _after_project_changes():
        QTimer.singleShot(0, on_project_loaded)

    def _do_new():
        try:
            action_nueva()
            _after_project_changes()
        except Exception as e:
            QMessageBox.critical(dlg, "GeoREID", f"Error en Nueva Red:\n{e}")
        finally:
            dlg.close()

    def _do_open():
        try:
            action_abrir()
            _after_project_changes()
        except Exception as e:
            QMessageBox.critical(dlg, "GeoREID", f"Error al Abrir:\n{e}")
        finally:
            dlg.close()

    def _do_use_current():
        try:
            on_project_loaded()
        except Exception as e:
            QMessageBox.critical(dlg, "GeoREID", f"Error al usar proyecto actual:\n{e}")
        finally:
            dlg.close()

    dlg.btn_new.clicked.connect(_do_new)
    dlg.btn_open.clicked.connect(_do_open)
    dlg.btn_use.clicked.connect(_do_use_current)

    dlg.exec_()

def resetear_estados_a_inicial():
    """
    Función para resetear todas las variables de estado al estado inicial de selección.
    Útil para limpiar el estado de la aplicación o reiniciar operaciones.
    """
    global estado_edicion, estado_flujo_trabajo
    global estado_seleccion_linea, estado_seleccion_nodo, estado_seleccion_generador
    global estado_seleccion_pvsystem, estado_seleccion_carga, estado_seleccion_capacitor
    global estado_seleccion_interruptor, estado_seleccion_transformador, estado_seleccion_et
    
    # Resetear variables de estado general al estado de selección
    estado_edicion = "Selec_None"
    estado_flujo_trabajo = "seleccion"
    
    # Resetear variables de estado por elemento
    estado_seleccion_linea = "Selec_None"
    estado_seleccion_nodo = "Selec_None"
    estado_seleccion_generador = "Selec_None"
    estado_seleccion_pvsystem = "Selec_None"
    estado_seleccion_carga = "Selec_None"
    estado_seleccion_capacitor = "Selec_None"
    estado_seleccion_interruptor = "Selec_None"
    estado_seleccion_transformador = "Selec_None"
    estado_seleccion_et = "Selec_None"
    
    # Resetear el botón de selección en la barra de herramientas
    try:
        # Buscar el botón de selección y marcarlo como presionado
        seleccion_btn = next((btn for btn in custom_toolbar_panel.tool_buttons 
                            if btn.objectName() == "seleccion"), None)
        if seleccion_btn:
            seleccion_btn.setChecked(True)
            # Desmarcar todos los demás botones
            for btn in custom_toolbar_panel.tool_buttons:
                if btn != seleccion_btn:
                    btn.setChecked(False)
        print("Botón de selección activado en la barra de herramientas")
    except Exception as e:
        print(f"Error al resetear botón de selección: {e}")
    
    # Restaurar el cursor inicial
    try:
        iface.mapCanvas().unsetCursor()
        print("Cursor restaurado al estado inicial")
    except Exception as e:
        print(f"Error al restaurar cursor: {e}")
    
    print("Estados reseteados al estado inicial de selección")

ubicacion_switch = 0.85 # Determina la ubicación en porcentaje de la longitud de línea del switch correspondiente al terminal 2

# Constantes para manejo de documentos .greid
HOME_DIR = os.path.expanduser("~")
BASE_WORKDIR = os.path.join(HOME_DIR, "GeoREID")
WORKDIR = os.path.join(BASE_WORKDIR, "temp")

# Plantilla por defecto: intenta usar template.greid dentro del "homePath" del proyecto.
# Si no existe, al ejecutar "Nueva" se pedirá localizarla.
DEFAULT_TEMPLATE_PATH = os.path.join(QgsProject.instance().homePath(), "template.greid")

current_doc_path = None   # Ruta del último .greid guardado/abierto
is_dirty = False          # Cambios sin guardar (quedará para conectar con eventos de edición)

# Lista de capas requeridas para el funcionamiento del plugin
REQUIRED_LAYERS = [
    # RED
    "nodos", "lineas", "cargas", "generadores", "sistemas_fotovoltaicos",
    "capacitores", "interruptores", "transformadores", "estacion_transformadora",
    # LIBRERIAS
    "linecode", "linegeometry", "linespacing", "wiredata",
    "loadshape", "tshape", "xycurve", "settings", "xfmrcode"
]

project_path = QgsProject.instance().homePath()


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
            self.dssLoadShapes = self.dssCircuit.LoadShapes
            self.dssLineCodes = self.dssCircuit.LineCodes


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

    def activar_barra(self, nombre_barra):
        self.dssCircuit.SetActiveBus(nombre_barra)
        return self.dssBus.Name

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

    def resolver_DSS_hourly(self, hour, multiplicador_carga):
        # 1. Modo diario
        self.dssText.Command = "Set Mode=Daily"
        # 2. Un único paso de cálculo
        self.dssText.Command = "Set Number=1"
        # 3. Hora y segundos exactos
        self.dssText.Command = f"Set Hour={hour}"
        self.dssText.Command = "Set Sec=0"
        # 4. (Control estático, igual que en snapshot)
        self.dssText.Command = "Set ControlMode=Static"
        # 5. Factor de carga
        self.dssSolution.LoadMult = multiplicador_carga
        # 6. Resolver sólo ese instante
        self.dssSolution.Solve()



class CustomToolbarPanel:
    def __init__(self, map_tool, node_layer, line_layer, generator_layer, pv_system_layer, load_layer, switch_layer, transformer_layer, et_layer, capacitor_layer):
        self.toolbox = None
        self.tool_buttons = []
        self.button_group = None
        self.map_tool = map_tool  # Referencia a la herramienta de mapa
        self.node_layer = node_layer  # Referencia a la capa de nodos
        self.line_layer = line_layer  # Referencia a la capa de lineas
        self.generator_layer = generator_layer  # Referencia a la capa de lineas
        self.pv_system_layer = pv_system_layer  # Referencia a la capa de sistemas fotovoltaicos
        self.load_layer = load_layer  # Referencia a la capa de cargas
        self.capacitor_layer = capacitor_layer  # Referencia a la capa de capacitores
        self.switch_layer = switch_layer  # Referencia a la capa de interruptores
        self.transformer_layer = transformer_layer  # Referencia a la capa de transformadores
        self.et_layer = et_layer  # Referencia a la capa de estacion_transformadora
        self.voltage_action_group = None  # Grupo de acciones para seleccionar el voltaje
        self.current_visualization_mode = "Flujo de potencia"  # Estado por defecto de visualización

    def init_panel(self):
        # Crear la caja de herramientas
        self.toolbox = QToolBar("OpenREiD")
        self.toolbox.setIconSize(QSize(50, 50))  # Ajustar el tamaño del ícono según sea necesario

        # Obtener la ruta del directorio de trabajo actual
        script_dir = project_path  
        iconos_dir = os.path.join(script_dir, "iconos")

        #print(f"Path a los archivos de iconos: {iconos_dir}")

        # Lista de nombres de botones
        #button_names = ["Seleccion","Estacion_transformadora","Nodo","Linea", "Interruptor","Carga","Generador","Transformador","seta"]
        button_names = [
            ("Archivo", "Menú de archivo"),
            ("Seleccion", "Seleccionar elementos en el mapa"),
            ("Estacion_transformadora", "Agregar una estación transformadora"),
            ("Nodo", "Agregar un nodo"),
            ("Linea", "Agregar una línea"),
            ("Interruptor", "Agregar un interruptor"),
            ("Carga", "Agregar una carga"),
            ("Capacitor", "Agregar un capacitor"),
            ("Generador", "Agregar un generador"),
            ("Sistema_fotovoltaico", "Agregar un sistema fotovoltaico"),
            ("Transformador", "Agregar un transformador"),
            ("Librerias", "Librerías de componentes"),
            ("DSS-import", "Importar desde dss"),
            ("DSS-export", "Exportar hacia dss"),
            ("Calcular", "Calcular"),
            ("Visualizar", "Cambiar visualización")
        ]
 
        # Agregar botones de opción a la caja de herramientas
        self.button_group = QButtonGroup()

        def create_handler(button_name, cursor_icon_path):
            def handler():
                if button_name.lower() == "archivo":
                    # Crear el menú desplegable de Archivo
                    menu = QMenu()
                    
                    # Acción para Nueva Red
                    nueva_action = menu.addAction("Nueva Red")
                    nueva_action.triggered.connect(lambda checked: action_nueva())
                    
                    # Acción para Abrir
                    abrir_action = menu.addAction("Abrir")
                    abrir_action.triggered.connect(lambda checked: action_abrir())
                    
                    # Acción para Guardar
                    guardar_action = menu.addAction("Guardar")
                    guardar_action.triggered.connect(lambda checked: action_guardar())
                    
                    # Acción para Guardar como
                    guardar_como_action = menu.addAction("Guardar como")
                    guardar_como_action.triggered.connect(lambda checked: action_guardar_como())
                    
                    # Mostrar el menú debajo del botón
                    button = next((btn for btn in self.tool_buttons if btn.objectName() == "archivo"), None)
                    if button:
                        menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))
                elif button_name.lower() == "librerias":
                    # Crear el menú desplegable
                    menu = QMenu()
                    
                    # Crear submenús para cada componente
                    components = {
                        "linecode": "Line Code",
                        "linegeometry": "Line Geometry",
                        "linespacing": "Line Spacing",
                        "wiredata": "Wire Data",
                        "loadshape": "Load Shape",
                        "tshape": "T Shape",
                        "xycurve": "XY Curve",
                        "xfmrcode": "XfmrCode",  # <-- Nueva entrada
                        "settings": "Settings"
                    }

                    # Para mantener el orden y ubicar xfmrcode antes de settings
                    ordered_keys = [
                        "linecode",
                        "linegeometry",
                        "linespacing",
                        "wiredata",
                        "loadshape",
                        "tshape",
                        "xycurve",
                        "xfmrcode",
                        "settings"
                    ]

                    for comp_name in ordered_keys:
                        comp_label = components[comp_name]
                        if comp_name == "settings":
                            # Para settings, crear una acción directa
                            settings_action = menu.addAction("Settings")
                            settings_action.triggered.connect(lambda checked: self.handle_library_action("settings", "edit"))
                        else:
                            # Para los demás componentes, mostrar submenú con Listar, Importar, Exportar y Crear
                            comp_menu = menu.addMenu(comp_label)
                            # --- LISTAR ---
                            list_action = comp_menu.addMenu("Listar")
                            list_action.aboutToShow.connect(lambda c=comp_name, m=list_action: self.show_list_library_items(c, m))
                            # --- IMPORTAR ---
                            import_action = comp_menu.addAction("Importar")
                            import_action.triggered.connect(lambda checked, c=comp_name: self.handle_library_action(c, "import"))
                            # --- EXPORTAR ---
                            export_action = comp_menu.addAction("Exportar")
                            export_action.triggered.connect(lambda checked, c=comp_name: self.handle_library_action(c, "export"))
                            # --- CREAR ---
                            create_action = comp_menu.addAction("Crear")
                            create_action.triggered.connect(lambda checked, c=comp_name: self.handle_library_action(c, "create"))
                    # Mostrar el menú debajo del botón
                    button = next((btn for btn in self.tool_buttons if btn.objectName() == "librerias"), None)
                    menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))
                elif button_name.lower() == "calcular":
                    # Crear el menú desplegable para los cálculos
                    menu = QMenu()
                    
                    # Acción para flujo de potencia instantáneo
                    snapshot_action = menu.addAction("Calcular flujo de potencia Instantáneo")
                    snapshot_action.triggered.connect(lambda checked: self.handle_powerflow_action("SNAPSHOT"))
                    
                    # Acción para flujo de potencia horario
                    hourly_action = menu.addAction("Calcular flujo de potencia Horario")
                    hourly_action.triggered.connect(lambda checked: self.handle_powerflow_action("HOURLY"))
                    
                    # Acción para borrar la red
                    clear_action = menu.addAction("Borrar Red")
                    clear_action.triggered.connect(lambda checked: clear_all_layers())

                    # Acción para resetear el flujo
                    reset_action = menu.addAction("Reset flujo")
                    reset_action.triggered.connect(lambda checked: reset_power_flow())

                    # TODO: añadir futuras opciones aquí
                    
                    # Mostrar el menú debajo del botón
                    button = next((btn for btn in self.tool_buttons if btn.objectName() == "calcular"), None)
                    if button:
                        menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))
                elif button_name.lower() == "visualizar":
                    # Crear el menú desplegable de visualización con opciones excluyentes
                    menu = QMenu()
                    action_group = QActionGroup(menu)
                    action_group.setExclusive(True)

                    opt1 = menu.addAction("Flujo de potencia")
                    opt1.setCheckable(True)
                    opt2 = menu.addAction("Niveles de Tensión")
                    opt2.setCheckable(True)

                    # Marcar la opción actual
                    if self.current_visualization_mode == "Flujo de potencia":
                        opt1.setChecked(True)
                    else:
                        opt2.setChecked(True)

                    action_group.addAction(opt1)
                    action_group.addAction(opt2)

                    opt1.triggered.connect(lambda checked: self.handle_visualization_action("Flujo de potencia"))
                    opt2.triggered.connect(lambda checked: self.handle_visualization_action("Niveles de Tensión"))

                    # Mostrar el menú debajo del botón "Visualizar"
                    button = next((btn for btn in self.tool_buttons if btn.objectName() == "visualizar"), None)
                    if button:
                        menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))
                    return
                else:
                    self.handle_button_click(button_name, cursor_icon_path)
            return handler

        for button_name, tooltip in button_names:
            # Manejo especial para el ícono del botón Archivo
            if button_name.lower() == "archivo":
                button_icon_path = os.path.join(iconos_dir, "mnu-archivo.png")
            else:
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

    def handle_button_click(self, button_name, cursor_icon_path):
        global estado_flujo_trabajo
        global estado_edicion
        # Desactivar cualquier herramienta de mapa activa
        iface.mapCanvas().setMapTool(None)
        # Reactivar la herramienta de mapa personalizada
        iface.mapCanvas().setMapTool(self.map_tool)
        
        # Cambiar el cursor al hacer clic en el botón
        if button_name.lower() == "archivo":
            # El botón Archivo no cambia el estado de edición, solo muestra el menú
            return
        elif button_name.lower() == "seleccion":
            estado_flujo_trabajo = "seleccion"
            estado_edicion = "Selec_None"
            iface.mapCanvas().unsetCursor()

        elif  button_name.lower() == "dss-import":
            estado_flujo_trabajo = "dss-import"
            estado_edicion = "Selec_None"
            iface.mapCanvas().unsetCursor()
            import_dss(self.map_tool.node_layer, self.map_tool.line_layer, self.map_tool.transformer_layer, self.map_tool.generator_layer, self.map_tool.pv_system_layer , self.map_tool.et_layer, self.map_tool.load_layer, self.map_tool.switch_layer, self.map_tool.capacitor_layer)
            
            # —— Zoom automático a la capa de nodos ——
            #from qgis.utils import iface
            # Busca la capa por nombre
            nodos_layers = QgsProject.instance().mapLayersByName("nodos")
            if nodos_layers:
                nodo_layer = nodos_layers[0]
                # Obtiene la extensión completa de la capa
                rect = nodo_layer.extent()
                # Aplica la extensión al canvas y refresca
                canvas = iface.mapCanvas()
                canvas.setExtent(rect)
                canvas.refresh()
    
        elif  button_name.lower() == "dss-export":
            estado_flujo_trabajo = "dss-export"
            estado_edicion = "Selec_None"
            iface.mapCanvas().unsetCursor()
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            folder_path = QFileDialog.getExistingDirectory(None, "Seleccionar ubicación para guardar archivos DSS", "", options=options)
            if not folder_path:
                print("No se seleccionó ninguna ubicación.")
                return
            export_dss_location(folder_path, self.map_tool.node_layer, self.map_tool.line_layer, self.map_tool.transformer_layer, self.map_tool.generator_layer, self.map_tool.pv_system_layer , self.map_tool.et_layer, self.map_tool.load_layer, self.map_tool.switch_layer, self.map_tool.capacitor_layer)


        else:
            estado_flujo_trabajo = button_name.lower()
            estado_edicion = "Insertando"
            cursor = QCursor(QPixmap(cursor_icon_path), 0, 0)
            iface.mapCanvas().setCursor(cursor)
        print(f"Botón {button_name} clicado - Estado del flujo de trabajo: {estado_flujo_trabajo}")

    def handle_powerflow_action(self, modo):
        """Maneja las acciones del menú de PowerFlow"""
        global estado_flujo_trabajo
        global estado_edicion
        
        estado_flujo_trabajo = "powerflow"
        estado_edicion = "Selec_None"
        iface.mapCanvas().unsetCursor()
        
        # Ejecutar el power flow con el modo especificado
        power_flow(
            self.node_layer, 
            self.line_layer, 
            self.load_layer,
            modo
        )
        
        # Volver al estado de selección después de ejecutar
        estado_flujo_trabajo = "seleccion"
        estado_edicion = "Selec_None"
        seleccion_btn = next((btn for btn in self.tool_buttons
                            if btn.objectName() == "seleccion"), None)
        if seleccion_btn:
            seleccion_btn.setChecked(True)
        
        print(f"PowerFlow ejecutado con modo: {modo}")

    def apply_styles(self, line_qml_path, node_qml_path, load_qml_path):
        """Carga estilos desde archivos .qml y refresca capas y leyenda"""
        try:
            if self.line_layer:
                self.line_layer.loadNamedStyle(line_qml_path)
            if self.node_layer:
                self.node_layer.loadNamedStyle(node_qml_path)
            if self.load_layer:
                self.load_layer.loadNamedStyle(load_qml_path)
        except Exception as exc:
            print(f"[Visualizar] Error al cargar estilos: {exc}")

        # Refrescar capas
        try:
            if self.line_layer:
                self.line_layer.triggerRepaint()
            if self.node_layer:
                self.node_layer.triggerRepaint()
            if self.load_layer:
                self.load_layer.triggerRepaint()
        except Exception:
            pass

        # Refrescar leyenda si está disponible
        try:
            if self.line_layer:
                iface.layerTreeView().refreshLayerSymbology(self.line_layer.id())
            if self.node_layer:
                iface.layerTreeView().refreshLayerSymbology(self.node_layer.id())
            if self.load_layer:
                iface.layerTreeView().refreshLayerSymbology(self.load_layer.id())
        except Exception:
            pass

    def handle_visualization_action(self, mode):
        """Cambia el modo de visualización y aplica estilos .qml a las capas."""
        # Persistir estado
        self.current_visualization_mode = mode

        # Determinar estilos por modo
        if mode == "Flujo de potencia":
            styles = {
                "line":  project_path + '/estilos/lineas_1.qml',
                "node":  project_path + '/estilos/nodos_1.qml',
                "load":  project_path + '/estilos/cargas_1.qml',
            }
        else:  # "Niveles de Tensión"
            styles = {
                "line":  project_path + '/estilos/lineas_2.qml',
                "node":  project_path + '/estilos/nodos_2.qml',
                "load":  project_path + '/estilos/cargas_2.qml',
            }

        # Aplicar estilos y refrescar
        self.apply_styles(styles["line"], styles["node"], styles["load"])

        print(f"[Visualizar] Modo activo: {mode}")

    def handle_library_action(self, component_type, action_type):
        """Maneja las acciones de importar, exportar o crear para los componentes de la librería"""
        if action_type == "edit" and component_type == "settings":
            # Obtener la capa de settings
            settings_layers = QgsProject.instance().mapLayersByName("settings")
            if settings_layers:
                layer = settings_layers[0]
                # Obtener el primer feature o crear uno nuevo si no existe
                features = list(layer.getFeatures())
                if features:
                    feature = features[0]
                else:
                    feature = QgsFeature(layer.fields())
                    feature.setAttribute("id", str(uuid.uuid4()))
                self.show_edit_settings_form(feature, layer)
        elif action_type == "import":
            # Llamar a la función de importación correspondiente
            if component_type == "linecode":
                file_path, _ = QFileDialog.getOpenFileName(None, "Seleccionar archivo LineCode", "", "DSS Files (*.dss)")
                if file_path:
                    linecode_layers = QgsProject.instance().mapLayersByName("linecode")
                    if linecode_layers:
                        importar_linecode(file_path, linecode_layers[0])
            elif component_type == "linegeometry":
                file_path, _ = QFileDialog.getOpenFileName(None, "Seleccionar archivo LineGeometry", "", "DSS Files (*.dss)")
                if file_path:
                    line_geometry_layers = QgsProject.instance().mapLayersByName("linegeometry")
                    if line_geometry_layers:
                        importar_linegeometry(file_path, line_geometry_layers[0])
            elif component_type == "linespacing":
                file_path, _ = QFileDialog.getOpenFileName(None, "Seleccionar archivo LineSpacing", "", "DSS Files (*.dss)")
                if file_path:
                    line_spacing_layers = QgsProject.instance().mapLayersByName("linespacing")
                    if line_spacing_layers:
                        importar_linespacing(file_path, line_spacing_layers[0])
            elif component_type == "wiredata":
                file_path, _ = QFileDialog.getOpenFileName(None, "Seleccionar archivo WireData", "", "DSS Files (*.dss)")
                if file_path:
                    wire_data_layers = QgsProject.instance().mapLayersByName("wiredata")
                    if wire_data_layers:
                        importar_wiredata(file_path, wire_data_layers[0])
            elif component_type == "loadshape":
                file_path, _ = QFileDialog.getOpenFileName(None, "Seleccionar archivo LoadShape", "", "DSS Files (*.dss)")
                if file_path:
                    loadshape_layers = QgsProject.instance().mapLayersByName("loadshape")
                    if loadshape_layers:
                        importar_loadshape(file_path, loadshape_layers[0])
            elif component_type == "tshape":
                file_path, _ = QFileDialog.getOpenFileName(None, "Seleccionar archivo TShape", "", "DSS Files (*.dss)")
                if file_path:
                    tshape_layers = QgsProject.instance().mapLayersByName("tshape")
                    if tshape_layers:
                        importar_tshape(file_path, tshape_layers[0])
            elif component_type == "xycurve":
                file_path, _ = QFileDialog.getOpenFileName(None, "Seleccionar archivo XYCurve", "", "DSS Files (*.dss)")
                if file_path:
                    xycurve_layers = QgsProject.instance().mapLayersByName("xycurve")
                    if xycurve_layers:
                        importar_xycurve(file_path, xycurve_layers[0])
            elif component_type == "xfmrcode":
                file_path, _ = QFileDialog.getOpenFileName(None, "Seleccionar archivo XfmrCode", "", "DSS Files (*.dss)")
                if file_path:
                    xfmrcode_layers = QgsProject.instance().mapLayersByName("xfmrcode")
                    if xfmrcode_layers:
                        importar_xfmrcode(file_path, xfmrcode_layers[0])
        elif action_type == "export":
            # Llamar a la función de exportación correspondiente
            output_dir = QFileDialog.getExistingDirectory(None, "Seleccionar directorio de salida")
            if output_dir:
                if component_type == "linecode":
                    linecode_layers = QgsProject.instance().mapLayersByName("linecode")
                    if linecode_layers:
                        create_linecode_dss(linecode_layers[0], output_dir)
                elif component_type == "linegeometry":
                    line_geometry_layers = QgsProject.instance().mapLayersByName("linegeometry")
                    if line_geometry_layers:
                        create_linegeometry_dss(line_geometry_layers[0], output_dir)
                elif component_type == "linespacing":
                    line_spacing_layers = QgsProject.instance().mapLayersByName("linespacing")
                    if line_spacing_layers:
                        create_linespacing_dss(line_spacing_layers[0], output_dir)
                elif component_type == "wiredata":
                    wire_data_layers = QgsProject.instance().mapLayersByName("wiredata")
                    if wire_data_layers:
                        create_wiredata_dss(wire_data_layers[0], output_dir)
                elif component_type == "loadshape":
                    loadshape_layers = QgsProject.instance().mapLayersByName("loadshape")
                    if loadshape_layers:
                        create_loadshape_dss(loadshape_layers[0], output_dir)
                elif component_type == "tshape":
                    tshape_layers = QgsProject.instance().mapLayersByName("tshape")
                    if tshape_layers:
                        create_tshape_dss(tshape_layers[0], output_dir)
                elif component_type == "xycurve":
                    xycurve_layers = QgsProject.instance().mapLayersByName("xycurve")
                    if xycurve_layers:
                        create_xycurve_dss(xycurve_layers[0], output_dir)
                elif component_type == "xfmrcode":
                    xfmrcode_layers = QgsProject.instance().mapLayersByName("xfmrcode")
                    if xfmrcode_layers:
                        create_xfmrcode_dss(xfmrcode_layers[0], output_dir)
        else:  # action_type == "create"
            # Mostrar formulario de creación
            self.show_create_library_form(component_type)

    def show_create_library_form(self, component_type):
        """Muestra el formulario para crear un nuevo registro en la librería"""
        dialog = QDialog()
        dialog.setWindowTitle(f"Crear {component_type}")
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.fields = {}
        # Obtener la capa correspondiente
        layer = QgsProject.instance().mapLayersByName(component_type)[0] if QgsProject.instance().mapLayersByName(component_type) else None        
        if layer:
            # Crear un nuevo feature
            feature = QgsFeature(layer.fields())            
            # Crear campos para cada atributo
            for field_name in layer.fields().names():
                if field_name == "id":
                    # Generar un nuevo UUID para el ID
                    line_edit = QLineEdit(str(uuid.uuid4()))
                    line_edit.setReadOnly(True)
                else:
                    line_edit = QLineEdit()
                self.fields[field_name] = line_edit
                form_layout.addRow(field_name, line_edit)

            layout.addLayout(form_layout)

            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(lambda: self.save_new_library_item(feature, layer, dialog))
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            dialog.setLayout(layout)
            dialog.exec_()

    def save_new_library_item(self, feature, layer, dialog):
        """Guarda el nuevo registro en la capa de la librería"""
        # Establecer los valores de los campos
        for field_name, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                value = widget.text()
                feature.setAttribute(field_name, None if value == "" else value)
        # Agregar el nuevo feature a la capa
        layer.startEditing()
        layer.addFeature(feature)
        layer.commitChanges()
        layer.triggerRepaint()
        dialog.accept()

    def show_edit_settings_form(self, feature, layer):
        """Muestra el formulario para editar los settings"""
        dialog = QDialog()
        dialog.setWindowTitle("Editar Settings")
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.fields = {}

        # Crear campos para cada atributo
        for field_name in layer.fields().names():
            field_value = feature.attribute(field_name)
            if field_name == "id":
                line_edit = QLineEdit(str(field_value))
                line_edit.setReadOnly(True)
            else:
                line_edit = QLineEdit(str(field_value) if field_value is not None else "")
            self.fields[field_name] = line_edit
            form_layout.addRow(field_name, line_edit)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_settings(feature, layer, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        dialog.exec_()

    def save_settings(self, feature, layer, dialog):
        """Guarda los cambios en los settings"""
        # Establecer los valores de los campos
        for field_name, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                value = widget.text()
                feature.setAttribute(field_name, None if value == "" else value)

        # Guardar los cambios
        layer.startEditing()
        if feature.id() == -1:  # Si es un nuevo feature
            layer.addFeature(feature)
        else:
            layer.updateFeature(feature)
        layer.commitChanges()
        layer.triggerRepaint()
        dialog.accept()

    def show_list_library_items(self, component_type, menu):
        """Llena el submenú con los ids de los objetos de la capa y conecta la edición"""
        menu.clear()
        layers = QgsProject.instance().mapLayersByName(component_type)
        layer = layers[0] if layers else None
        if layer:
            has_any = False
            for feat in layer.getFeatures():
                has_any = True
                item_id = str(feat["id"])
                action = menu.addAction(item_id)
                action.triggered.connect(lambda checked, f=feat, l=layer: self.show_edit_library_form(f, l))
            if not has_any:
                a = menu.addAction("(sin registros)")
                a.setEnabled(False)
        else:
            a = menu.addAction("(capa no encontrada)")
            a.setEnabled(False)

    def show_edit_library_form(self, feature, layer):
        """Muestra el formulario para editar un registro existente en la librería"""
        dialog = QDialog()
        dialog.setWindowTitle(f"Editar {layer.name()}")
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.fields = {}
        for field_name in layer.fields().names():
            field_value = feature.attribute(field_name)
            if field_name == "id":
                line_edit = QLineEdit(str(field_value))
                line_edit.setReadOnly(True)
            else:
                line_edit = QLineEdit(str(field_value) if field_value is not None else "")
            self.fields[field_name] = line_edit
            form_layout.addRow(field_name, line_edit)

        layout.addLayout(form_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        # Al confirmar la edición, llamamos a nuestro método save_edits local
        # En versiones anteriores se intentaba usar save_edits del mapa, pero
        # CustomToolbarPanel no define ese método, lo que provocaba un error.
        button_box.accepted.connect(lambda: self.save_edits(feature, layer, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        dialog.exec_()

    def save_edits(self, feature, layer, dialog):
        """
        Guarda los cambios en un registro de una capa de biblioteca.

        Este método recorre los widgets almacenados en ``self.fields`` (que se
        rellenan en ``show_edit_library_form``) y actualiza los atributos del
        ``feature`` correspondiente. A diferencia del método homónimo en
        ``CustomMapTool``, este método utiliza el diccionario ``self.fields``
        perteneciente a ``CustomToolbarPanel`` y actualiza el registro en la capa
        indicada. Si el valor de un campo es la cadena ``"NULL"``, se almacena
        ``None`` en el atributo correspondiente.

        Args:
            feature: El QgsFeature que se está editando.
            layer: La capa asociada al feature.
            dialog: El diálogo de edición que debe cerrarse una vez que se
                confirmen los cambios.
        """
        # Actualizar los atributos del feature en función de los widgets
        for field_name, widget in self.fields.items():
            if isinstance(widget, QComboBox):
                value = widget.currentText()
                # Interpretar "NULL" como None para limpiar el valor
                feature.setAttribute(field_name, None if value == "NULL" else value)
            elif isinstance(widget, QLineEdit):
                valor = widget.text()
                feature.setAttribute(field_name, None if valor == "NULL" else valor)

        # Iniciar edición y actualizar el feature en la capa
        layer.startEditing()
        # Si el feature no existe en la capa (id == -1), agregarlo
        # Si el feature no existe en la capa (id == -1), agregarlo; de lo contrario, actualizarlo
        if feature.id() == -1:
            layer.addFeature(feature)
        else:
            layer.updateFeature(feature)
        layer.commitChanges()
        layer.triggerRepaint()
        # Cerrar el diálogo
        dialog.accept()

# Esta clase maneja toda la lógica de edición gráfica de elementos de la red eléctrica
class CustomMapTool(QgsMapTool):
    def __init__(self, canvas, node_layer, line_layer, generator_layer, pv_system_layer, load_layer, switch_layer, transformer_layer, et_layer, capacitor_layer):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.active = False  # Agregar una variable para rastrear el estado de activación
        self.node_layer = node_layer  # Referencia a la capa de nodos
        self.line_layer = line_layer  # Referencia a la capa de lineas
        self.generator_layer = generator_layer  # Referencia a la capa de generadores
        self.pv_system_layer = pv_system_layer  # Referencia a la capa de sistemas fotovoltaicos
        self.load_layer = load_layer  # Referencia a la capa de cargas
        self.capacitor_layer = capacitor_layer  # Referencia a la capa de capacitores
        self.switch_layer = switch_layer  # Referencia a la capa de interruptores
        self.transformer_layer = transformer_layer  # Referencia a la capa de transformadores
        self.et_layer = et_layer  # Referencia a la capa de transformadores
        self.node_feature = None  # Inicializar la variable fuera del bloque condicional
        self.selected_node = None
        self.selected_node_pair = None
        self.selected_switch = None
        self.start_node = None
        self.end_node = None
        self.linked_line = None  # línea para asociar a un elemento de control
        self.linked_node = None  # Terminal asociado
        self.clonando = False  # Determina si se está clonando un elemento
        self.cloned_element = None  # id del elemento a clonar
        self.associated_lines = []  # Se utilizan tanto para el movimiento de un nodo como un nodo_bt 
        self.associated_nodes = [] # En realidad va a ser solo uno, es el nodo binculado por una seta
        self.associated_generators = [] #La restricción de ingreso no debe permitir mas de 1 elemento
        self.associated_pvsystems = [] #La restricción de ingreso no debe permitir mas de 1 elemento
        self.associated_loads = [] #La restricción de ingreso no debe permitir mas de 1 elemento
        self.associated_capacitors = [] #La restricción de ingreso no debe permitir mas de 1 elemento
        self.associated_switches = [] #La restricción de ingreso no debe permitir mas de 1 elemento
        self.associated_transformers = [] #La restricción de ingreso no debe permitir mas de 1 elemento
        self.associated_ets = [] #Debido a la forma de creación se asegura 1 solo elemento        


    def canvasPressEvent(self, event): #Este evento de dispara al presionar, no al hacer clic (presionar y soltar)
        print("canvasPressEvent")
        global estado_flujo_trabajo
        global estado_seleccion_linea
        global estado_seleccion_nodo
        global estado_seleccion_generador
        global estado_seleccion_pvsystem
        global estado_seleccion_carga
        global estado_seleccion_capacitor
        global estado_seleccion_interruptor
        global estado_seleccion_transformador
        global estado_seleccion_et
        global estado_edicion

        if event.button() == Qt.RightButton:
            print("Right button clicked")

            if estado_flujo_trabajo == "seleccion":
                capas_objetivo = {
                    "Carga": self.load_layer,
                    "Generador": self.generator_layer,
                    "FV": self.pv_system_layer,
                    "Capacitor": self.capacitor_layer,
                    "Transformador": self.transformer_layer,
                    "ET": self.et_layer,
                    "Nodo": self.node_layer
                }
                encontrados = find_nearest_objects_by_type(QgsPointXY(event.mapPoint()), capas_objetivo)
                if encontrados:
                    opciones = []
                    referencias = {}
                    for tipo, features in encontrados.items():
                        for feat in features:
                            id_ = feat["id"] if "id" in feat.fields().names() else feat.id()
                            etiqueta = f"{tipo} - ID: {id_}"
                            opciones.append(etiqueta)
                            referencias[etiqueta] = (tipo, feat)

                    seleccion, ok = QInputDialog.getItem(None, "Seleccionar elemento", "Elementos encontrados:", opciones, 0, False)
                    if ok and seleccion:
                        tipo, feat = referencias[seleccion]
                        print(f"Seleccionado: {tipo}, ID: {feat['id']}")
                        if tipo == "Carga":
                            menu = QMenu()
                            accion_editar = menu.addAction("Editar atributos")
                            accion_clonar = menu.addAction("Clonar Carga")
                            accion_eliminar = menu.addAction("Eliminar Carga")
                            menu.addSeparator()  # Agrega una línea separadora
                            accion_cancelar = menu.addAction("Cancelar")
                            accion_seleccionada = menu.exec_(QCursor.pos())
                            if accion_seleccionada == accion_editar:
                                self.show_edit_form_load(feat, self.load_layer)
                            elif accion_seleccionada == accion_clonar:
                                self.clonando = True
                                self.cloned_element = feat.attribute("id")
                                estado_flujo_trabajo = "carga"
                                estado_seleccion_carga = "Selec_None"
                                estado_edicion = "Insertando"
                                project_path = QgsProject.instance().homePath()
                                script_dir = project_path
                                iconos_dir = os.path.join(script_dir, "iconos")
                                cursor_icon_path = os.path.join(iconos_dir, f"carga.cur")
                                cursor = QCursor(QPixmap(cursor_icon_path), 0, 0)
                                iface.mapCanvas().setCursor(cursor)
                                print(f"Clonando carga: {self.cloned_element}")
                            elif accion_seleccionada == accion_eliminar:
                                self.load_layer.startEditing()
                                self.load_layer.deleteFeature(feat.id())
                                self.load_layer.commitChanges()
                                self.canvas.refresh()
                            # Si se selecciona cancelar o se cierra el menú, no se hace nada

                        elif tipo == "Generador":
                            menu = QMenu()
                            accion_editar = menu.addAction("Editar atributos")
                            accion_clonar = menu.addAction("Clonar Generador")
                            accion_eliminar = menu.addAction("Eliminar Generador")
                            menu.addSeparator()
                            accion_cancelar = menu.addAction("Cancelar")
                            accion_seleccionada = menu.exec_(QCursor.pos())
                            if accion_seleccionada == accion_editar:
                                self.show_edit_form_generator(feat)
                            elif accion_seleccionada == accion_clonar:
                                self.clonando = True
                                self.cloned_element = feat.attribute("id")
                                estado_flujo_trabajo = "generador"
                                estado_seleccion_generador = "Selec_None"
                                estado_edicion = "Insertando"
                                project_path = QgsProject.instance().homePath()
                                script_dir = project_path
                                iconos_dir = os.path.join(script_dir, "iconos")
                                cursor_icon_path = os.path.join(iconos_dir, f"generador.cur")
                                cursor = QCursor(QPixmap(cursor_icon_path), 0, 0)
                                iface.mapCanvas().setCursor(cursor)
                                print(f"Clonando generador: {self.cloned_element}")
                            elif accion_seleccionada == accion_eliminar:
                                self.generator_layer.startEditing()
                                self.generator_layer.deleteFeature(feat.id())
                                self.generator_layer.commitChanges()
                                self.canvas.refresh()
                            # Si se selecciona cancelar o se cierra el menú, no se hace nada
                        elif tipo == "FV":
                            menu = QMenu()
                            accion_editar = menu.addAction("Editar atributos")
                            accion_clonar = menu.addAction("Clonar Sistema Fotovoltaico")
                            accion_eliminar = menu.addAction("Eliminar Sistema Fotovoltaico")
                            menu.addSeparator()  # Agrega una línea separadora
                            accion_cancelar = menu.addAction("Cancelar")
                            accion_seleccionada = menu.exec_(QCursor.pos())
                            if accion_seleccionada == accion_editar:
                                self.show_edit_form_pv(feat, self.pv_system_layer)
                            elif accion_seleccionada == accion_clonar:
                                self.clonando = True
                                self.cloned_element = feat.attribute("id")
                                estado_flujo_trabajo = "sistema_fotovoltaico"
                                estado_seleccion_pvsystem = "Selec_None"
                                estado_edicion = "Insertando"
                                project_path = QgsProject.instance().homePath()
                                script_dir = project_path
                                iconos_dir = os.path.join(script_dir, "iconos")
                                cursor_icon_path = os.path.join(iconos_dir, f"sistema_fotovoltaico.cur")
                                cursor = QCursor(QPixmap(cursor_icon_path), 0, 0)
                                iface.mapCanvas().setCursor(cursor)
                                print(f"Clonando sistema fotovoltaico: {self.cloned_element}")
                            elif accion_seleccionada == accion_eliminar:
                                self.pv_system_layer.startEditing()
                                self.pv_system_layer.deleteFeature(feat.id())
                                self.pv_system_layer.commitChanges()
                                self.canvas.refresh()
                            # Si se selecciona cancelar o se cierra el menú, no se hace nada
                        elif tipo == "Capacitor":
                            menu = QMenu()
                            accion_editar = menu.addAction("Editar atributos")
                            accion_clonar = menu.addAction("Clonar Capacitor")
                            accion_eliminar = menu.addAction("Eliminar Capacitor")
                            menu.addSeparator()  # Agrega una línea separadora
                            accion_cancelar = menu.addAction("Cancelar")
                            accion_seleccionada = menu.exec_(QCursor.pos())
                            if accion_seleccionada == accion_editar:
                                self.show_edit_form_capacitor(feat)
                            elif accion_seleccionada == accion_clonar:
                                self.clonando = True
                                self.cloned_element = feat.attribute("id")
                                estado_flujo_trabajo = "capacitor"
                                estado_seleccion_capacitor = "Selec_None"
                                estado_edicion = "Insertando"
                                project_path = QgsProject.instance().homePath()
                                script_dir = project_path
                                iconos_dir = os.path.join(script_dir, "iconos")
                                cursor_icon_path = os.path.join(iconos_dir, f"capacitor.cur")
                                cursor = QCursor(QPixmap(cursor_icon_path), 0, 0)
                                iface.mapCanvas().setCursor(cursor)
                                print(f"Clonando capacitor: {self.cloned_element}")
                            elif accion_seleccionada == accion_eliminar:
                                self.capacitor_layer.startEditing()
                                self.capacitor_layer.deleteFeature(feat.id())
                                self.capacitor_layer.commitChanges()
                                self.canvas.refresh()
                            # Si se selecciona cancelar o se cierra el menú, no se hace nada

                        elif tipo == "Transformador":
                            menu = QMenu()
                            accion_editar = menu.addAction("Editar atributos")
                            accion_clonar = menu.addAction("Clonar Transformador")
                            accion_eliminar = menu.addAction("Eliminar Transformador")
                            menu.addSeparator()  # Agrega una línea separadora
                            accion_cancelar = menu.addAction("Cancelar")
                            accion_seleccionada = menu.exec_(QCursor.pos())
                            if accion_seleccionada == accion_editar:
                                self.show_edit_form_transformador(feat)
                            elif accion_seleccionada == accion_clonar:
                                self.clonando = True
                                self.cloned_element = feat.attribute("id")
                                estado_flujo_trabajo = "transformador"
                                estado_seleccion_transformador = "Selec_None"
                                estado_edicion = "Insertando"
                                project_path = QgsProject.instance().homePath()
                                script_dir = project_path
                                iconos_dir = os.path.join(script_dir, "iconos")
                                cursor_icon_path = os.path.join(iconos_dir, f"transformador.cur")
                                cursor = QCursor(QPixmap(cursor_icon_path), 0, 0)
                                iface.mapCanvas().setCursor(cursor)
                                print(f"Clonando transformador: {self.cloned_element}")
                            elif accion_seleccionada == accion_eliminar:
                                self.transformer_layer.startEditing()
                                self.transformer_layer.deleteFeature(feat.id())
                                self.transformer_layer.commitChanges()
                                self.canvas.refresh()

                        elif tipo == "ET":
                            menu = QMenu()
                            accion_editar = menu.addAction("Editar atributos")
                            accion_clonar = menu.addAction("Clonar Estación Transformadora")
                            accion_eliminar = menu.addAction("Eliminar Estación Transformadora")
                            menu.addSeparator()
                            accion_cancelar = menu.addAction("Cancelar")
                            accion_seleccionada = menu.exec_(QCursor.pos())

                            if accion_seleccionada == accion_editar:
                                self.show_edit_form_et(feat, self.et_layer)
                            elif accion_seleccionada == accion_clonar:
                                self.clonando = True
                                self.cloned_element = feat.attribute("id")
                                estado_flujo_trabajo = "estacion_transformadora"
                                estado_seleccion_et = "Selec_None"
                                estado_edicion = "Insertando"
                                project_path = QgsProject.instance().homePath()
                                script_dir = project_path
                                iconos_dir = os.path.join(script_dir, "iconos")
                                cursor_icon_path = os.path.join(iconos_dir, "estacion_transformadora.cur")
                                cursor = QCursor(QPixmap(cursor_icon_path), 0, 0)
                                iface.mapCanvas().setCursor(cursor)
                                print(f"Clonando ET: {self.cloned_element}")
                            elif accion_seleccionada == accion_eliminar:
                                self.et_layer.startEditing()
                                self.et_layer.deleteFeature(feat.id())
                                self.et_layer.commitChanges()
                                self.canvas.refresh()

                        elif tipo == "Nodo":
                            menu = QMenu()
                            accion_eliminar = menu.addAction("Eliminar Nodo")
                            menu.addSeparator()  # Agrega una línea separadora
                            accion_cancelar = menu.addAction("Cancelar")
                            accion_seleccionada = menu.exec_(QCursor.pos())
                            if accion_seleccionada == accion_eliminar:
                                self.node_layer.startEditing()
                                self.node_layer.deleteFeature(feat.id())
                                self.node_layer.commitChanges()
                                self.canvas.refresh()
                            # Si se selecciona cancelar o se cierra el menú, no se hace nada
                        else:
                            print("Tipo no reconocido")

                else:
                    # 2) Buscar interruptor cercano
                    self.selected_switch = find_nearest_switch_for_editing(
                        self.switch_layer,
                        QgsPointXY(event.mapPoint())
                    )

                    if self.selected_switch:
                        # ----- menú para interruptor -----
                        menu = QMenu()
                        accion_eliminar = menu.addAction("Eliminar Interruptor")
                        menu.addSeparator()
                        accion_cancelar = menu.addAction("Cancelar")
                        accion_seleccionada = menu.exec_(QCursor.pos())

                        if accion_seleccionada == accion_eliminar:
                            self.switch_layer.startEditing()
                            self.switch_layer.deleteFeature(self.selected_switch.id())
                            self.switch_layer.commitChanges()
                            self.canvas.refresh()
                        # si se elige "Cancelar", no hacer nada

                    else:
                        # 3) Si tampoco hay interruptor, buscar línea cercana
                        self.selected_line = find_nearest_line_for_editing(
                            self.line_layer,
                            QgsPointXY(event.mapPoint())
                        )

                        if self.selected_line:
                            # ----- menú para línea -----
                            menu = QMenu()
                            accion_editar   = menu.addAction("Editar atributos")
                            accion_clonar   = menu.addAction("Clonar línea")
                            accion_eliminar = menu.addAction("Eliminar línea")
                            menu.addSeparator()
                            accion_cancelar = menu.addAction("Cancelar")
                            accion_seleccionada = menu.exec_(QCursor.pos())

                            if accion_seleccionada == accion_editar:
                                self.show_edit_form_line(self.selected_line, self.line_layer)
                            elif accion_seleccionada == accion_clonar:
                                self.clonando = True
                                self.cloned_element = self.selected_line.attribute("id")                    
                                estado_flujo_trabajo = "linea"
                                estado_seleccion_linea = "Selec_None"
                                estado_edicion = "Insertando"
                                project_path = QgsProject.instance().homePath()
                                script_dir = project_path
                                iconos_dir = os.path.join(script_dir, "iconos")
                                cursor_icon_path = os.path.join(iconos_dir, f"linea.cur")
                                cursor = QCursor(QPixmap(cursor_icon_path), 0, 0)
                                iface.mapCanvas().setCursor(cursor)
                                print(f"Clonando línea: {self.cloned_element}")

                            elif accion_seleccionada == accion_eliminar:
                                self.line_layer.startEditing()
                                self.line_layer.deleteFeature(self.selected_line.id())
                                self.line_layer.commitChanges()
                                self.canvas.refresh()
            

            elif estado_flujo_trabajo in ["estacion_transformadora","nodo","linea","interruptor","carga","capacitor","generador","sistema_fotovoltaico","transformador"]:

                if getattr(self, 'clonando', False) and getattr(self, 'cloned_element', None):
                    self.clonando = False
                    self.cloned_element = None

                if estado_seleccion_linea == "N1_Selec":
                    estado_seleccion_linea = "Selec_None"
                    self.removeTempLineLayer()
                    self.line_layer.triggerRepaint()

                resetear_estados_a_inicial()


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
                estado_seleccion_et = "Selec_None"
                print("Seleccionando")

                self.selected_switch = find_nearest_switch_index(self.switch_layer, QgsPointXY(event.mapPoint()))
                
                if self.selected_switch:
                    print(f"Interruptor seleccionado: {self.selected_switch.id()}")
                    # Cambiar el estado del interruptor
                    current_state = self.selected_switch['State']  # Asegúrate de que el campo se llama 'State'
                    new_state = "closed" if current_state == "open" else "open"

                    # Iniciar edición si no está ya en modo de edición
                    if not self.switch_layer.isEditable():
                        self.switch_layer.startEditing()
                    
                    # Cambiar el valor del atributo
                    self.selected_switch.setAttribute('State', new_state)
                    
                    # Actualizar la característica
                    if self.switch_layer.updateFeature(self.selected_switch):
                        print(f"Estado del interruptor {self.selected_switch.id()} cambiado a {new_state}")
                    else:
                        print("Error al actualizar la característica del interruptor.")

                    # Confirmar los cambios
                    if not self.switch_layer.commitChanges():
                        print("Error al guardar los cambios en la capa de interruptores.")
                    else:
                        self.switch_layer.triggerRepaint()
                    
                    # Deseleccionar el interruptor
                    self.switch_layer.removeSelection()
                
                else:
                    self.selected_node = find_nearest_node_index(self.node_layer, QgsPointXY(event.mapPoint()))
                    
                    if self.selected_node:
                        estado_seleccion_nodo = "N_Selec"
                        print(f"Nodo seleccionado: {self.selected_node.id()}")
                        self.startNodes_Movement(self.selected_node.attribute("id"))
                        # Seleccionar el nodo encontrado
                        self.node_layer.selectByIds([self.selected_node.id()])
                        self.node_layer.triggerRepaint()
                        estado_edicion = "Moviendo_Nodo"


            elif estado_flujo_trabajo == "nodo":
                estado_seleccion_linea = "Selec_None" # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                estado_seleccion_pvsystem = "Selec_None"
                estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
                estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                estado_seleccion_et = "Selec_None"

                print("agregando nodo")
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
                        _safe_print_added_ids(new_feature_ids, "Feature.id")
                        self.node_layer.updateExtents()
                        self.node_layer.triggerRepaint()
                        # vuelve a crear el indice espacial para agregar el nodo recien insertado
                    else:
                        print("Error al agregar el nodo.")
                else:
                    print(f"Error: El campo '{field_name}' no existe en la capa de nodos.")

            elif estado_flujo_trabajo == "linea":
                estado_seleccion_nodo = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                estado_seleccion_generador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                estado_seleccion_pvsystem = "Selec_None"
                estado_seleccion_carga = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                estado_seleccion_capacitor = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                estado_seleccion_interruptor = "Selec_None"  # puede ser cualquira de ["L_Selec", "Selec_None"]
                estado_seleccion_transformador = "Selec_None"  # puede ser cualquira de ["N_Selec", "Selec_None"]
                estado_seleccion_et = "Selec_None"

                print("agregando linea")
                if estado_seleccion_linea == "Selec_None": # puede ser cualquira de ["N1_Selec", "N2_Selec", "Selec_None"]
                    #self.start_node = find_nearest_node(self.node_layer, QgsPoint(event.mapPoint()))
                    self.start_node = find_nearest_nodes_index(self.node_layer, QgsPointXY(event.mapPoint()))
                    if self.start_node:
                        estado_seleccion_linea = "N1_Selec"
                        self.createTempLineLayer()
                        print(f"Nodo de inicio ID: {self.start_node.id()}")
                    else:
                        print("Haga clic sobre el primer nodo")

                elif estado_seleccion_linea == "N1_Selec":
                    #self.end_node = find_nearest_node(self.node_layer, QgsPoint(event.mapPoint()))
                    self.end_node = find_nearest_nodes_index(self.node_layer, QgsPointXY(event.mapPoint()))
                    if self.end_node:
                        #estado_seleccion_linea = "Selec_None"                                                
                        #print(f"Nodo de fin ID: {self.end_node.id()}")
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

                            distance_calculator = QgsDistanceArea()
                            distance_calculator.setSourceCrs(self.line_layer.crs(), QgsProject.instance().transformContext())
                            distance_calculator.setEllipsoid('WGS84')  # opcional, mejora precisión
                            length_meters = distance_calculator.measureLength(line_geometry)
                            line_feature.setAttribute("length", str(round(length_meters, 2)))
                            line_feature.setAttribute("units", "4")  # valor fijo como texto

                            # Clonar atributos de la línea original si corresponde
                            if getattr(self, 'clonando', False) and getattr(self, 'cloned_element', None):
                                original_feat = find_line_by_uuid(self.line_layer, self.cloned_element)
                                if original_feat:
                                    # (2025-08-18) Se elimina el atributo 'enabled' de líneas: no clonar
                                    exclude_fields = ["id", "start_node", "end_node", "length", "units", "enabled"]
                                    for field in self.line_layer.fields():
                                        field_name = field.name()
                                        if field_name not in exclude_fields:
                                            try:
                                                value = original_feat.attribute(field_name)
                                                line_feature.setAttribute(field_name, value)
                                            except Exception as e:
                                                print(f"No se pudo clonar el campo {field_name}: {e}")
                                #self.clonando = False
                                #self.cloned_element = None

                            success, new_feature_ids = self.line_layer.dataProvider().addFeatures([line_feature])
                            if success:
                                estado_seleccion_linea = "Selec_None"
                                self.removeTempLineLayer()
                                print(f"Línea agregada con ID: {unique_line_id}")
                                # print(f"new_feature_ids: {new_feature_ids}")
                                _safe_print_added_ids(new_feature_ids, "Feature.id")
                                self.line_layer.updateExtents()
                                self.line_layer.triggerRepaint()
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
                estado_seleccion_et = "Selec_None"

                print("agregando generador")
                if estado_seleccion_generador == "Selec_None":
                    self.start_node = find_nearest_nodes_index(self.node_layer, QgsPointXY(event.mapPoint()))
                    if self.start_node:
                        #print(f"Nodo ID: {self.start_node.id()}")
                        start_point = QgsPointXY(self.start_node.geometry().asPoint())
                        unique_generator_id = str(uuid.uuid4())
                        field_names = ["id", "start_node"]
                        if all(field_name in self.generator_layer.fields().names() for field_name in field_names):
                            generator_feature = QgsFeature(self.generator_layer.fields())
                            generator_feature.setAttribute("id", unique_generator_id)
                            generator_feature.setAttribute("start_node", self.start_node.attribute("id"))

                            ### Aqui generador ###
                            # Clonar atributos del generador original si corresponde
                            if getattr(self, 'clonando', False) and getattr(self, 'cloned_element', None):
                                original_feat = None
                                for feature in self.generator_layer.getFeatures():
                                    if feature['id'] == self.cloned_element:
                                        original_feat = feature
                                        break
                                if original_feat:
                                    exclude_fields = ["id", "start_node"]
                                    for field in self.generator_layer.fields():
                                        field_name = field.name()
                                        if field_name not in exclude_fields:
                                            value = original_feat.attribute(field_name)
                                            generator_feature.setAttribute(field_name, value)

                            generator_geometry = QgsGeometry.fromPointXY(start_point)
                            generator_feature.setGeometry(generator_geometry)
                            success, new_feature_ids = self.generator_layer.dataProvider().addFeatures([generator_feature])
                            if success:
                                estado_seleccion_generador = "Selec_None"
                                print(f"Generador agregado con ID: {unique_generator_id}")
                                _safe_print_added_ids(new_feature_ids, "Feature.id")
                                self.generator_layer.updateExtents()
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
                estado_seleccion_et = "Selec_None"                    

                print("agregando sistema fotovoltaico")
                if estado_seleccion_pvsystem == "Selec_None":
                    self.start_node = find_nearest_nodes_index(self.node_layer, QgsPointXY(event.mapPoint()))
                    if self.start_node:
                        start_point = QgsPointXY(self.start_node.geometry().asPoint())
                        unique_pvsystem_id = str(uuid.uuid4())
                        field_names = ["id", "start_node"]
                        if all(field_name in self.pv_system_layer.fields().names() for field_name in field_names):
                            pvsystem_feature = QgsFeature(self.pv_system_layer.fields())
                            pvsystem_feature.setAttribute("id", unique_pvsystem_id)
                            pvsystem_feature.setAttribute("start_node", self.start_node.attribute("id"))

                            ### Aqui sistemas fotovoltaicos ###
                            # Clonar atributos del sistema fotovoltaico original si corresponde
                            if getattr(self, 'clonando', False) and getattr(self, 'cloned_element', None):
                                original_feat = None
                                for feature in self.pv_system_layer.getFeatures():
                                    if feature['id'] == self.cloned_element:
                                        original_feat = feature
                                        break
                                if original_feat:
                                    exclude_fields = ["id", "start_node"]
                                    for field in self.pv_system_layer.fields():
                                        field_name = field.name()
                                        if field_name not in exclude_fields:
                                            value = original_feat.attribute(field_name)
                                            pvsystem_feature.setAttribute(field_name, value)

                            pvsystem_geometry = QgsGeometry.fromPointXY(start_point)
                            pvsystem_feature.setGeometry(pvsystem_geometry)
                            success, new_feature_ids = self.pv_system_layer.dataProvider().addFeatures([pvsystem_feature])
                            if success:
                                estado_seleccion_pvsystem = "Selec_None"
                                print(f"Sistema fotovoltaico agregado con ID: {unique_pvsystem_id}")
                                _safe_print_added_ids(new_feature_ids, "Feature.id")
                                self.pv_system_layer.updateExtents()
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
                estado_seleccion_et = "Selec_None"

                print("agregando carga")
                if estado_seleccion_carga == "Selec_None":
                    self.start_node = find_nearest_nodes_index(self.node_layer, QgsPointXY(event.mapPoint()))
                    if self.start_node:
                        #print(f"Nodo ID: {self.start_node.id()}")
                        start_point = QgsPointXY(self.start_node.geometry().asPoint())
                        unique_load_id = str(uuid.uuid4())
                        field_names = ["id", "start_node"]
                        if all(field_name in self.load_layer.fields().names() for field_name in field_names):
                            load_feature = QgsFeature(self.load_layer.fields())
                            load_feature.setAttribute("id", unique_load_id)
                            load_feature.setAttribute("start_node", self.start_node.attribute("id"))

                            # Clonar atributos de la carga original si corresponde
                            if getattr(self, 'clonando', False) and getattr(self, 'cloned_element', None):
                                original_feat = None
                                for feature in self.load_layer.getFeatures():
                                    if feature['id'] == self.cloned_element:
                                        original_feat = feature
                                        break
                                if original_feat:
                                    exclude_fields = ["id", "start_node"]
                                    for field in self.load_layer.fields():
                                        field_name = field.name()
                                        if field_name not in exclude_fields:
                                            value = original_feat.attribute(field_name)
                                            load_feature.setAttribute(field_name, value)

                            load_geometry = QgsGeometry.fromPointXY(start_point)
                            load_feature.setGeometry(load_geometry)
                            success, new_feature_ids = self.load_layer.dataProvider().addFeatures([load_feature])
                            if success:
                                estado_seleccion_carga = "Selec_None"
                                print(f"Carga agregada con ID: {unique_load_id}")
                                _safe_print_added_ids(new_feature_ids, "Feature.id")
                                self.load_layer.updateExtents()
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
                estado_seleccion_et = "Selec_None"

                print("agregando capacitor")
                if estado_seleccion_capacitor == "Selec_None":
                    self.start_node = find_nearest_nodes_index(self.node_layer, QgsPointXY(event.mapPoint()))
                    if self.start_node:
                        start_point = QgsPointXY(self.start_node.geometry().asPoint())
                        unique_capacitor_id = str(uuid.uuid4())
                        field_names = ["id", "start_node"]
                        if all(field_name in self.capacitor_layer.fields().names() for field_name in field_names):
                            capacitor_feature = QgsFeature(self.capacitor_layer.fields())
                            capacitor_feature.setAttribute("id", unique_capacitor_id)
                            capacitor_feature.setAttribute("start_node", self.start_node.attribute("id"))

                            ### Aqui capacitores ###
                            # Clonar atributos del capacitor original si corresponde
                            if getattr(self, 'clonando', False) and getattr(self, 'cloned_element', None):
                                original_feat = None
                                for feature in self.capacitor_layer.getFeatures():
                                    if feature['id'] == self.cloned_element:
                                        original_feat = feature
                                        break
                                if original_feat:
                                    exclude_fields = ["id", "start_node"]
                                    for field in self.capacitor_layer.fields():
                                        field_name = field.name()
                                        if field_name not in exclude_fields:
                                            value = original_feat.attribute(field_name)
                                            capacitor_feature.setAttribute(field_name, value)

                            capacitor_geometry = QgsGeometry.fromPointXY(start_point)
                            capacitor_feature.setGeometry(capacitor_geometry)
                            success, new_feature_ids = self.capacitor_layer.dataProvider().addFeatures([capacitor_feature])
                            if success:
                                estado_seleccion_capacitor = "Selec_None"
                                print(f"Capacitor agregado con ID: {unique_capacitor_id}")
                                _safe_print_added_ids(new_feature_ids, "Feature.id")
                                self.capacitor_layer.updateExtents()
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
                estado_seleccion_et = "Selec_None"

                print("agregando interruptor")
                if estado_seleccion_interruptor == "Selec_None":
                    self.linked_line, terminal, point_on_line  = find_nearest_line_index(self.line_layer, self.node_layer, QgsPointXY(event.mapPoint()))
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
                            switch_feature.setAttribute("State", "closed")
                            switch_geometry = start_point
                            switch_feature.setGeometry(switch_geometry)
                            success, new_feature_ids = self.switch_layer.dataProvider().addFeatures([switch_feature])
                            if success:
                                estado_seleccion_interruptor = "Selec_None"
                                print(f"Interruptor agregado con ID: {unique_switch_id}")
                                _safe_print_added_ids(new_feature_ids, "Feature.id")
                                self.switch_layer.updateExtents()
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
                estado_seleccion_et = "Selec_None"

                print("agregando transformador")
                if estado_seleccion_transformador == "Selec_None":
                    self.start_node = find_nearest_node_index(self.node_layer, QgsPointXY(event.mapPoint()))
                    if self.start_node:

                        start_point = QgsPointXY(self.start_node.geometry().asPoint())

                        # *********Primero debo crear el nodo de media tensión<<<<<******************
                        unique_node_id = str(uuid.uuid4())
                        # Asegurarse de que el nombre del campo sea exactamente "id"
                        field_name = "id"
                        # Verificar si el campo existe en la capa de nodos
                        if field_name in self.node_layer.fields().names():
                            node_feature = QgsFeature(self.node_layer.fields())
                            node_feature.setAttribute(field_name, unique_node_id)
                            node_geometry = QgsGeometry.fromPointXY(start_point)
                            node_feature.setGeometry(node_geometry)
                            # Añadir la característica a la capa de nodos
                            success, new_feature_ids = self.node_layer.dataProvider().addFeatures([node_feature])
                            if success:
                                print(f"Nodo MT agregado con unique_node_id: {unique_node_id}")
                                # print(f"new_feature_ids: {new_feature_ids}")
                                _safe_print_added_ids(new_feature_ids, "Feature.id")
                                self.node_layer.updateExtents()
                                self.node_layer.triggerRepaint()
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

                            # Clonar atributos del transformador original si corresponde
                            if getattr(self, 'clonando', False) and getattr(self, 'cloned_element', None):
                                original_feat = None
                                for feature in self.transformer_layer.getFeatures():
                                    if feature['id'] == self.cloned_element:
                                        original_feat = feature
                                        break
                                if original_feat:
                                    exclude_fields = ["id", "wdg1_node", "wdg2_node"]
                                    for field in self.transformer_layer.fields():
                                        field_name = field.name()
                                        if field_name not in exclude_fields:
                                            value = original_feat.attribute(field_name)
                                            transformer_feature.setAttribute(field_name, value)

                            transformer_geometry = QgsGeometry.fromPointXY(start_point)
                            transformer_feature.setGeometry(transformer_geometry)
                            success, new_feature_ids = self.transformer_layer.dataProvider().addFeatures([transformer_feature])
                            if success:
                                estado_seleccion_transformador = "Selec_None"
                                print(f"Transformador agregado con ID: {unique_transformer_id}")
                                _safe_print_added_ids(new_feature_ids, "Feature.id")
                                self.transformer_layer.updateExtents()
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
                if field_name in self.node_layer.fields().names():
                    node_feature = QgsFeature(self.node_layer.fields())
                    node_feature.setAttribute(field_name, unique_node_id)
                    node_geometry = QgsGeometry.fromPointXY(QgsPointXY(event.mapPoint()))
                    node_feature.setGeometry(node_geometry)
                    success, new_feature_ids = self.node_layer.dataProvider().addFeatures([node_feature])
                    if success:
                        print(f"Nodo MT agregado con unique_node_id: {unique_node_id}")
                        _safe_print_added_ids(new_feature_ids, "Feature.id")
                        self.node_layer.updateExtents()
                        self.node_layer.triggerRepaint()
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
                    # --- Clonado de atributos (si corresponde) ---
                    if getattr(self, 'clonando', False) and getattr(self, 'cloned_element', None):
                        original_feat = None
                        for feature in self.et_layer.getFeatures():
                            if feature['id'] == self.cloned_element:
                                original_feat = feature
                                break
                        if original_feat:
                            exclude_fields = ["id", "start_node"]
                            for field in self.et_layer.fields():
                                field_name = field.name()
                                if field_name not in exclude_fields:
                                    try:
                                        value = original_feat.attribute(field_name)
                                        et_feature.setAttribute(field_name, value)
                                    except Exception as e:
                                        print(f"No se pudo clonar el campo {field_name}: {e}")
                        # limpiar flags de clonado
                        self.clonando = False
                        self.cloned_element = None
                    et_geometry = QgsGeometry.fromPointXY(QgsPointXY(event.mapPoint()))
                    et_feature.setGeometry(et_geometry)
                    success, new_feature_ids = self.et_layer.dataProvider().addFeatures([et_feature])
                    if success:
                        #estado_seleccion_et = "Selec_None"
                        print(f"estacion transformadora agregada con ID: {unique_et_id}")
                        _safe_print_added_ids(new_feature_ids, "Feature.id")
                        self.et_layer.updateExtents()
                        self.et_layer.triggerRepaint()
                    else:
                        print("Error al agregar la estacion transformadora.")
                else:
                    print("Error: Campos faltantes en la capa de estacion_transformadora.")



    def canvasMoveEvent(self, event):
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

        if estado_flujo_trabajo == "linea":
            if estado_seleccion_linea == "N1_Selec":
                self.redrawTempLineLayer(event)
            nearby_node = find_nearest_node_index(self.node_layer, QgsPointXY(event.mapPoint()))
            if nearby_node:
                print(f"Nodo cercano: {nearby_node.id()}")
                # Seleccionar el nodo encontrado
                self.node_layer.selectByIds([nearby_node.id()])
                self.node_layer.triggerRepaint()
            else:
                print("No se encontró un nodo cercano")
                self.node_layer.removeSelection()


        elif estado_flujo_trabajo == "generador":
            nearby_node = find_nearest_node_index(self.node_layer, QgsPointXY(event.mapPoint()))
            if nearby_node:
                print(f"Nodo cercano: {nearby_node.id()}")
                # Seleccionar el nodo encontrado
                self.node_layer.selectByIds([nearby_node.id()])
                self.node_layer.triggerRepaint()
            else:
                print("No se encontró un nodo cercano")
                self.node_layer.removeSelection()


        elif estado_flujo_trabajo == "sistema_fotovoltaico":
            nearby_node = find_nearest_node_index(self.node_layer, QgsPointXY(event.mapPoint()))
            if nearby_node:
                print(f"Nodo cercano: {nearby_node.id()}")
                # Seleccionar el nodo encontrado
                self.node_layer.selectByIds([nearby_node.id()])
                self.node_layer.triggerRepaint()
            else:
                print("No se encontró un nodo cercano")
                self.node_layer.removeSelection()


        elif estado_flujo_trabajo == "carga":
            nearby_node = find_nearest_node_index(self.node_layer, QgsPointXY(event.mapPoint()))
            if nearby_node:
                print(f"Nodo cercano: {nearby_node.id()}")
                # Seleccionar el nodo encontrado
                self.node_layer.selectByIds([nearby_node.id()])
                self.node_layer.triggerRepaint()
            else:
                print("No se encontró un nodo cercano")
                self.node_layer.removeSelection()


        elif estado_flujo_trabajo == "capacitor":
            nearby_node = find_nearest_node_index(self.node_layer, QgsPointXY(event.mapPoint()))
            if nearby_node:
                print(f"Nodo cercano: {nearby_node.id()}")
                self.node_layer.selectByIds([nearby_node.id()])
                self.node_layer.triggerRepaint()
            else:
                print("No se encontró un nodo cercano")
                self.node_layer.removeSelection()


        elif estado_flujo_trabajo == "interruptor":
            nearby_line, terminal, point_on_line = find_nearest_line_index(self.line_layer, self.node_layer, QgsPointXY(event.mapPoint()))
            
            if nearby_line:
                print(f"Línea cercana: {nearby_line.id()}, Terminal: {terminal}")
                self.line_layer.selectByIds([nearby_line.id()])
                self.line_layer.triggerRepaint()
            else:
                print("No se encontró una línea cercana")
                self.line_layer.removeSelection()  #FIJARSE SI SE ESTA ACCEDIENDO CORRECTAMENTE A LA CAPA


        elif estado_flujo_trabajo == "transformador":
            nearby_node = find_nearest_node_index(self.node_layer, QgsPointXY(event.mapPoint()))
            if nearby_node:
                print(f"Nodo cercano: {nearby_node.id()}")
                # Seleccionar el nodo encontrado
                self.node_layer.selectByIds([nearby_node.id()])
                self.node_layer.triggerRepaint()
            else:
                print("No se encontró un nodo cercano")
                self.node_layer.removeSelection()


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

            for node_feat in self.associated_nodes:
                updateNodeGeometry(self.node_layer, node_feat, clicked_point)
                moving_node_id = node_feat.attribute("id")

            for line_feat in self.associated_lines:
                self.updateLine_Geometry(line_feat)

            for switch_feat in self.associated_switches:
                self.updateSwitchGeometry(switch_feat)


    def canvasReleaseEvent(self, event):
        #print(f"canvasReleaseEvent:")
        global estado_edicion
        global estado_seleccion_nodo

        print("canvasReleaseEvent")
        print(f"Botón Liberado: {event.button()}")

        self.node_layer.removeSelection()
        #self.node_bt_layer.removeSelection()
        self.line_layer.removeSelection()
        #self.line_bt_layer.removeSelection()

        if estado_edicion == "Moviendo_Nodo":
            estado_edicion = "Selec_None"
            estado_seleccion_nodo = "Selec_None"
            # Finalizar la edición y guardar los cambios
            self.node_layer.commitChanges()
            self.line_layer.commitChanges()
            self.generator_layer.commitChanges()
            self.pv_system_layer.commitChanges()
            self.load_layer.commitChanges()
            self.capacitor_layer.commitChanges()
            self.switch_layer.commitChanges()
            self.transformer_layer.commitChanges()
            self.et_layer.commitChanges()
            self.selected_node = None
            self.associated_lines = []
            self.associated_nodes = [] 
            self.associated_generators = []
            self.associated_pvsystems = []
            self.associated_loads = []
            self.associated_capacitors = []
            self.associated_switches = []
            self.associated_transformers = []
            self.associated_ets = []

    def startNodes_Movement(self, node_id):
        print(f"startNodes_Movement:")        
        self.associated_nodes = []  # Esto es para mover los nodos de transformadores
        self.associated_lines = []
        self.associated_loads = []
        self.associated_capacitors = []
        self.associated_switches = []

        first_node = find_node_by_uuid(self.node_layer, node_id)
        if first_node:
            self.associated_nodes.append(first_node)

        self.associated_generators = [feat for feat in self.generator_layer.getFeatures() if feat['start_node'] == node_id]
        self.associated_pvsystems = [feat for feat in self.pv_system_layer.getFeatures() if feat['start_node'] == node_id]
        #self.associated_loads = [feat for feat in self.load_layer.getFeatures() if feat['start_node'] == node_id]
        self.associated_transformers = [feat for feat in self.transformer_layer.getFeatures() if feat['wdg1_node'] == node_id]
        self.associated_ets = [feat for feat in self.et_layer.getFeatures() if feat['start_node'] == node_id]

        for transformer_feat in self.associated_transformers:
            node_id = transformer_feat.attribute("wdg2_node")
            node_for_transformer = find_node_by_uuid(self.node_layer, node_id)
            if node_for_transformer:
                self.associated_nodes.append(node_for_transformer)
        
        for node_feat in self.associated_nodes:
            node_id = node_feat.attribute("id")

            lines_for_associated_node = [feat for feat in self.line_layer.getFeatures() if feat['start_node'] == node_id or feat['end_node'] == node_id]
            if lines_for_associated_node:
                self.associated_lines.extend(lines_for_associated_node)

            loads_for_associated_node = [feat for feat in self.load_layer.getFeatures() if feat['start_node'] == node_id]
            if loads_for_associated_node:
                self.associated_loads.extend(loads_for_associated_node)
            
            capacitors_for_associated_node = [feat for feat in self.capacitor_layer.getFeatures() if feat['start_node'] == node_id]
            if capacitors_for_associated_node:
                self.associated_capacitors.extend(capacitors_for_associated_node)

        for line_feat in self.associated_lines:
            line_id = line_feat.attribute("id")
            # Buscar interruptores asociados a la línea actual
            switches_for_line = [switch_feat for switch_feat in self.switch_layer.getFeatures() if switch_feat['line'] == line_id]
            self.associated_switches.extend(switches_for_line)            
      
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
        line_feat = find_line_by_uuid(self.line_layer, line_id)
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


    def updateLine_Geometry(self, line_feat):
        self.line_layer.startEditing()
        node1_feat = find_node_by_uuid(self.node_layer, line_feat['start_node'])
        node2_feat = find_node_by_uuid(self.node_layer, line_feat['end_node'])
        new_point_n1 = QgsPointXY(node1_feat.geometry().asPoint())
        new_point_n2 = QgsPointXY(node2_feat.geometry().asPoint())

        line_geom = line_feat.geometry()
        if line_geom.isMultipart():
            lines = line_geom.asMultiPolyline()
            for i in range(len(lines)):
                lines[i][0] = new_point_n1
                lines[i][-1] = new_point_n2
            new_geom = QgsGeometry.fromMultiPolylineXY(lines)
        else:
            line = line_geom.asPolyline()
            line[0] = new_point_n1
            line[-1] = new_point_n2
            new_geom = QgsGeometry.fromPolylineXY(line)

        self.line_layer.changeGeometry(line_feat.id(), new_geom)

        # Calcular nueva longitud precisa
        distance_calculator = QgsDistanceArea()
        distance_calculator.setSourceCrs(self.line_layer.crs(), QgsProject.instance().transformContext())
        distance_calculator.setEllipsoid('WGS84')
        length_meters = distance_calculator.measureLength(new_geom)
        self.line_layer.changeAttributeValue(line_feat.id(), self.line_layer.fields().indexFromName("length"), str(round(length_meters, 2)))

    def show_edit_form_generator(self, feature):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Generador")
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.fields = {}

        # Obtener capa de loadshape
        loadshape_layer = QgsProject.instance().mapLayersByName("loadshape")[0] if QgsProject.instance().mapLayersByName("loadshape") else None

        for field_name in feature.fields().names():
            field_value = feature.attribute(field_name)
            if field_name == "daily":
                combo = QComboBox()
                combo.addItem("NULL")
                if loadshape_layer:
                    ids = [feat["id"] for feat in loadshape_layer.getFeatures()]
                    combo.addItems(ids)
                if field_value is None:
                    combo.setCurrentIndex(combo.findText("NULL"))
                elif str(field_value) in [combo.itemText(i) for i in range(combo.count())]:
                    combo.setCurrentIndex(combo.findText(str(field_value)))
                self.fields[field_name] = combo
                form_layout.addRow("daily", combo)
            else:
                line_edit = QLineEdit(str(field_value) if field_value is not None else "")
                self.fields[field_name] = line_edit
                form_layout.addRow(field_name, line_edit)

        layout.addLayout(form_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_edits(feature, self.generator_layer, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        dialog.exec_()


    def show_edit_form_pv(self, element, layer):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Sistema Fotovoltaico")
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.fields = {}

        # Obtener capas necesarias
        loadshape_layer = QgsProject.instance().mapLayersByName("loadshape")[0] if QgsProject.instance().mapLayersByName("loadshape") else None
        xycurve_layer = QgsProject.instance().mapLayersByName("xycurve")[0] if QgsProject.instance().mapLayersByName("xycurve") else None
        tshape_layer = QgsProject.instance().mapLayersByName("tshape")[0] if QgsProject.instance().mapLayersByName("tshape") else None

        for field_name in element.fields().names():
            # (2025-08-18) Se elimina el atributo 'enabled' de líneas: no mostrar en formulario
            if field_name == "enabled":
                continue
            field_value = element.attribute(field_name)

            if field_name == "daily":
                combo = QComboBox()
                combo.addItem("NULL")
                if loadshape_layer:
                    ids = [feat["id"] for feat in loadshape_layer.getFeatures()]
                    combo.addItems(ids)
                if field_value is None:
                    combo.setCurrentIndex(combo.findText("NULL"))
                elif str(field_value) in [combo.itemText(i) for i in range(combo.count())]:
                    combo.setCurrentIndex(combo.findText(str(field_value)))
                self.fields[field_name] = combo
                form_layout.addRow("daily", combo)
            elif field_name == "EffCurve":
                combo = QComboBox()
                combo.addItem("NULL")
                if xycurve_layer:
                    ids = [feat["id"] for feat in xycurve_layer.getFeatures()]
                    combo.addItems(ids)
                if field_value is None:
                    combo.setCurrentIndex(combo.findText("NULL"))
                elif str(field_value) in [combo.itemText(i) for i in range(combo.count())]:
                    combo.setCurrentIndex(combo.findText(str(field_value)))
                self.fields[field_name] = combo
                form_layout.addRow("EffCurve", combo)
            elif field_name == "Tdaily":
                combo = QComboBox()
                combo.addItem("NULL")
                if tshape_layer:
                    ids = [feat["id"] for feat in tshape_layer.getFeatures()]
                    combo.addItems(ids)
                if field_value is None:
                    combo.setCurrentIndex(combo.findText("NULL"))
                elif str(field_value) in [combo.itemText(i) for i in range(combo.count())]:
                    combo.setCurrentIndex(combo.findText(str(field_value)))
                self.fields[field_name] = combo
                form_layout.addRow("Tdaily", combo)
            else:
                line_edit = QLineEdit(str(field_value) if field_value is not None else "")
                self.fields[field_name] = line_edit
                form_layout.addRow(field_name, line_edit)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_edits(element, layer, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        dialog.exec_()


    def show_edit_form_capacitor(self, feature):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Capacitor")
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.fields = {}

        for field_name in feature.fields().names():
            field_value = feature.attribute(field_name)
            line_edit = QLineEdit(str(field_value) if field_value is not None else "")
            self.fields[field_name] = line_edit
            form_layout.addRow(field_name, line_edit)

        layout.addLayout(form_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_edits(feature, self.capacitor_layer, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        dialog.exec_()


    def show_edit_form_transformador(self, feature):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Transformador")
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.fields = {}

        # Obtener capa de xfmrcode
        xfmrcode_layer = QgsProject.instance().mapLayersByName("xfmrcode")[0] if QgsProject.instance().mapLayersByName("xfmrcode") else None

        for field_name in feature.fields().names():
            field_value = feature.attribute(field_name)
            if field_name == "xfmrcode":
                combo = QComboBox()
                combo.addItem("NULL")
                if xfmrcode_layer:
                    ids = [feat["id"] for feat in xfmrcode_layer.getFeatures()]
                    combo.addItems(ids)
                if field_value is None or str(field_value) == "" or str(field_value).lower() == "null":
                    combo.setCurrentIndex(combo.findText("NULL"))
                elif str(field_value) in [combo.itemText(i) for i in range(combo.count())]:
                    combo.setCurrentIndex(combo.findText(str(field_value)))
                self.fields[field_name] = combo
                form_layout.addRow(field_name, combo)
            else:
                line_edit = QLineEdit(str(field_value) if field_value is not None else "")
                self.fields[field_name] = line_edit
                form_layout.addRow(field_name, line_edit)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_edits(feature, self.transformer_layer, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        dialog.exec_()


    def show_edit_form_et(self, element, layer):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Estación Transformadora")
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.fields = {}

        for field_name in element.fields().names():
            field_value = element.attribute(field_name)
            line_edit = QLineEdit(str(field_value) if field_value is not None else "")
            self.fields[field_name] = line_edit
            form_layout.addRow(field_name, line_edit)

        layout.addLayout(form_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_edits(element, layer, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        dialog.exec_()


    def show_edit_form_load(self, element, layer):
        dialog = QDialog()
        dialog.setWindowTitle("Editar Carga")
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.fields = {}

        # Obtener capa de loadshape
        loadshape_layer = QgsProject.instance().mapLayersByName("loadshape")[0] if QgsProject.instance().mapLayersByName("loadshape") else None

        for field_name in element.fields().names():
            field_value = element.attribute(field_name)

            if field_name == "daily":
                combo = QComboBox()
                combo.addItem("NULL")
                if loadshape_layer:
                    ids = [feat["id"] for feat in loadshape_layer.getFeatures()]
                    combo.addItems(ids)
                if field_value is None:
                    combo.setCurrentIndex(combo.findText("NULL"))
                elif str(field_value) in [combo.itemText(i) for i in range(combo.count())]:
                    combo.setCurrentIndex(combo.findText(str(field_value)))
                self.fields[field_name] = combo
                form_layout.addRow("daily", combo)
            else:
                line_edit = QLineEdit(str(field_value) if field_value is not None else "")
                self.fields[field_name] = line_edit
                form_layout.addRow(field_name, line_edit)

        layout.addLayout(form_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_edits(element, layer, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        dialog.exec_()


    def show_edit_form_line(self, element, layer):
        dialog = QDialog()
        dialog.setWindowTitle("Editar línea")
        layout = QVBoxLayout()
        
        # GroupBox de atributos generales (siempre visibles, arriba)
        self.gb_general = QGroupBox("Atributos Generales")
        general_layout = QFormLayout(self.gb_general)
        
        # Crear campos para atributos generales
        self.id_edit = QLineEdit()
        self.start_node_edit = QLineEdit()
        self.start_ph_edit = QLineEdit()
        self.end_node_edit = QLineEdit()
        self.end_ph_edit = QLineEdit()
        self.length_edit = QLineEdit()
        self.units_edit = QLineEdit()
        self.phases_edit = QLineEdit()
        
        # Aplicar validadores de números decimales a campos numéricos
        length_validator = QDoubleValidator()
        self.length_edit.setValidator(length_validator)
        self.length_edit.setPlaceholderText("0.0")
        
        # Agregar campos al layout de atributos generales
        general_layout.addRow("id", self.id_edit)
        general_layout.addRow("start_node", self.start_node_edit)
        general_layout.addRow("start_ph", self.start_ph_edit)
        general_layout.addRow("end_node", self.end_node_edit)
        general_layout.addRow("end_ph", self.end_ph_edit)
        general_layout.addRow("length(m)", self.length_edit)
        general_layout.addRow("units", self.units_edit)
        general_layout.addRow("phases", self.phases_edit)
        
        # Radio buttons for mode selection
        radios_layout = QHBoxLayout()
        self.rb_params = QRadioButton("Impedancias")
        self.rb_linecode = QRadioButton("LineCode")
        self.rb_geometry = QRadioButton("Geometry")
        
        self.button_group = QButtonGroup(dialog)
        self.button_group.addButton(self.rb_params)
        self.button_group.addButton(self.rb_linecode)
        self.button_group.addButton(self.rb_geometry)
        self.button_group.setExclusive(True)
        
        radios_layout.addWidget(self.rb_params)
        radios_layout.addWidget(self.rb_linecode)
        radios_layout.addWidget(self.rb_geometry)
        
        # Cargar capas auxiliares
        linegeometry_layer = QgsProject.instance().mapLayersByName("linegeometry")[0] if QgsProject.instance().mapLayersByName("linegeometry") else None
        linecode_layer = QgsProject.instance().mapLayersByName("linecode")[0] if QgsProject.instance().mapLayersByName("linecode") else None
        
        # GroupBox de impedancias
        self.gb_params = QGroupBox("Impedancias")
        params_layout = QFormLayout(self.gb_params)
        
        # Crear campos de impedancias
        self.r1_edit = QLineEdit()
        self.r0_edit = QLineEdit()
        self.x1_edit = QLineEdit()
        self.x0_edit = QLineEdit()
        self.c1_edit = QLineEdit()
        self.c0_edit = QLineEdit()
        
        # Aplicar validadores de números decimales
        dbl_validator = QDoubleValidator()
        for widget in [self.r1_edit, self.r0_edit, self.x1_edit, self.x0_edit, self.c1_edit, self.c0_edit]:
            widget.setValidator(dbl_validator)
            widget.setPlaceholderText("0.0")
        
        # Agregar campos al layout de impedancias
        params_layout.addRow("r1(Ω/m)", self.r1_edit)
        params_layout.addRow("r0(Ω/m)", self.r0_edit)
        params_layout.addRow("x1(Ω/m)", self.x1_edit)
        params_layout.addRow("x0(Ω/m)", self.x0_edit)
        params_layout.addRow("c1(nF/m)", self.c1_edit)
        params_layout.addRow("c0(nF/m)", self.c0_edit)
        
        # GroupBox de LineCode
        self.gb_linecode = QGroupBox("LineCode")
        lc_layout = QHBoxLayout(self.gb_linecode)
        self.cb_linecode = QComboBox()
        self.cb_linecode.addItem("NULL")
        if linecode_layer:
            ids = [feat["id"] for feat in linecode_layer.getFeatures()]
            self.cb_linecode.addItems(ids)
        lc_layout.addWidget(self.cb_linecode)
        
        # GroupBox de Geometry
        self.gb_geometry = QGroupBox("Geometry")
        geo_layout = QHBoxLayout(self.gb_geometry)
        self.cb_geometry = QComboBox()
        self.cb_geometry.addItem("NULL")
        if linegeometry_layer:
            ids = [feat["id"] for feat in linegeometry_layer.getFeatures()]
            self.cb_geometry.addItems(ids)
        geo_layout.addWidget(self.cb_geometry)
        
        # Agregar groupboxes al layout principal (orden: generales arriba, opciones abajo)
        layout.addWidget(self.gb_general)
        layout.addLayout(radios_layout)
        layout.addWidget(self.gb_params)
        layout.addWidget(self.gb_linecode)
        layout.addWidget(self.gb_geometry)
        
        # Botones de acción
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_line_edits(element, layer, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        # Cargar datos del feature
        self.load_line_from_feature(element)
        
        # Conectar señales
        self.rb_params.toggled.connect(self.update_line_mode)
        self.rb_linecode.toggled.connect(self.update_line_mode)
        self.rb_geometry.toggled.connect(self.update_line_mode)
        
        dialog.exec_()
    
    def update_line_mode(self):
        """Habilita/deshabilita grupos según el modo seleccionado"""
        use_params = self.rb_params.isChecked()
        use_linecode = self.rb_linecode.isChecked()
        use_geometry = self.rb_geometry.isChecked()
        
        # Habilitar/deshabilitar grupos
        self.gb_params.setEnabled(use_params)
        self.gb_linecode.setEnabled(use_linecode)
        self.gb_geometry.setEnabled(use_geometry)
        
        # Habilitar/deshabilitar widgets dentro de cada grupo
        for widget in [self.r1_edit, self.r0_edit, self.x1_edit, self.x0_edit, self.c1_edit, self.c0_edit]:
            widget.setEnabled(use_params)
        
        self.cb_linecode.setEnabled(use_linecode)
        self.cb_geometry.setEnabled(use_geometry)
    
    def load_line_from_feature(self, element):
        """Carga datos del feature en los widgets del formulario"""
        # Cargar parámetros eléctricos
        for field_name, widget in [("r1", self.r1_edit), ("r0", self.r0_edit),
                                 ("x1", self.x1_edit), ("x0", self.x0_edit),
                                 ("c1", self.c1_edit), ("c0", self.c0_edit)]:
            if field_name in element.fields().names():
                value = element.attribute(field_name)
                widget.setText(str(value) if value is not None else "")
        
        # Cargar linecode
        if "linecode" in element.fields().names():
            linecode_value = element.attribute("linecode")
            if linecode_value is not None:
                index = self.cb_linecode.findText(str(linecode_value))
                if index >= 0:
                    self.cb_linecode.setCurrentIndex(index)
                else:
                    self.cb_linecode.setEditText(str(linecode_value))
        
        # Cargar geometry
        if "geometry" in element.fields().names():
            geometry_value = element.attribute("geometry")
            if geometry_value is not None:
                index = self.cb_geometry.findText(str(geometry_value))
                if index >= 0:
                    self.cb_geometry.setCurrentIndex(index)
                else:
                    self.cb_geometry.setEditText(str(geometry_value))
        
        # Cargar atributos generales (siempre visibles)
        for field_name, widget in [("id", self.id_edit), ("start_node", self.start_node_edit),
                                 ("start_ph", self.start_ph_edit), ("end_node", self.end_node_edit),
                                 ("end_ph", self.end_ph_edit), ("length", self.length_edit),
                                 ("units", self.units_edit), ("phases", self.phases_edit)]:
            if field_name in element.fields().names():
                value = element.attribute(field_name)
                widget.setText(str(value) if value is not None else "")
        
        # Determinar modo inicial
        linecode = element.attribute("linecode") if "linecode" in element.fields().names() else None
        geometry = element.attribute("geometry") if "geometry" in element.fields().names() else None
        
        if geometry not in (None, "", "NULL"):
            self.rb_geometry.setChecked(True)
        elif linecode not in (None, "", "NULL"):
            self.rb_linecode.setChecked(True)
        else:
            self.rb_params.setChecked(True)
        
        # Aplicar modo inicial
        self.update_line_mode()
    
    def save_line_edits(self, element, layer, dialog):
        """Guarda los cambios del formulario de línea en el feature"""
        if self.rb_params.isChecked():
            # Guardar parámetros eléctricos
            for field_name, widget in [("r1", self.r1_edit), ("r0", self.r0_edit),
                                     ("x1", self.x1_edit), ("x0", self.x0_edit),
                                     ("c1", self.c1_edit), ("c0", self.c0_edit)]:
                if field_name in element.fields().names():
                    text = widget.text().strip()
                    try:
                        value = float(text) if text != "" else None
                        element.setAttribute(field_name, value)
                    except ValueError:
                        element.setAttribute(field_name, None)
            
            # Limpiar otros atributos
            for attr_name in ["linecode", "geometry"]:
                if attr_name in element.fields().names():
                    element.setAttribute(attr_name, None)
        
        elif self.rb_linecode.isChecked():
            # Guardar linecode
            linecode_value = self.cb_linecode.currentText().strip()
            if "linecode" in element.fields().names():
                element.setAttribute("linecode", None if linecode_value == "NULL" else linecode_value)
            
            # Limpiar parámetros eléctricos y geometry
            for attr_name in ["r1", "r0", "x1", "x0", "c1", "c0", "geometry"]:
                if attr_name in element.fields().names():
                    element.setAttribute(attr_name, None)
        
        elif self.rb_geometry.isChecked():
            # Guardar geometry
            geometry_value = self.cb_geometry.currentText().strip()
            if "geometry" in element.fields().names():
                element.setAttribute("geometry", None if geometry_value == "NULL" else geometry_value)
            
            # Limpiar parámetros eléctricos y linecode
            for attr_name in ["r1", "r0", "x1", "x0", "c1", "c0", "linecode"]:
                if attr_name in element.fields().names():
                    element.setAttribute(attr_name, None)
        
        # Guardar atributos generales (siempre se guardan)
        for field_name, widget in [("id", self.id_edit), ("start_node", self.start_node_edit),
                                 ("start_ph", self.start_ph_edit), ("end_node", self.end_node_edit),
                                 ("end_ph", self.end_ph_edit), ("length", self.length_edit),
                                 ("units", self.units_edit), ("phases", self.phases_edit)]:
            if field_name in element.fields().names():
                text = widget.text().strip()
                # Para campos numéricos, convertir a float si es posible
                if field_name == "length":
                    try:
                        value = float(text) if text != "" else None
                        element.setAttribute(field_name, value)
                    except ValueError:
                        element.setAttribute(field_name, None)
                else:
                    element.setAttribute(field_name, text if text != "" else None)
        
        # Guardar cambios en la capa
        layer.startEditing()
        layer.updateFeature(element)
        layer.commitChanges()
        layer.triggerRepaint()
        dialog.accept()

    def save_edits(self, element, layer, dialog):
        for field_name, widget in self.fields.items():
            if isinstance(widget, QComboBox):
                value = widget.currentText()
                element.setAttribute(field_name, None if value == "NULL" else value)
            elif isinstance(widget, QLineEdit):
                valor = widget.text()
                element.setAttribute(field_name, None if valor == "NULL" else valor)
                #element.setAttribute(field_name, widget.text())
        layer.startEditing()
        layer.updateFeature(element)
        layer.commitChanges()
        layer.triggerRepaint()
        dialog.accept()


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
            self.show_edit_form(self.selected_node, self.node_layer)

    def edit_line_element(self):
        if self.selected_line:
            line_id = self.selected_line.attribute("id")
            print(f"Editar línea con ID: {line_id}")
            self.show_edit_form(self.selected_line, self.line_layer)


# **** Hasta aquí estoy dentro de la clase CustomMapTool ****
# **** Hasta aquí estoy dentro de la clase CustomMapTool ****

def find_nearest_switch_for_editing(switch_layer, target_point):
    """
    Devuelve el interruptor más cercano al punto indicado o None.
    """
    scale = iface.mapCanvas().scale()
    buffer_meters = scale / 100          # misma relación que con nodos
    buffer_deg    = buffer_meters / 111000.0
    tol           = buffer_deg

    rect = QgsRectangle(target_point.x() - tol, target_point.y() - tol,
                        target_point.x() + tol, target_point.y() + tol)

    switch_layer.selectByRect(rect)
    candidates = switch_layer.selectedFeatures()
    switch_layer.removeSelection()

    if not candidates:
        return None

    nearest = min(
        candidates,
        key=lambda f: f.geometry().distance(QgsGeometry.fromPointXY(target_point))
    )
    return nearest



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


def updateNodeGeometry(node_layer, node_feat, clicked_point):
    node_layer.startEditing()
    new_geom = QgsGeometry.fromPointXY(QgsPointXY(clicked_point))
    node_layer.changeGeometry(node_feat.id(), new_geom)


def find_nearest_switch_index(switch_layer, target_point):
    """
    Encuentra el interruptor más cercano a un punto dado.

    :param switch_layer: La capa de interruptores.
    :param target_point: El punto de referencia (QgsPointXY).
    :return: El interruptor más cercano (QgsFeature) o None si no se encuentra ninguno.
    """
    scale = iface.mapCanvas().scale()
    buffer_meters = scale / 100  # Ajustar según sea necesario
    buffer_deg = buffer_meters / 111000.0  # Aproximadamente 1 grado de latitud ~ 111,000 metros
    buffer_distance = buffer_deg

    rect = QgsRectangle(target_point.x() - buffer_distance, target_point.y() - buffer_distance,
                        target_point.x() + buffer_distance, target_point.y() + buffer_distance)
    switch_layer.selectByRect(rect)
    selected_switches = [feature for feature in switch_layer.selectedFeatures()]

    if selected_switches:
        nearest_switch = min(selected_switches, key=lambda switch: switch.geometry().distance(QgsGeometry.fromPointXY(target_point)))
        switch_layer.selectByIds([nearest_switch.id()])
        return nearest_switch

    return None


def find_nearest_objects_by_type(point, capas_dict):
    scale = iface.mapCanvas().scale()
    buffer_meters = scale / 100  # igual que en find_nearest_nodes_index
    buffer_deg = buffer_meters / 111000.0
    buffer_distance = buffer_deg

    search_rect = QgsRectangle(
        point.x() - buffer_distance,
        point.y() - buffer_distance,
        point.x() + buffer_distance,
        point.y() + buffer_distance
    )

    encontrados = {}

    # 1) Intentar identificar primero el nodo más cercano
    node_layer = capas_dict.get("Nodo") if isinstance(capas_dict, dict) else None
    nearest_node = None
    if node_layer:
        nearest_node = find_nearest_node_index(node_layer, QgsPointXY(point))

    if nearest_node:
        # Incluir el nodo
        encontrados["Nodo"] = [nearest_node]
        node_id = nearest_node["id"] if "id" in nearest_node.fields().names() else None

        # 2) Buscar asociados por atributos
        for tipo, capa in capas_dict.items():
            if not capa or tipo == "Nodo":
                continue

            asociados = []
            if tipo in ["Carga", "Generador", "FV", "Capacitor", "ET"] and node_id is not None:
                if "start_node" in [f.name() for f in capa.fields()]:
                    for feat in capa.getFeatures():
                        try:
                            if feat["start_node"] == node_id:
                                asociados.append(feat)
                        except Exception:
                            pass
            elif tipo == "Transformador" and node_id is not None:
                field_names = [f.name() for f in capa.fields()]
                has_wdg1 = "wdg1_node" in field_names
                has_wdg2 = "wdg2_node" in field_names
                if has_wdg1 or has_wdg2:
                    for feat in capa.getFeatures():
                        try:
                            if (has_wdg1 and feat["wdg1_node"] == node_id) or (has_wdg2 and feat["wdg2_node"] == node_id):
                                asociados.append(feat)
                        except Exception:
                            pass

            if asociados:
                encontrados[tipo] = asociados

        # Si se encontró el nodo, devolvemos solo asociados por atributo (más precisos)
        return encontrados

    # 3) Fallback: búsqueda espacial para todos los tipos si no se identificó nodo
    for tipo, capa in capas_dict.items():
        if not capa:
            continue
        capa.selectByRect(search_rect)
        features = capa.selectedFeatures()
        if features:
            encontrados.setdefault(tipo, []).extend(features)
        capa.removeSelection()

    return encontrados


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


def import_dss(node_layer, line_layer, transformer_layer, generator_layer, pv_system_layer, et_layer, load_layer, switch_layer, capacitor_layer):
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
    LoadShapes = dss_instance.dssLoadShapes
    LineCodes = dss_instance.dssLineCodes
    Settings = dss_instance.dssSettings
    dssSolution = dss_instance.dssSolution

    node_count = len(nodes)
    line_count = len(lines)
    transformer_count = len(transformers)
    load_count = loads.Count
    relay_count = relays.Count
    vsource_count = vsources.Count
    capacitor_count = Capacitors.Count
    generator_count = Generators.Count
    pvsystem_count = PVSystems.Count
    loadshape_count = LoadShapes.Count
    linecodes_count = LineCodes.Count
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
    print(f"Cantidad de LoadShapes en la red: {loadshape_count}")
    print(f"Cantidad de LineCodes en la red: {linecodes_count}")
    print(f"Los Voltaje Base son: {myVBases}")

    total_elements = node_count + line_count + transformer_count + load_count + relay_count + vsource_count + capacitor_count + generator_count + pvsystem_count
    increment_per_element = 100 / total_elements
    messageLabel.setText("Importando nodos...")
    progress.setValue(int(progress_level))
    QApplication.processEvents()


    # Importar nodos
    node_layer.startEditing()
    for node in nodes:
        dss_instance.activar_barra(node)
        x, y = dss_instance.dssBus.x, dss_instance.dssBus.y
        if x != 0 and y != 0:
            node_feature = QgsFeature(node_layer.fields())
            node_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
            node_feature.setAttribute("id", node)
            #node_feature.setAttribute("pu1", 0)
            node_layer.addFeature(node_feature)

        progress_level += increment_per_element
        progress.setValue(int(progress_level))
        QApplication.processEvents()

    node_layer.commitChanges()
    print(f"Cantidad de nodos importados: {len(node_layer)}")

    # Importar líneas
    messageLabel.setText("Importando lineas...")
    line_layer.startEditing()
    # Nota: los parámetros, a pesar de estar definidos con algunos caracteres en mayúsculas, la interfaz los expone todo convertido a minúsculas
    # Nota1: los parámetros no expuestos directamente, que deben ser accesados a través de la activación del elemento, sí pueden venir con mayúsculas

    if lines.First != 0:
        while True:
            line_name = lines.Name
            # bus1 = lines.Bus1.split('.')[0]
            # bus2 = lines.Bus2.split('.')[0]
            bus1_base, bus1_phases = split_bus(lines.Bus1)
            bus2_base, bus2_phases = split_bus(lines.Bus2)
            bus1_feature = find_node_by_uuid(node_layer, bus1_base)
            bus2_feature = find_node_by_uuid(node_layer, bus2_base)
            if bus1_feature and bus2_feature:
                bus1_geom = bus1_feature.geometry().asPoint()
                bus2_geom = bus2_feature.geometry().asPoint()
                line_feature = QgsFeature(line_layer.fields())
                line_feature.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(bus1_geom), QgsPointXY(bus2_geom)]))
                line_feature.setAttribute("id", line_name)
                line_feature.setAttribute("start_node", bus1_base)
                line_feature.setAttribute("start_ph", bus1_phases)  # ← fases (antes: start_phases)
                line_feature.setAttribute("end_node", bus2_base)
                line_feature.setAttribute("end_ph", bus2_phases)    # ← fases (antes: end_phases)
                #******<Parametros esenciales***************
                #line_feature.setAttribute("length", str(lines.Length))
                #line_feature.setAttribute("units", str(lines.Units)) # Ocurre que viene en none porque no toma el atributo units=m en el .dss
                line_feature.setAttribute("r1", str(lines.R1))
                line_feature.setAttribute("r0", str(lines.R0))
                line_feature.setAttribute("x1", str(lines.X1))
                line_feature.setAttribute("x0", str(lines.X0))
                line_feature.setAttribute("c1", str(lines.C1))
                line_feature.setAttribute("c0", str(lines.C0))                
                line_feature.setAttribute("phases", str(lines.Phases))
                # (2025-08-18) Se elimina el atributo 'enabled' de líneas: ignorar propiedad DSS
                # dss_instance.activar_elemento(f"Line.{line_name}")
                # Enabled = dssCktElement.Properties("enabled").Val
                # line_feature.setAttribute("enabled", Enabled)
                #******<Parametros adicionales**************
                line_feature.setAttribute("linecode", str(lines.LineCode))
                line_feature.setAttribute("geometry", str(lines.Geometry))
                #line_feature.setAttribute("Rmatrix", str(lines.RMatrix))
                #line_feature.setAttribute("Xmatrix", str(lines.XMatrix))
                #line_feature.setAttribute("Cmatrix", str(lines.CMatrix))
                #line_feature.setAttribute("rg", str(lines.Rg))
                #line_feature.setAttribute("rho", str(lines.Rho))
                #line_feature.setAttribute("seasonrating", str(lines.SeasonRating))
                #line_feature.setAttribute("xg", str(lines.Xg))
                #line_feature.setAttribute("spacing", str(lines.Spacing))
                #line_feature.setAttribute("normamps", str(lines.NormAmps))
                #******>Parametros***************

                ## AQUÍ RECALCULAR EL PARAMETRO lenght en metros
                distance_calculator = QgsDistanceArea()
                distance_calculator.setSourceCrs(line_layer.crs(), QgsProject.instance().transformContext())
                # Establecer el elipsoide para cálculos más precisos. Se utiliza WGS84 por defecto.
                distance_calculator.setEllipsoid('WGS84')
                precise_length = distance_calculator.measureLength(line_feature.geometry())
                # Redondear la longitud a dos decimales y actualizar el atributo 'length'.
                line_feature.setAttribute("length", str(round(precise_length, 2)))
                # Asegurar que la unidad de medida quede establecida en metros.
                line_feature.setAttribute("units", "m")

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

            # bus1 = barra1.split('.')[0]
            # bus2 = barra2.split('.')[0]
            bus1, w1_ph = split_bus(barra1)
            bus2, w2_ph = split_bus(barra2)
            bus1_feature = find_node_by_uuid(node_layer, bus1)

            if bus1_feature:
                bus1_geom = bus1_feature.geometry().asPoint()      
                transformer_feature = QgsFeature(transformer_layer.fields())
                transformer_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
                transformer_feature.setAttribute("id", transformer_name)
                transformer_feature.setAttribute("wdg1_node", bus1)
                transformer_feature.setAttribute("wdg1_ph", w1_ph)  # ← fases (antes: wdg1_phases)
                transformer_feature.setAttribute("wdg2_node", bus2)
                transformer_feature.setAttribute("wdg2_ph", w2_ph)  # ← fases (antes: wdg2_phases)
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
                transformer_feature.setAttribute("nwindings", str(transformers.NumWindings))
                transformer_feature.setAttribute("xfmrcode", str(transformers.XfmrCode))
                transformer_feature.setAttribute("tap", str(transformers.Tap))
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
                #transformer_feature.setAttribute("xfmrcode", transformers.xfmrcode)  
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

            # bus1 = barra1.split('.')[0]
            bus1, phases = split_bus(barra1)
            bus1_feature = find_node_by_uuid(node_layer, bus1)

            if bus1_feature:
                bus1_geom = bus1_feature.geometry().asPoint()  
                load_feature = QgsFeature(load_layer.fields())
                load_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
                load_feature.setAttribute("id", load_name)
                load_feature.setAttribute("start_node", bus1)
                load_feature.setAttribute("start_ph", phases)  # ← fases (antes: start_phases)
                #******<Parametros esenciales***************
                load_feature.setAttribute("kv", str(loads.kV))
                load_feature.setAttribute("kw", str(loads.kW))
                load_feature.setAttribute("pf", str(loads.PF))
                #load_feature.setAttribute("status", str(loads.Status)) #Lo toma mal
                load_feature.setAttribute("model", str(loads.Model))
                load_feature.setAttribute("cvrwatts", str(loads.CVRwatts))
                load_feature.setAttribute("cvrvars", str(loads.CVRvars))
                load_feature.setAttribute("class", str(loads.Class))
                load_feature.setAttribute("daily", str(loads.daily)) # Viene siempre los caracteres en minúscula
                #******<Parametros esenciales no presentes en interfaz*****
                dss_instance.activar_elemento(f"Load.{load_name}")
                phases_val = dssCktElement.Properties("phases").Val
                load_feature.setAttribute("phases", phases_val)
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

            # bus1 = barra1.split('.')[0]
            bus1, phases = split_bus(barra1)
            bus1_feature = find_node_by_uuid(node_layer, bus1)

            if bus1_feature:
                bus1_geom = bus1_feature.geometry().asPoint()  
                capacitor_feature = QgsFeature(capacitor_layer.fields())
                capacitor_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
                capacitor_feature.setAttribute("id", capacitor_name)
                capacitor_feature.setAttribute("start_node", bus1)
                capacitor_feature.setAttribute("start_ph", phases)  # ← fases (antes: start_phases)
                #******<Parametros esenciales***************
                capacitor_feature.setAttribute("kv", str(Capacitors.kV))
                capacitor_feature.setAttribute("kvar", str(Capacitors.kvar))
                #******<Parametros esenciales no presentes en interfaz*****
                dss_instance.activar_elemento(f"Capacitor.{capacitor_name}")
                phases_val = dssCktElement.Properties("phases").Val
                capacitor_feature.setAttribute("phases", phases_val)
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

            # bus1 = barra1.split('.')[0]
            bus1, phases = split_bus(barra1)
            bus1_feature = find_node_by_uuid(node_layer, bus1)

            if bus1_feature:
                bus1_geom = bus1_feature.geometry().asPoint()  
                generator_feature = QgsFeature(generator_layer.fields())
                generator_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
                generator_feature.setAttribute("id", generator_name)
                generator_feature.setAttribute("start_node", bus1)
                generator_feature.setAttribute("start_ph", phases)  # ← fases (antes: start_phases)
                #******<Parametros esenciales***************
                generator_feature.setAttribute("Phases", str(Generators.Phases))
                generator_feature.setAttribute("kV", str(Generators.kV))
                generator_feature.setAttribute("kW", str(Generators.kW))
                generator_feature.setAttribute("PF", str(Generators.PF))
                #******<Parametros esenciales no presentes en interfaz*****
                dss_instance.activar_elemento(f"Generator.{generator_name}")
                daily = dssCktElement.Properties("daily").Val
                if daily is not None:
                    daily = str(daily).lower()
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

            # bus1 = barra1.split('.')[0]
            bus1, phases = split_bus(barra1)
            bus1_feature = find_node_by_uuid(node_layer, bus1)

            if bus1_feature:
                bus1_geom = bus1_feature.geometry().asPoint()  
                pv_system_feature = QgsFeature(pv_system_layer.fields())
                pv_system_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
                pv_system_feature.setAttribute("id", pv_system_name)
                pv_system_feature.setAttribute("start_node", bus1)
                pv_system_feature.setAttribute("start_ph", phases)  # ← fases (antes: start_phases)
                #******<Parametros esenciales***************
                pv_system_feature.setAttribute("Irradiance", str(PVSystems.Irradiance))
                pv_system_feature.setAttribute("Pmpp", str(PVSystems.Pmpp))
                #******<Parametros esenciales no presentes en interfaz*****
                dss_instance.activar_elemento(f"PVSystem.{pv_system_name}")
                phases_val = dssCktElement.Properties("phases").Val
                pv_system_feature.setAttribute("phases", phases_val)
                kv = dssCktElement.Properties("kv").Val
                pv_system_feature.setAttribute("kv", kv)
                temperature = dssCktElement.Properties("Temperature").Val
                pv_system_feature.setAttribute("Temperatur", temperature)  # Ojo que el atributo en Opendss es Temperature, pero qgis permite solo 10 caracteres
                kva = dssCktElement.Properties("kVA").Val
                pv_system_feature.setAttribute("kVA", kva)
                effcurve = dssCktElement.Properties("EffCurve").Val
                if effcurve is not None:
                    effcurve = str(effcurve).lower()
                pv_system_feature.setAttribute("EffCurve", effcurve)
                daily = dssCktElement.Properties("daily").Val
                if daily is not None:
                    daily = str(daily).lower()
                pv_system_feature.setAttribute("daily", daily)
                tdaily = dssCktElement.Properties("Tdaily").Val
                if tdaily is not None:
                    tdaily = str(tdaily).lower()
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
            line_feat = find_line_by_uuid(line_layer, linea)
            if line_feat:
                # Calcular la posición del interruptor en la línea
                switch_point = find_point_on_line(line_feat, monitored_term)
                if switch_point:
                    switch_feature = QgsFeature(switch_layer.fields())
                    switch_feature.setGeometry(switch_point)
                    switch_feature.setAttribute("id", relay_name)
                    switch_feature.setAttribute("line", linea)
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

            # bus1 = barra1.split('.')[0]
            bus1, phases = split_bus(barra1)
            bus1_feature = find_node_by_uuid(node_layer, bus1)

            if bus1_feature:
                bus1_geom = bus1_feature.geometry().asPoint()  
                et_feature = QgsFeature(et_layer.fields())
                et_feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(bus1_geom)))
                et_feature.setAttribute("id", vsource_name)
                et_feature.setAttribute("start_node", bus1)
                et_feature.setAttribute("start_ph", phases)  # ← fases (antes: start_phases)
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
                #******<Asignar phases desde la interfaz***************
                et_feature.setAttribute("phases", str(vsources.Phases))
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

    # Importar LoadShapes
    messageLabel.setText("Importando LoadShapes...")
    loadshape_layers = QgsProject.instance().mapLayersByName("loadshape")

    if not loadshape_layers:
        raise Exception("No se encontró la capa 'loadshape'")

    loadshape_layer = loadshape_layers[0]
    loadshape_layer.startEditing()


    if LoadShapes.First != 0:
        while True:
            loadshape_name = LoadShapes.Name
            npts = LoadShapes.Npts
            interval = LoadShapes.HrInterval
            #******<Parametros esenciales no presentes en interfaz*****
            dss_instance.activar_elemento(f"LoadShape.{loadshape_name}")
            csvfile = dssCktElement.Properties("csvfile").Val
            Mult = dssCktElement.Properties("Mult").Val
            Pmult = dssCktElement.Properties("Pmult").Val

            loadshape_feature = QgsFeature(loadshape_layer.fields())
            loadshape_feature.setAttribute("id", loadshape_name)
            loadshape_feature.setAttribute("npts", npts)
            loadshape_feature.setAttribute("interval", interval)
            loadshape_feature.setAttribute("mult", Mult)
            loadshape_feature.setAttribute("csvfile", csvfile)
            #******>Parametros***************
            loadshape_layer.addFeature(loadshape_feature)

            if LoadShapes.Next == 0:
                break

    loadshape_layer.commitChanges()
    print(f"Cantidad de LoadShapes importadas: {len(loadshape_layer)}")


    # Importar Settings
    settings_layers = QgsProject.instance().mapLayersByName("settings")
    if not settings_layers:
        raise Exception("No se encontró la capa 'settings'")
    
    settings_layer = settings_layers[0]
    settings_layer.startEditing()
    id = "caso_base"
    frequency = dssSolution.Frequency
    voltagebases = str(Settings.VoltageBases) if Settings.VoltageBases is not None else ""  # Convertir a string y manejar None
    solu_mode = dssSolution.Mode
    #******<Parametros***************
    settings_feature = QgsFeature(settings_layer.fields())
    settings_feature.setAttribute("id", id)
    settings_feature.setAttribute("frequency", frequency)
    settings_feature.setAttribute("voltbases", voltagebases)
    settings_feature.setAttribute("solu_mode", solu_mode)
    #******>Parametros***************
    settings_layer.addFeature(settings_feature)
    settings_layer.commitChanges()


    # Importar LineCode
    linecode_file = os.path.join(os.path.dirname(dss_path), "LineCode.dss")
    linecode_layers = QgsProject.instance().mapLayersByName("linecode")
    if linecode_layers:
        importar_linecode(linecode_file, linecode_layers[0])
    else:
        print("No se encontró la capa 'linecode'")

    # Importar LineGeometry
    line_geometry_file = os.path.join(os.path.dirname(dss_path), "LineGeometry.dss")
    line_geometry_layers = QgsProject.instance().mapLayersByName("linegeometry")
    if line_geometry_layers:
        importar_linegeometry(line_geometry_file, line_geometry_layers[0])
    else:
        print("No se encontró la capa 'linegeometry'")

    # Importar LineSpacing
    line_spacing_file = os.path.join(os.path.dirname(dss_path), "LineSpacing.dss")
    line_spacing_layers = QgsProject.instance().mapLayersByName("linespacing")
    if line_spacing_layers:
        importar_linespacing(line_spacing_file, line_spacing_layers[0])
    else:
        print("No se encontró la capa 'linespacing'")


    # Importar WireData
    wire_data_file = os.path.join(os.path.dirname(dss_path), "WireData.dss")
    wire_data_layers = QgsProject.instance().mapLayersByName("wiredata")
    if wire_data_layers:
        importar_wiredata(wire_data_file, wire_data_layers[0])
    else:
        print("No se encontró la capa 'wiredata'")


    # Importar XYCurve
    xycurve_data_file = os.path.join(os.path.dirname(dss_path), "XYcurve.dss")
    xycurve_layers = QgsProject.instance().mapLayersByName("xycurve")
    if xycurve_layers:
        importar_xycurve(xycurve_data_file, xycurve_layers[0])
    else:
        print("No se encontró la capa 'xycurve'")


    # Importar TShape
    tshape_data_file = os.path.join(os.path.dirname(dss_path), "TShape.dss")
    tshape_layers = QgsProject.instance().mapLayersByName("tshape")
    if tshape_layers:
        importar_tshape(tshape_data_file, tshape_layers[0])
    else:
        print("No se encontró la capa 'tshape'")


    # Importar XfmrCode
    xfmrcode_data_file = os.path.join(os.path.dirname(dss_path), "XfmrCode.dss")
    xfmrcode_layers = QgsProject.instance().mapLayersByName("xfmrcode")
    if xfmrcode_layers:
        importar_xfmrcode(xfmrcode_data_file, xfmrcode_layers[0])
    else:
        print("No se encontró la capa 'xfmrcode'")


    # Finalización
    iface.messageBar().clearWidgets()  # Limpiar la barra de mensajes

    print("Importación desde OpenDSS completada.")


def split_bus(bus_str: str):
    """Devuelve (nombre_base, fases) tal como usa OpenDSS.
    Ej.: 'feeder1.1.2'  -> ('feeder1', '12')
         'loadB.3'      -> ('loadB',   '3')
         'sourcebus'    -> ('sourcebus','123')  # default trifásico
    """
    parts = bus_str.split('.')
    base   = parts[0]
    phases = ''.join(parts[1:]) or '123'
    return base, phases



def importar_xfmrcode(file_path, xfmrcode_layer):
    """
    Importa objetos XfmrCode desde *file_path* a la capa *xfmrcode_layer*.
    • Cada línea del archivo debe comenzar con:  New "XfmrCode.<nombre>" …
    • Todos los parámetros presentes se copian al campo homónimo de la capa.
      Los no presentes quedan en blanco ("").
    """
    import os, re

    if not os.path.exists(file_path):
        print("Archivo xfmrcode.dss no encontrado")
        return

    if not xfmrcode_layer:
        print("Error: La capa 'xfmrcode' no es válida")
        return

    # Diccionario clave → nombre-de-campo ordenado exactamente como en la capa
    attr_order = [
        "id", "phases", "windings", "kvs", "kvas", "conns", "%rs",
        "xhl", "xht", "xlt", "maxtap", "mintap",
        "%loadloss", "%nloadloss", "ppm_afloat", "%imag"
    ]  # campos definidos al crear la capa :contentReference[oaicite:0]{index=0}

    # RegEx para extraer el nombre (tolera comillas opcionales)
    name_re = re.compile(r'New\s+"?XfmrCode\.([^\s"]+)"?', re.IGNORECASE)

    xfmrcode_layer.startEditing()
    count = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("//"):
                continue

            m = name_re.match(line)
            if not m:
                continue

            code_id = m.group(1).lower()
            tail = line[m.end():].strip()        # resto de la línea tras el nombre
            tokens = tail.split()

            params = {}
            i = 0
            while i < len(tokens):
                if "=" in tokens[i]:
                    key, value = tokens[i].split("=", 1)
                    # Si el valor inicia con '[' y aún no cerró ']', concatenar tokens
                    if value.startswith("[") and not value.endswith("]"):
                        full = value
                        i += 1
                        while i < len(tokens) and not tokens[i].endswith("]"):
                            full += " " + tokens[i]
                            i += 1
                        if i < len(tokens):
                            full += " " + tokens[i]
                        value = full
                    params[key.lower()] = value
                i += 1

            # Aceptar indistintamente ppm_afloat / ppm_antifloat
            if "ppm_antifloat" in params and "ppm_afloat" not in params:
                params["ppm_afloat"] = params["ppm_antifloat"]

            feat = QgsFeature(xfmrcode_layer.fields())
            # Rellenar atributos siguiendo el orden declarado en la capa
            for field in attr_order:
                if field == "id":
                    feat.setAttribute(field, code_id)
                else:
                    feat.setAttribute(field, params.get(field, ""))

            xfmrcode_layer.addFeature(feat)
            count += 1

    xfmrcode_layer.commitChanges()
    print(f"Cantidad de XfmrCode importados: {count}")



def importar_loadshape(file_path, loadshape_layer):
    """
    Importa definiciones de LoadShape desde *file_path* a la capa *loadshape_layer*.

    • Si aparece csvfile=…, se abre el CSV, se redondean los valores a 3 decimales
      y se almacenan en «mult» como una lista de texto.
    • Si aparece mult=[…] / mult=(…)  o  pmult=…, también se redondea a 3 decimales.
    • Los nombres de los objetos se convierten a minúsculas sin el prefijo 'loadshape.'.
    """
    if not os.path.exists(file_path):
        print("Archivo LoadShape.dss no encontrado")
        return
    if not loadshape_layer:
        print("Error: capa de loadshape no válida")
        return

    base_dir = os.path.dirname(file_path)
    loadshape_layer.startEditing()
    creados = 0

    # --------- ayudante para extraer parámetros ----------
    def _buscar_pat(pat, texto):
        m = re.search(pat, texto, flags=re.I)
        return m.group(1) if m else None

    # --------- formateo a 3 decimales --------------------
    def _lista_a_str(valores):
        return "[" + ", ".join(f"{v:.3f}" for v in valores) + "]"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith(("!", "//")):
                    continue
                if not linea.lower().startswith("new"):
                    continue

                # ------------- nombre del objeto ---------------
                partes = linea.split(None, 2)
                if len(partes) < 2:
                    continue
                nombre = partes[1].strip('"\'')

                if nombre.lower().startswith("loadshape."):
                    nombre = nombre.split(".", 1)[1]
                nombre = nombre.lower()

                params = partes[2] if len(partes) > 2 else ""

                npts = _buscar_pat(r"npts\s*=\s*(\d+)", params) or ""
                intervalo = (
                    _buscar_pat(r"hrinterval\s*=\s*([\d\.]+)", params)
                    or _buscar_pat(r"sinterval\s*=\s*([\d\.]+)", params)
                    or _buscar_pat(r"interval\s*=\s*([\d\.]+)", params)
                    or ""
                )

                csvfile = _buscar_pat(r"csvfile\s*=\s*([^\s]+)", params)
                mult_txt = ""

                if csvfile:
                    # -------- leer CSV y redondear ------------
                    csvfile = csvfile.strip('"\'')

                    ruta_csv = (
                        csvfile if os.path.isabs(csvfile) else os.path.join(base_dir, csvfile)
                    )
                    if not os.path.exists(ruta_csv):
                        print(f"• CSV '{csvfile}' no encontrado; se omite")
                        valores = []
                    else:
                        valores = []
                        with open(ruta_csv, "r", encoding="utf-8") as c:
                            for fila in c:
                                fila = fila.strip().strip('"').strip()
                                if fila and not fila.startswith(("!", "//")):
                                    for v in re.split(r"[,\s]+", fila):
                                        if v:
                                            try:
                                                valores.append(round(float(v), 3))
                                            except ValueError:
                                                pass
                    mult_txt = _lista_a_str(valores)
                else:
                    # -------- mult= […]  / pmult= (…) ---------
                    m_mult = _buscar_pat(r"(?:p?mult)\s*=\s*\[([^\]]+)\]", params)
                    if not m_mult:
                        m_mult = _buscar_pat(r"(?:p?mult)\s*=\s*\(([^\)]+)\)", params)
                    if m_mult:
                        nums = []
                        for num in re.split(r"[,\s]+", m_mult):
                            if num:
                                try:
                                    nums.append(round(float(num), 3))
                                except ValueError:
                                    pass
                        mult_txt = _lista_a_str(nums)

                # ------------- crear feature ------------------
                feat = QgsFeature(loadshape_layer.fields())
                feat.setAttributes([
                    nombre,      # id
                    npts,        # npts
                    intervalo,   # interval
                    mult_txt,    # mult
                    csvfile      # csvfile (None si no aplica)
                ])
                loadshape_layer.addFeature(feat)
                creados += 1

        loadshape_layer.commitChanges()
        print(f"Importación de LoadShape completada: {creados} objetos.")
    except Exception as e:
        loadshape_layer.rollBack()
        print("Error al importar LoadShape:", e)



def importar_tshape(file_path, tshape_layer):
    if not os.path.exists(file_path):
        print("Archivo TShape.dss no encontrado")
        return

    if not tshape_layer:
        print("Error: La capa de tshape no es válida")
        return

    tshape_layer.startEditing()
    base_dir = os.path.dirname(file_path)

    try:
        with open(file_path, 'r') as f:
            line_count = 0
            shape_count = 0
            for line in f:
                line_count += 1
                line = line.strip()
                if not line or line.startswith('!'):
                    continue

                # Buscar líneas que comienzan con "New TShape"
                if line.lower().startswith('new tshape'):
                    try:
                        # Extraer el nombre del tshape
                        parts = line.split()
                        if len(parts) < 2:
                            continue
                        
                        # El nombre está después de "New TShape."
                        tshape_name = parts[1]
                        if '.' in tshape_name:
                            tshape_name = tshape_name.split('.')[-1]  # Tomar la parte después del último punto                        
                        tshape_name = tshape_name.lower()  # Convertir a minúsculas

                        # Extraer el número de puntos
                        npts_start = line.find('npts=') + 5
                        npts_end = line.find(' ', npts_start)
                        if npts_start == 4 or npts_end == -1:
                            continue
                        
                        npts = int(line[npts_start:npts_end])
                        
                        # Determinar si es tipo 1 (temp) o tipo 2 (csvfile)
                        if 'temp=[' in line:
                            # Tipo 1: Extraer temperaturas directamente
                            temp_start = line.find('temp=[') + 6
                            temp_end = line.find(']', temp_start)
                            if temp_start == 5 or temp_end == -1:
                                continue
                            
                            temp_str = line[temp_start:temp_end]
                            temps = [float(t) for t in temp_str.split()]
                            csvfile = None
                        
                        elif 'csvfile=' in line:
                            # Tipo 2: Leer temperaturas desde archivo CSV
                            csv_start = line.find('csvfile=') + 8
                            csv_end = line.find(' ', csv_start)
                            if csv_end == -1:
                                csv_end = len(line)
                            
                            csv_filename = line[csv_start:csv_end]
                            csvfile = csv_filename
                            
                            # Construir la ruta completa del archivo CSV
                            if os.path.isabs(csv_filename):
                                csv_path = csv_filename
                            else:
                                csv_path = os.path.join(base_dir, csv_filename)
                            
                            if not os.path.exists(csv_path):
                                continue
                            
                            # Leer temperaturas desde el CSV
                            temps = []
                            with open(csv_path, 'r') as csv_file:
                                for csv_line in csv_file:
                                    csv_line = csv_line.strip()
                                    if csv_line and not csv_line.startswith('!'):
                                        try:
                                            # Eliminar comillas y espacios
                                            csv_line = csv_line.strip().strip('"')
                                            if csv_line:  # Verificar que no esté vacío después de limpiar
                                                temp = float(csv_line)
                                                temps.append(temp)
                                        except ValueError:
                                            continue
                        else:
                            continue
                        
                        # Crear nuevo feature
                        feat = QgsFeature()
                        feat.setAttributes([
                            tshape_name,  # id
                            str(npts),    # npts
                            str(temps),   # temp
                            csvfile       # csvfile (None para tipo 1, nombre archivo para tipo 2)
                        ])
                        
                        tshape_layer.addFeature(feat)
                        shape_count += 1
                        
                    except Exception:
                        continue

        tshape_layer.commitChanges()
        print(f"Importación de TShape completada. Se importaron {shape_count} shapes.")
    except Exception as e:
        tshape_layer.rollBack()
        raise

def importar_xycurve(file_path, xycurve_layer):
    if not os.path.exists(file_path):
        print("Archivo XYcurve.dss no encontrado")
        return

    if not xycurve_layer:
        print("Error: La capa de xycurve no es válida")
        return

    xycurve_layer.startEditing()
    base_dir = os.path.dirname(file_path)

    try:
        with open(file_path, 'r') as f:
            line_count = 0
            curve_count = 0
            for line in f:
                line_count += 1
                line = line.strip()
                if not line or line.startswith('!'):
                    continue

                # Buscar líneas que comienzan con "New XYcurve"
                if line.lower().startswith('new xycurve'):
                    try:
                        # Extraer el nombre de la curva
                        parts = line.split()
                        if len(parts) < 2:
                            continue
                        
                        # El nombre está después de "New XYcurve."
                        curve_name = parts[1]
                        if '.' in curve_name:
                            curve_name = curve_name.split('.')[-1]  # Tomar la parte después del último punto                        
                        curve_name = curve_name.lower()  # Convertir a minúsculas

                        # Extraer el número de puntos
                        npts_start = line.find('npts=') + 5
                        npts_end = line.find(' ', npts_start)
                        if npts_start == 4 or npts_end == -1:
                            continue
                        
                        npts = int(line[npts_start:npts_end])
                        
                        # Determinar si es tipo 1 (Points) o tipo 2 (csvfile)
                        if 'Points=[' in line:
                            # Tipo 1: Extraer puntos directamente
                            points_start = line.find('Points=[') + 7
                            points_end = line.find(']', points_start)
                            if points_start == 6 or points_end == -1:
                                continue
                            
                            # Mantener el formato original de los puntos incluyendo los corchetes
                            points = f"[{line[points_start:points_end]}]"
                            csvfile = None
                        
                        elif 'csvfile=' in line:
                            # Tipo 2: Leer puntos desde archivo CSV
                            csv_start = line.find('csvfile=') + 8
                            csv_end = line.find(' ', csv_start)
                            if csv_end == -1:
                                csv_end = len(line)
                            
                            csv_filename = line[csv_start:csv_end]
                            csvfile = csv_filename
                            
                            # Construir la ruta completa del archivo CSV
                            if os.path.isabs(csv_filename):
                                csv_path = csv_filename
                            else:
                                csv_path = os.path.join(base_dir, csv_filename)
                            
                            if not os.path.exists(csv_path):
                                continue
                            
                            # Leer puntos desde el CSV y formatearlos en el formato OpenDSS
                            points_list = []
                            with open(csv_path, 'r') as csv_file:
                                for csv_line in csv_file:
                                    csv_line = csv_line.strip()
                                    if csv_line and not csv_line.startswith('!'):
                                        try:
                                            # Eliminar comillas si existen
                                            csv_line = csv_line.strip('"')
                                            x, y = map(float, csv_line.split(','))
                                            points_list.append(f"{x},{y}")
                                        except ValueError:
                                            continue
                            points = f"[{' '.join(points_list)}]"
                        else:
                            continue
                        
                        # Crear nuevo feature
                        feat = QgsFeature()
                        feat.setAttributes([
                            curve_name,  # id
                            str(npts),   # npts
                            points,      # points (ya en formato OpenDSS con corchetes)
                            csvfile      # csvfile (None para tipo 1, nombre archivo para tipo 2)
                        ])
                        
                        xycurve_layer.addFeature(feat)
                        curve_count += 1
                        
                    except Exception:
                        continue

        xycurve_layer.commitChanges()
        print(f"Importación de XYcurve completada. Se importaron {curve_count} curvas.")
    except Exception as e:
        xycurve_layer.rollBack()
        raise

def importar_linecode(file_path, linecode_layer):
    if not os.path.exists(file_path):
        print("Archivo LineCode.dss no encontrado")
        return

    if not linecode_layer:
        print("Error: La capa de linecodes no es válida")
        return

    linecode_layer.startEditing()

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('//'):
                continue

            #if line.lower().startswith('new linecode.'):
            if line.startswith('New LineCode.'):
                parts = line.split('New LineCode.')[1].split()
                name = parts[0].lower()
                params = {}
                i = 1
                while i < len(parts):
                    if '=' in parts[i]:
                        key, value = parts[i].split('=')
                        params[key.lower()] = value
                    i += 1

                linecode_feature = QgsFeature()
                linecode_feature.setAttributes([
                    name,
                    params.get('nphases', ''),
                    params.get('r1', ''),
                    params.get('r0', ''),
                    params.get('x1', ''),
                    params.get('x0', ''),
                    params.get('c1', ''),
                    params.get('c0', '')
                ])
                linecode_layer.addFeature(linecode_feature)

    linecode_layer.commitChanges()
    print(f"Cantidad de LineCode importados: {len(linecode_layer)}")



def importar_linegeometry(file_path, line_geometry_layer):
    if not os.path.exists(file_path):
        print("Archivo LineGeometry.dss no encontrado")
        return

    if not line_geometry_layer:
        print("Error: La capa de geometrías de línea no es válida")
        return

    line_geometry_layer.startEditing()

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('//'):
                continue

            if line.startswith('New LineGeometry.'):
                parts = line.split('New LineGeometry.')[1].split()
                name = parts[0].lower()  # Convertir a minúsculas
                params = {}
                i = 1
                while i < len(parts):
                    if '=' in parts[i]:
                        key, value = parts[i].split('=')
                        if value.startswith('('):
                            full_value = value
                            i += 1
                            while i < len(parts) and not parts[i].endswith(')'):
                                full_value += ' ' + parts[i]
                                i += 1
                            if i < len(parts):
                                full_value += ' ' + parts[i]
                            params[key] = full_value
                        else:
                            params[key] = value
                    i += 1

                # Extraer los parámetros opcionales y normalizarlos.  "reduce" es una
                # bandera opcional (True/False) en OpenDSS y puede no estar presente.
                spacing = params.get('spacing', '').lower()
                wires = params.get('wires', '').lower()
                # Convertir el valor de reduce a minúsculas para mantener el mismo
                # patrón de uso que con otros parámetros como 'spacing' y 'wires'.  Si
                # no existe, usar cadena vacía.
                reduce_param = params.get('reduce', '').lower()

                # Crear el feature y establecer sus atributos en el mismo orden que la
                # definición de la capa: id, nconds, nphases, spacing, wires, reduce.
                line_geometry_feature = QgsFeature()
                line_geometry_feature.setAttributes([
                    name,
                    params.get('nconds', ''),
                    params.get('nphases', ''),
                    spacing,
                    wires,
                    reduce_param
                ])
                line_geometry_layer.addFeature(line_geometry_feature)

    line_geometry_layer.commitChanges()
    print(f"Cantidad de LineGeometry importadas: {len(line_geometry_layer)}")



def importar_linespacing(file_path, line_spacing_layer):
    if not os.path.exists(file_path):
        print("Archivo LineSpacing.dss no encontrado")
        return

    if not line_spacing_layer:
        print("Error: La capa de espaciados de línea no es válida")
        return

    line_spacing_layer.startEditing()

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('//'):
                continue

            if line.startswith('New LineSpacing.'):
                parts = line.split('New LineSpacing.')[1].split()
                name = parts[0].lower()  # Convertir a minúsculas
                params = {}
                i = 1
                while i < len(parts):
                    if '=' in parts[i]:
                        key, value = parts[i].split('=')
                        if value.startswith('('):
                            full_value = value
                            i += 1
                            while i < len(parts) and not parts[i].endswith(')'):
                                full_value += ' ' + parts[i]
                                i += 1
                            if i < len(parts):
                                full_value += ' ' + parts[i]
                            params[key] = full_value
                        else:
                            params[key] = value
                    i += 1

                line_spacing_feature = QgsFeature()
                line_spacing_feature.setAttributes([
                    name,
                    params.get('nconds', ''),
                    params.get('nphases', ''),
                    params.get('units', ''),
                    params.get('x', ''),
                    params.get('h', '')
                ])
                line_spacing_layer.addFeature(line_spacing_feature)

    line_spacing_layer.commitChanges()
    print(f"Cantidad de LineSpacing importados: {len(line_spacing_layer)}")

def importar_wiredata(file_path, wire_data_layer):
    if not os.path.exists(file_path):
        print("Archivo WireData.dss no encontrado")
        return

    if not wire_data_layer:
        print("Error: La capa de datos de conductores no es válida")
        return

    wire_data_layer.startEditing()

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('//'):
                continue

            if line.startswith('New WireData.'):
                parts = line.split('New WireData.')[1].split()
                name = parts[0].lower()  # Convertir a minúsculas
                params = {}
                i = 1
                while i < len(parts):
                    if '=' in parts[i]:
                        key, value = parts[i].split('=')
                        params[key] = value
                    i += 1

                wire_data_feature = QgsFeature()
                wire_data_feature.setAttributes([
                    name,
                    params.get('Rdc', ''),
                    params.get('Runits', ''),
                    params.get('diam', ''),
                    params.get('Radunits', ''),
                    params.get('emergamps', '')
                ])
                wire_data_layer.addFeature(wire_data_feature)

    wire_data_layer.commitChanges()
    print(f"Cantidad de WireData importados: {len(wire_data_layer)}")


def reset_power_flow():
    # Indicador de ejecución (spinner) para el reseteo del flujo
    QApplication.setOverrideCursor(Qt.BusyCursor)
    msg = iface.messageBar().createMessage("Flujo de potencia", "Reiniciando resultados…")
    bar = QProgressBar(); bar.setRange(0, 0)
    msg.layout().addWidget(bar)
    handle = iface.messageBar().pushWidget(msg, Qgis.Info)
    try:
        # Iniciar edición en la capa de nodos
        node_layer.startEditing()
        for node in node_layer.getFeatures():
            node.setAttribute("pu1", None)
            node_layer.updateFeature(node)
        node_layer.commitChanges()

        # Iniciar edición en la capa de líneas
        line_layer.startEditing()
        for line in line_layer.getFeatures():
            line.setAttribute("P.Activa", None)
            line.setAttribute("P.Reactiva", None)
            line.setAttribute("kVBaseLL", None)
            line_layer.updateFeature(line)
        line_layer.commitChanges()

        # Iniciar edición en la capa de cargas
        load_layer.startEditing()
        for load in load_layer.getFeatures():
            load.setAttribute("P.Activa", None)
            load.setAttribute("P.Reactiva", None)
            load_layer.updateFeature(load)
        load_layer.commitChanges()

        # Forzar la actualización del lienzo y procesar eventos
        iface.mapCanvas().refresh()
        QApplication.processEvents()
    finally:
        iface.messageBar().popWidget(handle)
        QApplication.restoreOverrideCursor()



def power_flow(node_layer, line_layer, load_layer, Modo):
    # Indicar estado ocupado y mostrar barra indeterminada persistente
    QApplication.setOverrideCursor(Qt.BusyCursor)
    msg = iface.messageBar().createMessage("Flujo de potencia", "Calculando…")
    bar = QProgressBar(); bar.setRange(0, 0)
    msg.layout().addWidget(bar)
    handle = iface.messageBar().pushWidget(msg, Qgis.Info)
    try:
        # Paso 1: Exportar archivos DSS
        script_dir = project_path
        power_flow_dir = os.path.join(script_dir, "power-flow")
        # Ensure the directory exists
        if not os.path.exists(power_flow_dir):
            os.makedirs(power_flow_dir)

        export_dss_location(power_flow_dir, node_layer, line_layer, transformer_layer, generator_layer, pv_system_layer, et_layer, load_layer, switch_layer, capacitor_layer)

        # Paso 2: Conectar a la red generada y realizar el cálculo de flujo de potencia
        script_dir = project_path
        master_dss_path = os.path.join(script_dir, "power-flow", "Master.dss")
        dss_instance = DSS(master_dss_path)
        dss_instance.compilar_DSS()

        if Modo == "SNAPSHOT":
            dss_instance.resolver_DSS_snapshot(1.0)
        elif Modo == "HOURLY":
            hour, ok = QInputDialog.getInt(None, "Input Hour", "Enter the hour for power flow calculation:", min=0, max=23)
            if ok:
                dss_instance.resolver_DSS_hourly(hour, 1.0)
            else:
                print("Hour input was cancelled. Exiting power flow calculation.")

        # Paso 3: Leer los resultados del cálculo y actualizar las capas
        node_layer.startEditing()
        for node in node_layer.getFeatures():
            node_id = node['id']
            dss_instance.activar_barra(node_id)

            pu1 = dss_instance.dssBus.puVmagAngle[0]
            pu1 = round(pu1, 5)
            node.setAttribute("pu1", str(pu1))

            voltages = dss_instance.dssBus.kVBase
            voltages_LL = voltages * math.sqrt(3)
            voltages_LL = round(voltages_LL, 3)
            node.setAttribute("kVBaseLL", str(voltages_LL))

            node_layer.updateFeature(node)
        node_layer.commitChanges()

        line_layer.startEditing()
        for line in line_layer.getFeatures():
            line_id = line['id']
            dss_instance.activar_elemento(f"Line.{line_id}")
            p_activa = dss_instance.dssCktElement.TotalPowers[0]
            p_activa = round(p_activa, 3)
            line.setAttribute("P.Activa", str(p_activa))

            p_reactiva = dss_instance.dssCktElement.TotalPowers[1]
            p_reactiva = round(p_reactiva, 3)
            line.setAttribute("P.Reactiva", str(p_reactiva))

            node_id = line['start_node']
            dss_instance.activar_barra(node_id)

            voltages = dss_instance.dssBus.kVBase
            voltages_LL = voltages * math.sqrt(3)
            voltages_LL = round(voltages_LL, 3)
            line.setAttribute("kVBaseLL", str(voltages_LL))

            line_layer.updateFeature(line)
        line_layer.commitChanges()

        load_layer.startEditing()
        for load in load_layer.getFeatures():
            load_id = load['id']
            dss_instance.activar_elemento(f"Load.{load_id}")

            p_activa = abs(dss_instance.dssCktElement.TotalPowers[0])
            p_activa = round(p_activa, 3)
            load.setAttribute("P.Activa", str(p_activa))

            p_reactiva = abs(dss_instance.dssCktElement.TotalPowers[1])
            p_reactiva = round(p_reactiva, 3)
            load.setAttribute("P.Reactiva", str(p_reactiva))

            load_layer.updateFeature(load)
        load_layer.commitChanges()

        # Forzar la actualización del lienzo y procesar eventos
        iface.mapCanvas().refresh()
        QApplication.processEvents()
    finally:
        # Cerrar el mensaje persistente y restaurar cursor
        iface.messageBar().popWidget(handle)
        QApplication.restoreOverrideCursor()




def export_dss_location(export_dir, node_layer, line_layer, transformer_layer, generator_layer, pv_system_layer, et_layer, load_layer, switch_layer, capacitor_layer):

    # Inicializar la barra de progreso (sólo barra) y enviar mensajes a consola
    print("Exportando elementos DSS...")
    progress = QProgressBar()
    progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    iface.messageBar().pushWidget(progress, Qgis.Info)
    # Calcular el total de TIPOS de elementos a exportar
    # Tipos base (siempre se exportan aunque estén vacíos):
    base_types = 9  # Vsource, Line, Transformer, Load, Switch, Capacitor, PVSystem, Generator, Buscoords
    total_types = base_types
    # Tipos de librería opcionales: contar sólo si existen en el proyecto
    if QgsProject.instance().mapLayersByName("linecode"): total_types += 1
    if QgsProject.instance().mapLayersByName("linegeometry"): total_types += 1
    if QgsProject.instance().mapLayersByName("linespacing"): total_types += 1
    if QgsProject.instance().mapLayersByName("wiredata"): total_types += 1
    if QgsProject.instance().mapLayersByName("loadshape"): total_types += 1
    if QgsProject.instance().mapLayersByName("tshape"): total_types += 1
    if QgsProject.instance().mapLayersByName("xycurve"): total_types += 1
    if QgsProject.instance().mapLayersByName("xfmrcode"): total_types += 1

    progress.setMaximum(total_types)
    steps_done = 0

    frequency = ""
    voltbases = ""
    solu_mode = ""
    for feature in settings_layer.getFeatures():
        frequency = feature["frequency"]
        voltbases = feature["voltbases"]
        solu_mode = feature["solu_mode"]


    # Aqui crear los archivos vacios en el directorio destino:
    empty_files = [
        "Vsource.dss",
        "LineCode.dss",
        "WireData.dss",
        "LineSpacing.dss",
        "LineGeometry.dss",
        "Line.dss",
        "XfmrCode.dss",
        "Transformer.dss",
        "Switch.dss",
        "LoadShape.dss",
        "TShape.dss",
        "XYcurve.dss",
        "Load.dss",
        "Capacitor.dss",
        "PVSystem.dss",
        "Generator.dss",
        "Buscoords.csv"
    ]
    for fname in empty_files:
        fpath = os.path.join(export_dir, fname)
        if not os.path.exists(fpath):
            with open(fpath, 'w') as f:
                pass  # Crea el archivo vacío

    # Crear el archivo master.dss
    master_dss_path = os.path.join(export_dir, "Master.dss")
    with open(master_dss_path, 'w') as master_file:
        master_file.write("Clear\n")
        #master_file.write("Set DefaultBaseFrequency=50\n")
        master_file.write(f"Set DefaultBaseFrequency={frequency}\n")
        master_file.write("Redirect Vsource.dss\n")
        master_file.write("Redirect LineCode.dss\n")
        master_file.write("Redirect WireData.dss\n")
        master_file.write("Redirect LineSpacing.dss\n")
        master_file.write("Redirect LineGeometry.dss\n")
        master_file.write("Redirect Line.dss\n")
        master_file.write("Redirect XfmrCode.dss\n")
        master_file.write("Redirect Transformer.dss\n")
        master_file.write("Redirect Switch.dss\n")
        master_file.write("Redirect LoadShape.dss\n")
        master_file.write("Redirect TShape.dss\n")
        master_file.write("Redirect XYcurve.dss\n")
        master_file.write("Redirect Load.dss\n")
        master_file.write("Redirect Capacitor.dss\n")
        master_file.write("Redirect PVSystem.dss\n")
        master_file.write("Redirect Generator.dss\n")
        master_file.write(f"Set voltagebases={voltbases}\n")
        master_file.write("Calcvoltagebases\n")
        #master_file.write("set mode=Snapshot\n")
        master_file.write(f"set mode={solu_mode}\n")
        master_file.write("solve\n")
        master_file.write("LatLongCoords Buscoords.csv\n")

    # Crear los archivos DSS para los distintos elementos eléctricos
    create_vsource_dss(et_layer, export_dir)
    steps_done += 1
    progress.setValue(steps_done); QApplication.processEvents()
    create_line_dss(line_layer, export_dir)
    steps_done += 1
    progress.setValue(steps_done); QApplication.processEvents()
    create_transformer_dss(transformer_layer, export_dir)
    steps_done += 1
    progress.setValue(steps_done); QApplication.processEvents()
    create_load_dss(load_layer, export_dir)
    steps_done += 1
    progress.setValue(steps_done); QApplication.processEvents()
    create_switch_dss(switch_layer, export_dir)
    steps_done += 1
    progress.setValue(steps_done); QApplication.processEvents()
    create_capacitor_dss(capacitor_layer, export_dir)
    steps_done += 1
    progress.setValue(steps_done); QApplication.processEvents()
    create_pv_system_dss(pv_system_layer, export_dir)
    steps_done += 1
    progress.setValue(steps_done); QApplication.processEvents()
    create_generator_dss(generator_layer, export_dir)
    steps_done += 1
    progress.setValue(steps_done); QApplication.processEvents()
    create_buscoords_csv(node_layer, export_dir)
    steps_done += 1
    progress.setValue(steps_done); QApplication.processEvents()

    # Exportar librerías geométricas con mensaje y progreso

    linecode_layers = QgsProject.instance().mapLayersByName("linecode")
    if linecode_layers:
        create_linecode_dss(linecode_layers[0], export_dir)
        steps_done += 1
        progress.setValue(steps_done); QApplication.processEvents()
    else:
        print("No se encontró la capa 'linecode'")

    linegeometry_layers = QgsProject.instance().mapLayersByName("linegeometry")
    if linegeometry_layers:
        create_linegeometry_dss(linegeometry_layers[0], export_dir)
        steps_done += 1
        progress.setValue(steps_done); QApplication.processEvents()
    else:
        print("No se encontró la capa 'linegeometry'")

    linespacing_layers = QgsProject.instance().mapLayersByName("linespacing")
    if linespacing_layers:
        create_linespacing_dss(linespacing_layers[0], export_dir)
        steps_done += 1
        progress.setValue(steps_done); QApplication.processEvents()
    else:
        print("No se encontró la capa 'linespacing'")

    wiredata_layers = QgsProject.instance().mapLayersByName("wiredata")
    if wiredata_layers:
        create_wiredata_dss(wiredata_layers[0], export_dir)
        steps_done += 1
        progress.setValue(steps_done); QApplication.processEvents()
    else:
        print("No se encontró la capa 'wiredata'")

    loadshape_layers = QgsProject.instance().mapLayersByName("loadshape")
    if loadshape_layers:
        loadshape_layer = loadshape_layers[0]
        create_loadshape_dss(loadshape_layer, export_dir)
        steps_done += 1
        progress.setValue(steps_done); QApplication.processEvents()
    else:
        print("No se encontró la capa 'loadshape'")

    tshape_layers = QgsProject.instance().mapLayersByName("tshape")
    if tshape_layers:
        tshape_layer = tshape_layers[0]
        create_tshape_dss(tshape_layer, export_dir)
        steps_done += 1
        progress.setValue(steps_done); QApplication.processEvents()
    else:
        print("No se encontró la capa 'tshape'")

    xycurve_layers = QgsProject.instance().mapLayersByName("xycurve")
    if xycurve_layers:
        xycurve_layer = xycurve_layers[0]
        create_xycurve_dss(xycurve_layer, export_dir)
        steps_done += 1
        progress.setValue(steps_done); QApplication.processEvents()
    else:
        print("No se encontró la capa 'xycurve'")

    xfmrcode_layers = QgsProject.instance().mapLayersByName("xfmrcode")
    if xfmrcode_layers:
        xfmrcode_layer = xfmrcode_layers[0]
        create_xfmrcode_dss(xfmrcode_layer, export_dir)
        steps_done += 1
        progress.setValue(steps_done); QApplication.processEvents()
    else:
        print("No se encontró la capa 'xfmrcode'")


    iface.messageBar().clearWidgets()  # Limpiar la barra de mensajes
    print("Exportación a OpenDSS completada.")


# === Función auxiliar para exportación de buses con fases ===
def format_bus(base_name, phases_str):
    """Devuelve el nombre de bus en notación OpenDSS: base.1.2.3, base.2.3, etc."""
    if not phases_str or str(phases_str).strip() == '' or str(phases_str) == '123':
        return f"{base_name}.1.2.3"
    return f"{base_name}." + ".".join(str(phases_str))


def create_xfmrcode_dss(xfmrcode_layer, output_directory):
    """Genera el archivo XfmrCode.dss a partir de la capa xfmrcode."""
    import os

    if not xfmrcode_layer:
        print("Capa xfmrcode no disponible.")
        return

    output_path = os.path.join(output_directory, "XfmrCode.dss")
    with open(output_path, 'w') as file:
        for feature in xfmrcode_layer.getFeatures():
            name = feature['id']
            if not name:
                continue
            line = f'New XfmrCode.{name}'

            # Agregar atributos si existen
            def append_param(attr, key=None, wrap_list=False):
                value = feature[attr]
                if value not in [None, '', 'NULL']:
                    val = str(value).strip()
                    if wrap_list and not val.startswith('['):
                        val = f"[{val}]"
                    return f" {key or attr}={val}"
                return ''

            line += append_param("phases")
            line += append_param("windings")
            line += append_param("kvs", wrap_list=True)
            line += append_param("kvas", wrap_list=True)
            line += append_param("conns", wrap_list=True)
            line += append_param("%rs")
            line += append_param("xhl")
            line += append_param("xht")
            line += append_param("xlt")
            line += append_param("maxtap")
            line += append_param("mintap")
            line += append_param("%loadloss")
            line += append_param("%nloadloss")
            line += append_param("ppm_afloat")
            line += append_param("%imag")

            file.write(line + '\n')

    print(f"Archivo XfmrCode.dss generado")



def create_loadshape_dss(loadshape_layer, output_dir):
    """
    Genera LoadShape.dss a partir de *loadshape_layer*.

    • No se exporta el parámetro csvfile bajo ninguna circunstancia.
    • Se añaden npts=…, interval=… y mult=… solo si contienen
      un valor distinto de NULL / cadena vacía.
    """

    if not loadshape_layer or loadshape_layer.featureCount() == 0:
        print("La capa LoadShape está vacía o no se encontró.")
        return

    filepath = os.path.join(output_dir, "LoadShape.dss")
    with open(filepath, "w", encoding="utf-8") as f:
        for feat in loadshape_layer.getFeatures():
            name     = str(feat["id"]).strip()
            npts     = feat["npts"]
            interval = feat["interval"]
            mult     = feat["mult"]

            params = []

            if npts and str(npts).strip().lower() != "null":
                params.append(f"npts={npts}")

            if interval and str(interval).strip().lower() != "null":
                params.append(f"interval={interval}")

            # mult debe figurar siempre que haya algún dato útil
            if mult and str(mult).strip().lower() != "null":
                params.append(f"mult={mult}")

            # Construcción de la línea DSS
            linea = " ".join(["New LoadShape." + name] + params).strip() + "\n"
            f.write(linea)

    print(f"Archivo LoadShape.dss generado")



def create_tshape_dss(tshape_layer, output_dir):
    if not tshape_layer or tshape_layer.featureCount() == 0:
        print("La capa TShape está vacía o no se encontró.")
        return

    filepath = os.path.join(output_dir, "TShape.dss")
    with open(filepath, "w") as f:
        for feature in tshape_layer.getFeatures():
            name = feature["id"]
            npts = feature["npts"]
            temp = feature["temp"]
            csvfile = feature["csvfile"]

            # if csvfile and csvfile.strip().lower() != "null":
            #     line = f"New TShape.{name} npts={npts} csvfile={csvfile}\n"
            # else:
            #     line = f"New TShape.{name} npts={npts} temp={temp}\n"

            line = f"New TShape.{name} npts={npts} temp={temp}\n"
            f.write(line)

    print(f"Archivo TShape.dss generado")

def create_xycurve_dss(xycurve_layer, output_dir):
    if not xycurve_layer or xycurve_layer.featureCount() == 0:
        print("La capa XYcurve está vacía o no se encontró.")
        return

    filepath = os.path.join(output_dir, "XYcurve.dss")
    with open(filepath, "w") as f:
        for feature in xycurve_layer.getFeatures():
            name = feature["id"]
            npts = feature["npts"]
            points = feature["points"]
            csvfile = feature["csvfile"]

            # Los puntos ya vienen con corchetes, solo necesitamos extraer el contenido
            points_content = points.strip('[]')
            line = f"New XYcurve.{name} npts={npts} Points=[{points_content}]\n"
            f.write(line)

    print(f"Archivo XYcurve.dss generado")

def create_linecode_dss(linecode_layer, folder_path):
    output_path = os.path.join(folder_path, "LineCode.dss")

    with open(output_path, 'w') as f:
        if linecode_layer.featureCount() == 0:
            pass
        else:
            for feat in linecode_layer.getFeatures():
                name = feat["id"]
                nphases = feat["nphases"]
                r1 = feat["r1"]
                r0 = feat["r0"]
                x1 = feat["x1"]
                x0 = feat["x0"]
                c1 = feat["c1"]
                c0 = feat["c0"]
                f.write(f"New LineCode.{name} nphases={nphases} r1={r1} x1={x1} r0={r0} x0={x0} c1={c1} c0={c0}\n")

    print(f"Archivo LineCode.dss generado")


def create_linegeometry_dss(linegeometry_layer, folder_path):
    output_path = os.path.join(folder_path, "LineGeometry.dss")
    with open(output_path, 'w') as f:
        if linegeometry_layer.featureCount() == 0:
            pass
        else:
            for feat in linegeometry_layer.getFeatures():
                name = feat["id"]
                nconds = feat["nconds"]
                nphases = feat["nphases"]
                spacing = feat["spacing"]
                wires = feat["wires"]

                # Obtener el valor de 'reduce' si existe en la definición de la capa.  Si
                # el campo no está presente o su valor es None, dejarlo como cadena vacía.
                reduce_val = ''
                if "reduce" in [field.name() for field in linegeometry_layer.fields()]:
                    value = feat["reduce"]
                    if value is not None:
                        # Normalizar el valor a minúsculas para mantener un patrón consistente
                        reduce_val = str(value).lower()

                # Construir la línea DSS.  Incluir el parámetro 'reduce' sólo si tiene un
                # valor no vacío.  Esto mantiene la compatibilidad con OpenDSS cuando el
                # parámetro es opcional.
                dss_parts = [
                    f"New LineGeometry.{name}",
                    f"nconds={nconds}",
                    f"nphases={nphases}",
                    f"spacing={spacing}",
                    f"wires={wires}"
                ]
                if reduce_val not in (None, '', 'NULL'):
                    dss_parts.append(f"reduce={reduce_val}")
                dss_line = ' '.join(dss_parts) + "\n"
                f.write(dss_line)

    print(f"Archivo LinLineGeometr.dss generado")

def create_linespacing_dss(linespacing_layer, folder_path):
    output_path = os.path.join(folder_path, "LineSpacing.dss")
    with open(output_path, 'w') as f:
        if linespacing_layer.featureCount() == 0:
            pass
        else:
            for feat in linespacing_layer.getFeatures():
                name = feat["id"]
                nconds = feat["nconds"]
                nphases = feat["nphases"]
                units = feat["units"]
                x = feat["x"]
                h = feat["h"]
                f.write(f"New LineSpacing.{name} nconds={nconds} nphases={nphases} units={units} x={x} h={h}\n")

    print(f"Archivo LineSpacing.dss generado")

def create_wiredata_dss(wiredata_layer, folder_path):
    output_path = os.path.join(folder_path, "WireData.dss")
    with open(output_path, 'w') as f:
        if wiredata_layer.featureCount() == 0:
            pass
        else:
            for feat in wiredata_layer.getFeatures():
                name = feat["id"]
                rdc = feat["Rdc"]
                runits = feat["Runits"]
                diam = feat["diam"]
                radunits = feat["Radunits"]
                emergamps = feat["emergamps"]
                f.write(f"New WireData.{name} Rdc={rdc} Runits={runits} diam={diam} Radunits={radunits} emergamps={emergamps}\n")

    print(f"Archivo WireData.dss generado")


def create_vsource_dss(et_layer, folder_path):
    vsource_dss_path = os.path.join(folder_path, "Vsource.dss")
    with open(vsource_dss_path, 'w') as file:
        first = True
        for feature in et_layer.getFeatures():
            id = feature["id"]
            start_node = feature["start_node"]
            start_ph = feature["start_ph"] if "start_ph" in feature.fields().names() else ''
            bus1 = format_bus(start_node, start_ph)
            pu = feature["pu"]
            basekv = feature["basekv"]
            r1 = feature["r1"]
            r0 = feature["r0"]
            x1 = feature["x1"]
            x0 = feature["x0"]
            phases = feature["phases"] if "phases" in feature.fields().names() else ''
            if first:
                file.write(f"New Circuit.{id} bus1={bus1} pu={pu} basekv={basekv} r1={r1} r0={r0} x1={x1} x0={x0} phases={phases}\n")
                first = False
            else:
                file.write(f"New Vsource.{id} bus1={bus1} pu={pu} basekv={basekv} r1={r1} r0={r0} x1={x1} x0={x0} phases={phases}\n")

    print(f"Archivo Vsource.dss generado")


def create_line_dss(line_layer, folder_path):
    line_dss_path = os.path.join(folder_path, "Line.dss")
    with open(line_dss_path, 'w') as file:
        for feature in line_layer.getFeatures():
            id = feature["id"]
            start_node = feature["start_node"]
            end_node = feature["end_node"]
            start_ph = feature["start_ph"] if "start_ph" in feature.fields().names() else ''
            end_ph = feature["end_ph"] if "end_ph" in feature.fields().names() else ''
            bus1 = format_bus(start_node, start_ph)
            bus2 = format_bus(end_node, end_ph)
            length = feature["length"]
            units = feature["units"]
            r1 = feature["r1"]
            r0 = feature["r0"]
            x1 = feature["x1"]
            x0 = feature["x0"]
            c1 = feature["c1"]
            c0 = feature["c0"]
            phases = feature["phases"]
            linecode = feature["linecode"]
            geometry = feature["geometry"]

            ### Las unidades "units" se debe mantener en metros ya que la longitud de linea se calcula en esa unidad
            if linecode and linecode.strip().lower() != "null":
                # (2025-08-18) Se elimina el atributo 'enabled' de líneas del DSS
                file.write(f"New Line.{id} bus1={bus1} bus2={bus2} length={length} units=m phases={phases} linecode={linecode}\n")
                #file.write(f"New Line.{id} bus1={bus1} bus2={bus2} length={length} units={units} enabled={enabled} phases={phases} linecode={linecode}\n")
            elif geometry and geometry.strip().lower() != "null":
                file.write(f"New Line.{id} bus1={bus1} bus2={bus2} length={length} Geometry={geometry} units=m phases={phases}\n")
                #file.write(f"New Line.{id} bus1={bus1} bus2={bus2} length={length} Geometry={geometry} units={units} phases={phases}\n")
            else:
                # (2025-08-18) Se elimina el atributo 'enabled' de líneas del DSS
                file.write(f"New Line.{id} bus1={bus1} bus2={bus2} length={length} units=m r1={r1} r0={r0} x1={x1} x0={x0} c1={c1} c0={c0} phases={phases}\n")
                #file.write(f"New Line.{id} bus1={bus1} bus2={bus2} length={length} units={units} r1={r1} r0={r0} x1={x1} x0={x0} c1={c1} c0={c0} enabled={enabled} phases={phases}\n")
    print(f"Archivo Line.dss generado")



def create_transformer_dss(transformer_layer, folder_path):
    transformer_dss_path = os.path.join(folder_path, "Transformer.dss")
    with open(transformer_dss_path, 'w') as file:
        for feature in transformer_layer.getFeatures():
            id = feature["id"]
            wdg1_node = feature["wdg1_node"]
            wdg2_node = feature["wdg2_node"]
            wdg1_ph = feature["wdg1_ph"] if "wdg1_ph" in feature.fields().names() else ''
            wdg2_ph = feature["wdg2_ph"] if "wdg2_ph" in feature.fields().names() else ''
            bus1 = format_bus(wdg1_node, wdg1_ph)
            bus2 = format_bus(wdg2_node, wdg2_ph)
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
            xfmrcode = feature["xfmrcode"]
            tap = feature["tap"]
            nwindings = feature["nwindings"]            

            #file.write(f"New Transformer.{id} phases={phases} wdg=1 bus={bus1} kv={kv1} kVA={kva1} wdg=2 bus={bus2} kv={kv2} kVA={kva2} %imag={percent_imag} %loadloss={percent_loadloss} %noloadloss={percent_noloadloss} XHL={xhl} conns={conns} ppm_antifloat={ppm_antifloat}\n")

            if xfmrcode and xfmrcode.strip().lower() != "null":
                file.write(f"New Transformer.{id} tap={tap} wdg=1 bus={bus1} wdg=2 bus={bus2} xfmrcode={xfmrcode}\n")
            else:
                file.write(f"New Transformer.{id} phases={phases} wdg=1 bus={bus1} kv={kv1} kVA={kva1} wdg=2 bus={bus2} kv={kv2} kVA={kva2} %imag={percent_imag} %loadloss={percent_loadloss} %noloadloss={percent_noloadloss} XHL={xhl} conns={conns} ppm_antifloat={ppm_antifloat}\n")
            
    print(f"Archivo Transformer.dss generado")

def create_load_dss(load_layer, folder_path):
    load_dss_path = os.path.join(folder_path, "Load.dss")
    with open(load_dss_path, 'w') as file:
        for feature in load_layer.getFeatures():
            id = feature["id"]
            start_node = feature["start_node"]
            start_ph = feature["start_ph"] if "start_ph" in feature.fields().names() else ''
            bus1 = format_bus(start_node, start_ph)
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

            if daily and daily.strip().lower() != "null":
                file.write(f"New Load.{id} phases={phases} bus1={bus1} kv={kv} kw={kw} pf={pf} status={status} model={model} CVRwatts={cvrwatts} CVRvars={cvrvars} class={class_type} daily={daily} conn={conn}\n")
            else:
                file.write(f"New Load.{id} phases={phases} bus1={bus1} kv={kv} kw={kw} pf={pf} status={status} model={model} CVRwatts={cvrwatts} CVRvars={cvrvars} class={class_type} conn={conn}\n")

    print(f"Archivo Load.dss generado")

def create_capacitor_dss(capacitor_layer, folder_path):
    capacitor_dss_path = os.path.join(folder_path, "Capacitor.dss")
    with open(capacitor_dss_path, 'w') as file:
        for feature in capacitor_layer.getFeatures():
            id = feature["id"]
            start_node = feature["start_node"]
            start_ph = feature["start_ph"] if "start_ph" in feature.fields().names() else ''
            bus1 = format_bus(start_node, start_ph)
            kv = feature["kv"]
            kvar = feature["kvar"]
            phases = feature["phases"]
            file.write(f"New Capacitor.{id} bus1={bus1} kv={kv} kvar={kvar} phases={phases}\n")

    print(f"Archivo Capacitor.dss generado")

def create_generator_dss(generator_layer, folder_path):
    generator_dss_path = os.path.join(folder_path, "Generator.dss")
    with open(generator_dss_path, 'w') as file:
        for feature in generator_layer.getFeatures():
            id = feature["id"]
            start_node = feature["start_node"]
            start_ph = feature["start_ph"] if "start_ph" in feature.fields().names() else ''
            bus1 = format_bus(start_node, start_ph)
            kv = feature["kV"]
            kw = feature["kW"]
            pf = feature["PF"]
            daily = feature["daily"]
            phases = feature["Phases"] if "Phases" in feature.fields().names() else feature["phases"]
            file.write(f"New Generator.{id} bus1={bus1} phases={phases} kv={kv} kw={kw} pf={pf} daily={daily}\n")

    print(f"Archivo Generator.dss generado")

def create_pv_system_dss(pv_system_layer, folder_path):
    pv_system_dss_path = os.path.join(folder_path, "PVSystem.dss")
    with open(pv_system_dss_path, 'w') as file:
        for feature in pv_system_layer.getFeatures():
            id = feature["id"]
            start_node = feature["start_node"]
            start_ph = feature["start_ph"] if "start_ph" in feature.fields().names() else ''
            bus1 = format_bus(start_node, start_ph)
            irradiance = feature["Irradiance"]
            pmpp = feature["Pmpp"]
            kv = feature["kv"]
            temperature = feature["Temperatur"]
            kva = feature["kVA"]
            effcurve = feature["EffCurve"]
            daily = feature["daily"]
            tdaily = feature["Tdaily"]
            phases = feature["phases"]
            file.write(f"New PVSystem.{id} phases={phases} bus1={bus1} kv={kv} irradiance={irradiance} pmpp={pmpp} temperature={temperature} kva={kva} effcurve={effcurve} daily={daily} tdaily={tdaily}\n")

    print(f"Archivo PVSystem.dss generado")

def create_switch_dss(switch_layer, folder_path):
    switch_dss_path = os.path.join(folder_path, "Switch.dss")
    with open(switch_dss_path, 'w') as file:
        for feature in switch_layer.getFeatures():
            id = feature["id"]
            line = feature["line"]
            terminal = feature["terminal"]
            state = feature["State"]
            file.write(f"New Relay.{id} MonitoredObj=Line.{line} MonitoredTerm={terminal} State={state}\n")

    print(f"Archivo Switch.dss generado")

def create_buscoords_csv(node_layer, folder_path):
    buscoords_csv_path = os.path.join(folder_path, "Buscoords.csv")
    with open(buscoords_csv_path, 'w') as file:
        for feature in node_layer.getFeatures():
            
            node_id = feature["id"]
            geom = feature.geometry().asPoint()
            x, y = geom.x(), geom.y()
            file.write(f"{node_id},{y},{x}\n")

    print(f"Archivo Buscoords.dss generado")

# ********** Funciones para limpieza de capas *************

def clear_all_layers():
    # Start editing the layers
    clear_settings_layer()
    clear_loadshape_layer()
    clear_linecode_layer()
    clear_linegeometry_layer()
    clear_linespacing_layer()
    clear_wiredata_layer()
    clear_node_layer()
    clear_line_layer()
    clear_generator_layer()
    clear_pv_system_layer()
    clear_load_layer()
    clear_capacitor_layer()
    clear_switch_layer()
    clear_transformer_layer()
    clear_et_layer()
    clear_xycurve_layer()
    clear_tshape_layer()
    clear_xfmrcode_layer()

def clear_xfmrcode_layer():
    xfmrcode_layer.startEditing()
    xfmrcode_layer.dataProvider().truncate()
    xfmrcode_layer.commitChanges()

def clear_settings_layer():
    settings_layer.startEditing()
    settings_layer.dataProvider().truncate()
    settings_layer.commitChanges()

def clear_loadshape_layer():
    loadshape_layer.startEditing()
    loadshape_layer.dataProvider().truncate()
    loadshape_layer.commitChanges()

def clear_linecode_layer():
    linecode_layer.startEditing()
    linecode_layer.dataProvider().truncate()
    linecode_layer.commitChanges()

def clear_linegeometry_layer():
    linegeometry_layer.startEditing()
    linegeometry_layer.dataProvider().truncate()
    linegeometry_layer.commitChanges()

def clear_linespacing_layer():
    linespacing_layer.startEditing()
    linespacing_layer.dataProvider().truncate()
    linespacing_layer.commitChanges()

def clear_wiredata_layer():
    wiredata_layer.startEditing()
    wiredata_layer.dataProvider().truncate()
    wiredata_layer.commitChanges()

def clear_node_layer():
    node_layer.startEditing()
    node_layer.dataProvider().truncate()
    node_layer.commitChanges()

def clear_line_layer():
    line_layer.startEditing()
    line_layer.dataProvider().truncate()
    line_layer.commitChanges()

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

def clear_xycurve_layer():
    xycurve_layers = QgsProject.instance().mapLayersByName("xycurve")
    if xycurve_layers:
        xycurve_layer = xycurve_layers[0]
        xycurve_layer.startEditing()
        xycurve_layer.deleteFeatures([f.id() for f in xycurve_layer.getFeatures()])
        xycurve_layer.commitChanges()

def clear_tshape_layer():
    tshape_layers = QgsProject.instance().mapLayersByName("tshape")
    if tshape_layers:
        tshape_layer = tshape_layers[0]
        tshape_layer.startEditing()
        tshape_layer.deleteFeatures([f.id() for f in tshape_layer.getFeatures()])
        tshape_layer.commitChanges()

def reduce_network():
    # Start editing the layers
    print("Starting network reduction...")
    node_layer.startEditing()
    line_layer.startEditing()
    
    # Step 1: Identify connections of nodes
    node_connections = {}
    for line in line_layer.getFeatures():
        start_node = line['start_node']
        end_node = line['end_node']
        if start_node not in node_connections:
            node_connections[start_node] = []
        if end_node not in node_connections:
            node_connections[end_node] = []
        node_connections[start_node].append(line)
        node_connections[end_node].append(line)    
    print(f"Identified {len(node_connections)} nodes with connections.")

    # Define layers for other elements associated with nodes
    associated_layers = [
        generator_layer,
        pv_system_layer,
        load_layer,
        capacitor_layer,
        et_layer
    ]    
    # Define special layers that use "wdg1_node" and "wdg2_node" for node linkage
    special_layers = {
        transformer_layer: ["wdg1_node", "wdg2_node"]
    }

    nodes_processed = 0
    nodes_eliminated = 0    

    # Step 2: Process each node to determine if it can be eliminated
    for node_id, lines in node_connections.items():

        nodes_processed += 1    

        # Condition 1: Node must connect exactly two lines
        if len(lines) != 2:
            print(f"Node {node_id} skipped - not exactly 2 connections (has {len(lines)})")
            continue
        line1, line2 = lines    

        # Condition 2a: Lines must have the same 'r1' attribute
        if line1['r1'] != line2['r1']:
            print(f"Node {node_id} skipped - connected lines have different 'r1' values ({line1['r1']} vs {line2['r1']}).")
            continue

        # Condition 2: Check if node is associated with any element from specified layers
        associated_with_elements = False
        associated_elements_details = []

        # Check association in regular layers
        for layer in associated_layers:
            features = layer.getFeatures(QgsFeatureRequest(QgsExpression(f'\"start_node\"=\'{node_id}\' OR \"end_node\"=\'{node_id}\'')))
            if any(features):
                associated_with_elements = True
                associated_elements_details.append(layer.name())  

        # Check association in special layers
        for layer, link_fields in special_layers.items():
            for link_field in link_fields:
                features = layer.getFeatures(QgsFeatureRequest(QgsExpression(f'\"{link_field}\"=\'{node_id}\'')))
                if any(features):
                    associated_with_elements = True
                    associated_elements_details.append(f"{layer.name()} ({link_field})")
        if associated_with_elements:
            print(f"Node {node_id} skipped - associated with electrical elements in layers: {', '.join(associated_elements_details)}")
            continue
           
        # Condition 3: Check if either of the lines contain switches
        has_switch = any(
            switch['line'] == line1['id'] or switch['line'] == line2['id']
            for switch in switch_layer.getFeatures()
        )
        if has_switch:
            print(f"Node {node_id} skipped - associated lines have switches.")
            continue
        
        # Step 3: Merge lines and remove the node
        start_node = line1['start_node'] if line1['start_node'] != node_id else line1['end_node']
        end_node = line2['start_node'] if line2['start_node'] != node_id else line2['end_node']
        
        # Find the start and end node features
        start_node_feature = find_node_by_uuid(node_layer, start_node)
        end_node_feature = find_node_by_uuid(node_layer, end_node)
        
        if start_node_feature and end_node_feature:
            print(f"Node {node_id} will be removed - merging lines.")
            # Create new line feature that merges the two lines
            new_line = QgsFeature(line_layer.fields())
            new_line.setGeometry(QgsGeometry.fromPolylineXY([
                QgsPointXY(start_node_feature.geometry().asPoint()),
                QgsPointXY(end_node_feature.geometry().asPoint())
            ]))
            new_line.setAttributes(line1.attributes())
            new_line['start_node'] = start_node
            new_line['end_node'] = end_node
            new_line['length'] = float(line1['length']) + float(line2['length'])
            
            # Add new line and remove old lines
            line_layer.addFeature(new_line)
            line_layer.deleteFeature(line1.id())
            line_layer.deleteFeature(line2.id())
            
            # Remove the node
            node_layer.deleteFeature(find_node_by_uuid(node_layer, node_id).id())
            nodes_eliminated += 1
        else:
            print(f"Error: Could not find start or end node features for node {node_id}.")
    
    # Commit changes to layers
    node_layer.commitChanges()
    line_layer.commitChanges()
    
    print(f"Network reduction completed. Nodes processed: {nodes_processed}, Nodes eliminated: {nodes_eliminated}")




# *************INICIO DEL PROGRAMA PRINCIPAL *********************
# Obtener la capa de nodos y la capa de líneas del proyecto
node_layer_name = "nodos"
line_layer_name = "lineas"
generator_layer_name = "generadores"
pv_system_layer_name = "sistemas_fotovoltaicos"
load_layer_name = "cargas"
capacitor_layer_name = "capacitores"
switch_layer_name = "interruptores"
transformer_layer_name = "transformadores"
et_layer_name = "estacion_transformadora"
linecode_layer_name = "linecode"
linegeometry_layer_name = "linegeometry"
linespacing_layer_name = "linespacing"
wiredata_layer_name = "wiredata"
loadshape_layer_name = "loadshape"
settings_layer_name = "settings"
xfmrcode_layer_name = "xfmrcode"


node_layer = QgsProject.instance().mapLayersByName(node_layer_name)[0]
line_layer = QgsProject.instance().mapLayersByName(line_layer_name)[0]
generator_layer = QgsProject.instance().mapLayersByName(generator_layer_name)[0]
pv_system_layer = QgsProject.instance().mapLayersByName(pv_system_layer_name)[0]
load_layer = QgsProject.instance().mapLayersByName(load_layer_name)[0]
capacitor_layer = QgsProject.instance().mapLayersByName(capacitor_layer_name)[0]
switch_layer = QgsProject.instance().mapLayersByName(switch_layer_name)[0]
transformer_layer = QgsProject.instance().mapLayersByName(transformer_layer_name)[0]
et_layer = QgsProject.instance().mapLayersByName(et_layer_name)[0]
linecode_layer = QgsProject.instance().mapLayersByName(linecode_layer_name)[0]
linegeometry_layer = QgsProject.instance().mapLayersByName(linegeometry_layer_name)[0]
linespacing_layer = QgsProject.instance().mapLayersByName(linespacing_layer_name)[0]
wiredata_layer = QgsProject.instance().mapLayersByName(wiredata_layer_name)[0]
loadshape_layer = QgsProject.instance().mapLayersByName(loadshape_layer_name)[0]
settings_layer = QgsProject.instance().mapLayersByName(settings_layer_name)[0]
xfmrcode_layer = QgsProject.instance().mapLayersByName(xfmrcode_layer_name)[0]



# Crear una instancia de la herramienta personalizada
custom_map_tool = CustomMapTool(iface.mapCanvas(), node_layer, line_layer, generator_layer, pv_system_layer, load_layer, switch_layer, transformer_layer, et_layer, capacitor_layer)
iface.mapCanvas().setMapTool(custom_map_tool)

# Crear una instancia de la clase y mostrar la caja de herramientas
custom_toolbar_panel = CustomToolbarPanel(custom_map_tool, node_layer, line_layer, generator_layer,pv_system_layer, load_layer, switch_layer, transformer_layer, et_layer, capacitor_layer)
custom_toolbar_panel.init_panel()

# Agregar la caja de herramientas a la barra de herramientas principal
iface.addToolBar(custom_toolbar_panel.toolbox)






