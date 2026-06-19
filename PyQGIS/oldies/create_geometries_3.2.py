# Importar módulos necesarios
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsSvgMarkerSymbolLayer, QgsSymbol, QgsSimpleLineSymbolLayer,\
      QgsRendererCategory, QgsCategorizedSymbolRenderer, QgsSimpleMarkerSymbolLayer, QgsSingleSymbolRenderer, QgsMarkerSymbol,\
          QgsMarkerLineSymbolLayer, QgsLineSymbolLayer, QgsGeometryGeneratorSymbolLayer, QgsCoordinateReferenceSystem
from PyQt5.QtCore import QVariant, QPointF, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QInputDialog

# Función para seleccionar el SRC
def seleccionar_src():
    crs_list = [
        "EPSG:4326",  # WGS 84
        "EPSG:22182", # POSGAR 94 / Argentina 2
        # "EPSG:3857",  # Pseudo-Mercator
        # "EPSG:32633", # WGS 84 / UTM zone 33N
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

# Obtener la ruta del proyecto
project_path = QgsProject.instance().homePath()

# Crear capa de nodos MT
node_mt_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "nodos_mt", "memory")
node_mt_layer_provider = node_mt_layer.dataProvider()
node_mt_layer_provider.addAttributes([QgsField("id", QVariant.String)])
node_mt_layer.updateFields()

# Guardar la capa de nodos MT como Shapefile en la ruta del proyecto
node_mt_layer_path = project_path + '/nodos_mt.shp'
QgsVectorFileWriter.writeAsVectorFormat(node_mt_layer, node_mt_layer_path, 'utf-8', node_mt_layer.crs(), 'ESRI Shapefile')

# Crear capa de nodos BT
node_bt_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "nodos_bt", "memory")
node_bt_layer_provider = node_bt_layer.dataProvider()
node_bt_layer_provider.addAttributes([QgsField("id", QVariant.String)])
node_bt_layer.updateFields()

# Guardar la capa de nodos BT como Shapefile en la ruta del proyecto
node_bt_layer_path = project_path + '/nodos_bt.shp'
QgsVectorFileWriter.writeAsVectorFormat(node_bt_layer, node_bt_layer_path, 'utf-8', node_bt_layer.crs(), 'ESRI Shapefile')

# Crear capa de líneas MT
line_mt_layer = QgsVectorLayer(f"LineString?crs={crs.authid()}", "lineas_mt", "memory")
line_mt_layer_provider = line_mt_layer.dataProvider()
line_mt_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("start_node", QVariant.String),
    QgsField("end_node", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("length", QVariant.String),
    QgsField("units", QVariant.String),
    QgsField("r1", QVariant.String),
    QgsField("r0", QVariant.String),
    QgsField("x1", QVariant.String),
    QgsField("x0", QVariant.String),
    QgsField("c1", QVariant.String),
    QgsField("c0", QVariant.String),
    QgsField("phases", QVariant.String),
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("enabled", QVariant.String)
    #******<Parametros adicionales**************
    #QgsField("rg", QVariant.String),
    #QgsField("rho", QVariant.String),
    #QgsField("seasonrating", QVariant.String),
    #QgsField("xg", QVariant.String),    
    #QgsField("linecode", QVariant.String),
    #QgsField("geometry", QVariant.String),
    #QgsField("spacing", QVariant.String),
    #QgsField("normamps", QVariant.String),
    #QgsField("emergamps", QVariant.String)
    #******>Parametros***************
])
line_mt_layer.updateFields()

# Guardar la capa de líneas MT como Shapefile en la ruta del proyecto
line_mt_layer_path = project_path + '/lineas_mt.shp'
QgsVectorFileWriter.writeAsVectorFormat(line_mt_layer, line_mt_layer_path, 'utf-8', line_mt_layer.crs(), 'ESRI Shapefile')

# Crear capa de líneas BT
line_bt_layer = QgsVectorLayer(f"LineString?crs={crs.authid()}", "lineas_bt", "memory")
line_bt_layer_provider = line_bt_layer.dataProvider()
line_bt_layer_provider.addAttributes([QgsField("id", QVariant.String), QgsField("start_node", QVariant.String), QgsField("end_node", QVariant.String)])
line_bt_layer.updateFields()

# Guardar la capa de líneas BT como Shapefile en la ruta del proyecto
line_bt_layer_path = project_path + '/lineas_bt.shp'
QgsVectorFileWriter.writeAsVectorFormat(line_bt_layer, line_bt_layer_path, 'utf-8', line_bt_layer.crs(), 'ESRI Shapefile')

# Crear capa de puntos para generadores
generator_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "generadores", "memory")
generator_layer_provider = generator_layer.dataProvider()
generator_layer_provider.addAttributes([QgsField("id", QVariant.String), QgsField("start_node", QVariant.String)])
generator_layer.updateFields()

# Guardar la capa de puntos de generadores como Shapefile en la ruta del proyecto
generator_layer_path = project_path + '/generadores.shp'
QgsVectorFileWriter.writeAsVectorFormat(generator_layer, generator_layer_path, 'utf-8', generator_layer.crs(), 'ESRI Shapefile')

# Crear capa de puntos para cargas
load_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "cargas", "memory")
load_layer_provider = load_layer.dataProvider()
load_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("start_node", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("kv", QVariant.String),
    QgsField("kw", QVariant.String),
    QgsField("pf", QVariant.String),
    QgsField("status", QVariant.String),
    QgsField("model", QVariant.String),
    QgsField("cvrwatts", QVariant.String),
    QgsField("cvrvars", QVariant.String),
    QgsField("class", QVariant.String),
    QgsField("daily", QVariant.String),
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("phases", QVariant.String),
    QgsField("conn", QVariant.String)
    #******<Parametros adicionales**************
    #'allocationfactor',
    #'CVRcurve',
    #'Cfactor',
    #'growth',
    #'IsDelta',
    #'PctMean',
    #'PctStdDev',
    #'RelWeight',
    #'Rneut',
    #'Sensor',
    #'Spectrum',
    #'Status',
    #'Vmaxpu',
    #'Vminemerg',
    #'Vminnorm',
    #'Vminpu',
    #'Xneut',
    #'yearly',
    #'duty',
    #'idx',
    #'kva',
    #'kvar',
    #'kwh',
    #'kwhdays',
    #'pctSeriesRL',
    #'xfkVA',
    #******>Parametros***************
])
load_layer.updateFields()


# Guardar la capa de puntos de cargas como Shapefile en la ruta del proyecto
load_layer_path = project_path + '/cargas.shp'
QgsVectorFileWriter.writeAsVectorFormat(load_layer, load_layer_path, 'utf-8', load_layer.crs(), 'ESRI Shapefile')

# Crear capa de puntos para interruptores
switch_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "interruptores", "memory")
switch_layer_provider = switch_layer.dataProvider()
switch_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("line", QVariant.String),
    QgsField("terminal", QVariant.String),
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("State", QVariant.String)
    #******<Parametros adicionales**************
    # QgsField("NormalState", QVariant.String)
    # QgsField("State", QVariant.String) --> Figura un valor numérico
    #******>Parametros***************
])
switch_layer.updateFields()


# Guardar la capa de puntos de interruptores como Shapefile en la ruta del proyecto
switch_layer_path = project_path + '/interruptores.shp'
QgsVectorFileWriter.writeAsVectorFormat(switch_layer, switch_layer_path, 'utf-8', switch_layer.crs(), 'ESRI Shapefile')

# Crear capa de puntos para transformadores
transformer_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "transformadores", "memory")
transformer_layer_provider = transformer_layer.dataProvider()
transformer_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("wdg1_node", QVariant.String),
    QgsField("wdg2_node", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("kv1", QVariant.String),
    QgsField("kva1", QVariant.String),
    QgsField("kv2", QVariant.String),
    QgsField("kva2", QVariant.String),
    QgsField("xhl", QVariant.String),
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("phases", QVariant.String),
    QgsField("%imag", QVariant.String),
    QgsField("%loadloss", QVariant.String),
    QgsField("%nloadloss", QVariant.String),
    QgsField("conns", QVariant.String),
    QgsField("ppm_afloat", QVariant.String)
    #******<Parametros adicionales**************
    #QgsField("coretype", QVariant.String),
    #QgsField("isdelta", QVariant.String),
    #QgsField("maxtap", QVariant.String),
    #QgsField("mintap", QVariant.String),
    #QgsField("numtaps", QVariant.String),
    #QgsField("numwindings", QVariant.String),
    #QgsField("r", QVariant.String),
    #QgsField("rdcohms1", QVariant.String), #<-depende del Wdg
    #QgsField("rdcohms2", QVariant.String), #<-depende del Wdg
    #QgsField("rneut", QVariant.String),
    #QgsField("tap", QVariant.String),
    #QgsField("xfrmcode", QVariant.String),
    #QgsField("xht", QVariant.String),
    #QgsField("xlt", QVariant.String),
    #QgsField("xneut", QVariant.String)
    #******>Parametros***************
])
transformer_layer.updateFields()


# Guardar la capa de puntos de transformadores como Shapefile en la ruta del proyecto
transformer_layer_path = project_path + '/transformadores.shp'
QgsVectorFileWriter.writeAsVectorFormat(transformer_layer, transformer_layer_path, 'utf-8', transformer_layer.crs(), 'ESRI Shapefile')

# Crear capa de Estación Transformadora
et_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "estacion_transformadora", "memory")
et_layer_provider = et_layer.dataProvider()
et_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("start_node", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("pu", QVariant.String),
    QgsField("basekv", QVariant.String),
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("r1", QVariant.String),
    QgsField("r0", QVariant.String),
    QgsField("x1", QVariant.String),
    QgsField("x0", QVariant.String)
    #******<Parametros adicionales**************
    # QgsField("frequency", QVariant.String),
    # QgsField("angledeg", QVariant.String),
    #******>Parametros***************
])
et_layer.updateFields()


# Guardar la capa de nodos como Shapefile en la ruta del proyecto
et_layer_path = project_path + '/estacion_transformadora.shp'
QgsVectorFileWriter.writeAsVectorFormat(et_layer, et_layer_path, 'utf-8', et_layer.crs(), 'ESRI Shapefile')

# Crear capa de puntos para Setas
seta_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "setas", "memory")
seta_layer_provider = seta_layer.dataProvider()
seta_layer_provider.addAttributes([QgsField("id", QVariant.String), QgsField("wdg1_node", QVariant.String), QgsField("wdg2_node", QVariant.String)])
seta_layer.updateFields()

# Guardar la capa de puntos de Setas como Shapefile en la ruta del proyecto
seta_layer_path = project_path + '/setas.shp'
QgsVectorFileWriter.writeAsVectorFormat(seta_layer, seta_layer_path, 'utf-8', seta_layer.crs(), 'ESRI Shapefile')

# Crear nuevas instancias de capas utilizando QgsVectorLayer
node_mt_layer = QgsVectorLayer(node_mt_layer_path, "nodos_mt", "ogr")
node_bt_layer = QgsVectorLayer(node_bt_layer_path, "nodos_bt", "ogr")
line_mt_layer = QgsVectorLayer(line_mt_layer_path, "lineas_mt", "ogr")
line_bt_layer = QgsVectorLayer(line_bt_layer_path, "lineas_bt", "ogr")
generator_layer = QgsVectorLayer(generator_layer_path, "generadores", "ogr")
load_layer = QgsVectorLayer(load_layer_path, "cargas", "ogr")
switch_layer = QgsVectorLayer(switch_layer_path, "interruptores", "ogr")
transformer_layer = QgsVectorLayer(transformer_layer_path, "transformadores", "ogr")
et_layer = QgsVectorLayer(et_layer_path, "estacion_transformadora", "ogr")
seta_layer = QgsVectorLayer(seta_layer_path, "setas", "ogr")

# Crear y organizar grupos de capas
root = QgsProject.instance().layerTreeRoot()

# Crear grupo para capas de Media Tensión (MT)
group_mt = root.addGroup("Media Tensión")
group_mt.addLayer(QgsProject.instance().addMapLayer(seta_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(transformer_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(generator_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(load_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(et_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(node_mt_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(switch_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(line_mt_layer, False))

# Crear grupo para capas de Baja Tensión (BT)
group_bt = root.addGroup("Baja Tensión")
group_bt.addLayer(QgsProject.instance().addMapLayer(node_bt_layer, False))
group_bt.addLayer(QgsProject.instance().addMapLayer(line_bt_layer, False))

# Simbología para los generadores
svg_path = project_path + '/iconos/generador.svg'  # Definir la ruta del archivo SVG
svg_marker = QgsSvgMarkerSymbolLayer(svg_path)  # Crear una nueva instancia de QgsSvgMarkerSymbolLayer
svg_marker.setSize(10)  # Establecer el tamaño del marcador SVG
svg_marker.setOffset(QPointF(2.3, -5.2))  # Establecer el desplazamiento del marcador SVG
symbol = QgsSymbol.defaultSymbol(generator_layer.geometryType())  # Crear un nuevo símbolo y añadir la capa de marcador SVG
symbol.changeSymbolLayer(0, svg_marker)
generator_layer.renderer().setSymbol(symbol)  # Establecer el símbolo para la capa de generadores
generator_layer.triggerRepaint()  # Actualizar la capa de generadores
generator_layer.setMinimumScale(10000)
generator_layer.setScaleBasedVisibility(True)

# Simbología para las líneas MT
line_mt_symbol = QgsSymbol.defaultSymbol(line_mt_layer.geometryType())  # Crear un nuevo símbolo de línea
line_mt_symbol_layer = QgsSimpleLineSymbolLayer()  # Crear una capa de símbolo de línea simple y configurar sus propiedades
line_mt_symbol_layer.setColor(QColor(255, 127, 0))
line_mt_symbol_layer.setWidth(0.7)  # La anchura se establece en milímetros
line_mt_symbol.changeSymbolLayer(0, line_mt_symbol_layer)  # Reemplazar la capa de símbolo por defecto con la nueva capa de símbolo de línea simple
line_mt_renderer = QgsCategorizedSymbolRenderer('', [QgsRendererCategory('', line_mt_symbol, '')])  # Crear un nuevo renderizador utilizando el símbolo de línea definido
line_mt_layer.setRenderer(line_mt_renderer)  # Establecer el renderizador en la capa de líneas
line_mt_layer.triggerRepaint()  # Actualizar la capa de líneas para aplicar el nuevo estilo

# Simbología para las líneas BT
line_bt_symbol = QgsSymbol.defaultSymbol(line_bt_layer.geometryType())  # Crear un nuevo símbolo de línea
line_bt_symbol_layer = QgsSimpleLineSymbolLayer()  # Crear una capa de símbolo de línea simple y configurar sus propiedades
line_bt_symbol_layer.setColor(QColor(167, 47, 211))
line_bt_symbol_layer.setWidth(0.26)  # La anchura se establece en milímetros
line_bt_symbol.changeSymbolLayer(0, line_bt_symbol_layer)  # Reemplazar la capa de símbolo por defecto con la nueva capa de símbolo de línea simple
line_bt_renderer = QgsCategorizedSymbolRenderer('', [QgsRendererCategory('', line_bt_symbol, '')])  # Crear un nuevo renderizador utilizando el símbolo de línea definido
line_bt_layer.setRenderer(line_bt_renderer)  # Establecer el renderizador en la capa de líneas
line_bt_layer.triggerRepaint()  # Actualizar la capa de líneas para aplicar el nuevo estilo
line_bt_layer.setMinimumScale(10000)
line_bt_layer.setScaleBasedVisibility(True)

# Simbología para las cargas
load_symbol = QgsMarkerSymbol()
while load_symbol.symbolLayerCount() > 0:
    load_symbol.deleteSymbolLayer(0)
triangle_load_layer = QgsSimpleMarkerSymbolLayer()
triangle_load_layer.setShape(QgsSimpleMarkerSymbolLayer.Triangle)
triangle_load_layer.setAngle(180)
triangle_load_layer.setColor(QColor('blue'))
triangle_load_layer.setOffset(QPointF(0, -3.45))
triangle_load_layer.setSize(2.4)
load_symbol.appendSymbolLayer(triangle_load_layer)
line_load_layer = QgsSimpleMarkerSymbolLayer()
line_load_layer.setShape(QgsSimpleMarkerSymbolLayer.Line)
line_load_layer.setColor(QColor('blue'))
line_load_layer.setOffset(QPointF(0, 1.5))
line_load_layer.setSize(1.5)
load_symbol.appendSymbolLayer(line_load_layer)
load_layer.setRenderer(QgsSingleSymbolRenderer(load_symbol))
load_layer.triggerRepaint()
load_layer.setMinimumScale(10000)
load_layer.setScaleBasedVisibility(True)

# # Simbología para los interruptores
# switch_symbol = QgsSymbol.defaultSymbol(switch_layer.geometryType())  # Crear un nuevo símbolo para la capa de geometría de puntos
# switch_symbol_layer = QgsSimpleMarkerSymbolLayer()  # Crear una capa de símbolo de marcador simple
# switch_symbol_layer.setColor(QColor('green'))  # Establecer el color del marcador a verde
# switch_symbol_layer.setSize(2)  # Establecer el tamaño del marcador a 2mm
# switch_symbol_layer.setShape(QgsSimpleMarkerSymbolLayer.Square)  # Establecer la forma del marcador como un cuadrado
# switch_symbol.changeSymbolLayer(0, switch_symbol_layer)  # Reemplazar la capa de símbolo por defecto con la nueva capa de símbolo de marcador simple
# switch_layer.setRenderer(QgsSingleSymbolRenderer(switch_symbol))  # Establecer el renderizador para la capa de interruptores
# switch_layer.triggerRepaint()  # Actualizar la capa de interruptores para aplicar el nuevo estilo
# switch_layer.setMinimumScale(10000)  # Establece la escala mínima a 1:5000
# switch_layer.setScaleBasedVisibility(True)  # Establecer la visibilidad dependiente de la escala para la capa de interruptores

# Simbología para los interruptores
switch_symbol_closed = QgsSymbol.defaultSymbol(switch_layer.geometryType())  # Crear un nuevo símbolo para la capa de geometría de puntos
switch_symbol_layer_closed = QgsSimpleMarkerSymbolLayer()  # Crear una capa de símbolo de marcador simple
switch_symbol_layer_closed.setColor(QColor('green'))  # Establecer el color del marcador a verde
switch_symbol_layer_closed.setSize(2)  # Establecer el tamaño del marcador a 2mm
switch_symbol_layer_closed.setShape(QgsSimpleMarkerSymbolLayer.Square)  # Establecer la forma del marcador como un cuadrado
switch_symbol_closed.changeSymbolLayer(0, switch_symbol_layer_closed)  # Reemplazar la capa de símbolo por defecto con la nueva capa de símbolo de marcador simple

switch_symbol_open = QgsSymbol.defaultSymbol(switch_layer.geometryType())  # Crear un nuevo símbolo para la capa de geometría de puntos
switch_symbol_layer_open = QgsSimpleMarkerSymbolLayer()  # Crear una capa de símbolo de marcador simple
switch_symbol_layer_open.setColor(QColor('red'))  # Establecer el color del marcador a rojo
switch_symbol_layer_open.setSize(2)  # Establecer el tamaño del marcador a 2mm
switch_symbol_layer_open.setShape(QgsSimpleMarkerSymbolLayer.Square)  # Establecer la forma del marcador como un cuadrado
switch_symbol_open.changeSymbolLayer(0, switch_symbol_layer_open)  # Reemplazar la capa de símbolo por defecto con la nueva capa de símbolo de marcador simple

categories = [
    QgsRendererCategory('closed', switch_symbol_closed, 'Closed'),
    QgsRendererCategory('open', switch_symbol_open, 'Open')
]

switch_renderer = QgsCategorizedSymbolRenderer('State', categories)  # Crear un renderizador categorizado basado en el atributo "State"
switch_layer.setRenderer(switch_renderer)  # Establecer el renderizador para la capa de interruptores
switch_layer.triggerRepaint()  # Actualizar la capa de interruptores para aplicar el nuevo estilo
switch_layer.setMinimumScale(10000)  # Establece la escala mínima a 1:5000
switch_layer.setScaleBasedVisibility(True)  # Establecer la visibilidad dependiente de la escala para la capa de interruptores


# Simbología para los nodos MT
node_mt_symbol = QgsSymbol.defaultSymbol(node_mt_layer.geometryType())
node_mt_symbol_layer = QgsSimpleMarkerSymbolLayer()
node_mt_symbol_layer.setColor(QColor('orange'))
node_mt_symbol_layer.setSize(1.5)  # El tamaño se establece en milímetros
node_mt_symbol_layer.setShape(QgsSimpleMarkerSymbolLayer.Circle)  # Establecer la forma del marcador como un círculo
node_mt_symbol.changeSymbolLayer(0, node_mt_symbol_layer)
node_mt_renderer = QgsSingleSymbolRenderer(node_mt_symbol)
node_mt_layer.setRenderer(node_mt_renderer)
node_mt_layer.triggerRepaint()
node_mt_layer.setMinimumScale(10000)
node_mt_layer.setScaleBasedVisibility(True)

# Simbología para los nodos BT
node_bt_symbol = QgsSymbol.defaultSymbol(node_bt_layer.geometryType())
node_bt_symbol_layer = QgsSimpleMarkerSymbolLayer()
node_bt_symbol_layer.setColor(QColor(167, 47, 211))
node_bt_symbol_layer.setSize(1.0)  # El tamaño se establece en milímetros
node_bt_symbol_layer.setShape(QgsSimpleMarkerSymbolLayer.Circle)  # Establecer la forma del marcador como un círculo
node_bt_symbol.changeSymbolLayer(0, node_bt_symbol_layer)
node_bt_renderer = QgsSingleSymbolRenderer(node_bt_symbol)
node_bt_layer.setRenderer(node_bt_renderer)
node_bt_layer.triggerRepaint()
node_bt_layer.setMinimumScale(5000)
node_bt_layer.setScaleBasedVisibility(True)

# Simbología para la estación transformadora
et_symbol = QgsSymbol.defaultSymbol(et_layer.geometryType())  # Crear un nuevo símbolo para la capa de geometría de puntos
et_symbol_layer = QgsSimpleMarkerSymbolLayer()  # Crear una capa de símbolo de marcador simple
et_symbol_layer.setColor(QColor(211, 158, 93))
et_symbol_layer.setSize(3.0)  # Establecer el tamaño del marcador a 3mm
et_symbol_layer.setShape(QgsSimpleMarkerSymbolLayer.Square)  # Establecer la forma del marcador como un cuadrado
et_symbol.changeSymbolLayer(0, et_symbol_layer)  # Reemplazar la capa de símbolo por defecto con la nueva capa de símbolo de marcador simple
et_layer.setRenderer(QgsSingleSymbolRenderer(et_symbol))  # Establecer el renderizador para la capa de estación transformadora
et_layer.triggerRepaint()  # Actualizar la capa de estación transformadora para aplicar el nuevo estilo

# Simbología para los setas
seta_symbol = QgsSymbol.defaultSymbol(seta_layer.geometryType())
seta_symbol_layer = QgsSimpleMarkerSymbolLayer()
seta_symbol_layer.setShape(QgsSimpleMarkerSymbolLayer.Triangle)
seta_symbol_layer.setColor(QColor('black'))
seta_symbol_layer.setSize(3.0)  # El tamaño se establece en milímetros
seta_symbol.changeSymbolLayer(0, seta_symbol_layer)
seta_renderer = QgsSingleSymbolRenderer(seta_symbol)
seta_layer.setRenderer(seta_renderer)
seta_layer.triggerRepaint()
seta_layer.setMinimumScale(10000)
seta_layer.setScaleBasedVisibility(True)

# Simbología para los transformadores
transformer_symbol = QgsMarkerSymbol()
while transformer_symbol.symbolLayerCount() > 0:
    transformer_symbol.deleteSymbolLayer(0)
circle1_layer = QgsSimpleMarkerSymbolLayer()
circle1_layer.setShape(QgsSimpleMarkerSymbolLayer.Circle)
circle1_layer.setFillColor(QColor('white'))  # Color de relleno
circle1_layer.setStrokeColor(QColor('red'))  # Color del borde rojo
circle1_layer.setStrokeWidth(0.4)  # Ancho del borde
circle1_layer.setSize(3.0)  # Diámetro en milímetros
circle1_layer.setOffset(QPointF(0, -0.7))  # Desplazamiento vertical hacia arriba
circle2_layer = QgsSimpleMarkerSymbolLayer()
circle2_layer.setShape(QgsSimpleMarkerSymbolLayer.Circle)
circle2_layer.setFillColor(QColor(0, 0, 0, 0))  # Color de relleno transparente
circle2_layer.setStrokeColor(QColor('red'))  # Color del borde rojo
circle2_layer.setStrokeWidth(0.4)  # Ancho del borde
circle2_layer.setSize(3.0)  # Diámetro en milímetros
circle2_layer.setOffset(QPointF(0, 0.7))  # Desplazamiento vertical hacia abajo
transformer_symbol.appendSymbolLayer(circle1_layer)
transformer_symbol.appendSymbolLayer(circle2_layer)
transformer_layer.setRenderer(QgsSingleSymbolRenderer(transformer_symbol))
transformer_layer.triggerRepaint()
transformer_layer.setMinimumScale(10000)
transformer_layer.setScaleBasedVisibility(True)
