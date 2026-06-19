# Importar módulos necesarios
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsSvgMarkerSymbolLayer, QgsSymbol, QgsSimpleLineSymbolLayer, QgsSymbolLayerRegistry, QgsRendererCategory, QgsCategorizedSymbolRenderer, QgsSimpleMarkerSymbolLayer, QgsSymbol, QgsSingleSymbolRenderer
from PyQt5.QtCore import QVariant, QPointF
from PyQt5.QtGui import QColor

# Obtener la ruta del proyecto
project_path = QgsProject.instance().homePath()

# Crear capa de nodos
node_layer = QgsVectorLayer("Point?crs=EPSG:4326", "nodos", "memory")
node_layer_provider = node_layer.dataProvider()
node_layer_provider.addAttributes([QgsField("id", QVariant.String)])
node_layer.updateFields()

# Guardar la capa de nodos como Shapefile en la ruta del proyecto
node_layer_path = project_path + '/nodos.shp'
QgsVectorFileWriter.writeAsVectorFormat(node_layer, node_layer_path, 'utf-8', node_layer.crs(), 'ESRI Shapefile')

# Crear capa de líneas
line_layer = QgsVectorLayer("LineString?crs=EPSG:4326", "lineas", "memory")
line_layer_provider = line_layer.dataProvider()
line_layer_provider.addAttributes([QgsField("id", QVariant.String), QgsField("start_node", QVariant.String), QgsField("end_node", QVariant.String)])
line_layer.updateFields()

# Guardar la capa de líneas como Shapefile en la ruta del proyecto
line_layer_path = project_path + '/lineas.shp'
QgsVectorFileWriter.writeAsVectorFormat(line_layer, line_layer_path, 'utf-8', line_layer.crs(), 'ESRI Shapefile')

# Crear capa de puntos para generadores
generator_layer = QgsVectorLayer("Point?crs=EPSG:4326", "generadores", "memory")
generator_layer_provider = generator_layer.dataProvider()
generator_layer_provider.addAttributes([QgsField("id", QVariant.String), QgsField("start_node", QVariant.String)])
generator_layer.updateFields()

# Guardar la capa de puntos de generadores como Shapefile en la ruta del proyecto
generator_layer_path = project_path + '/generadores.shp'
QgsVectorFileWriter.writeAsVectorFormat(generator_layer, generator_layer_path, 'utf-8', generator_layer.crs(), 'ESRI Shapefile')

# Crear nuevas instancias de capas utilizando QgsVectorLayer
node_layer = QgsVectorLayer(node_layer_path, "nodos", "ogr")
line_layer = QgsVectorLayer(line_layer_path, "lineas", "ogr")
generator_layer = QgsVectorLayer(generator_layer_path, "generadores", "ogr")

# Agregar capas al proyecto
QgsProject.instance().addMapLayer(line_layer)
QgsProject.instance().addMapLayer(generator_layer)
QgsProject.instance().addMapLayer(node_layer)

# Simbología para los generadores
svg_path = project_path + '/iconos/generador.svg'  # Definir la ruta del archivo SVG
svg_marker = QgsSvgMarkerSymbolLayer(svg_path) # Crear una nueva instancia de QgsSvgMarkerSymbolLayer
svg_marker.setSize(10)  # Establecer el tamaño del marcador SVG
svg_marker.setOffset(QPointF(2.5, -5))  # Establecer el desplazamiento del marcador SVG
symbol = QgsSymbol.defaultSymbol(generator_layer.geometryType())    # Crear un nuevo símbolo y añadir la capa de marcador SVG
symbol.changeSymbolLayer(0, svg_marker)
generator_layer.renderer().setSymbol(symbol)    # Establecer el símbolo para la capa de generadores
generator_layer.triggerRepaint()    # Actualizar la capa de generadores

# Simbología para las líneas
line_symbol = QgsSymbol.defaultSymbol(line_layer.geometryType())    # Crear un nuevo símbolo de línea
line_symbol_layer = QgsSimpleLineSymbolLayer()  # Crear una capa de símbolo de línea simple y configurar sus propiedades
line_symbol_layer.setColor(QColor('orange'))
line_symbol_layer.setWidth(1)  # La anchura se establece en milímetros
line_symbol.changeSymbolLayer(0, line_symbol_layer) # Reemplazar la capa de símbolo por defecto con la nueva capa de símbolo de línea simple
line_renderer = QgsCategorizedSymbolRenderer('', [QgsRendererCategory('', line_symbol, '')])    # Crear un nuevo renderizador utilizando el símbolo de línea definido
line_layer.setRenderer(line_renderer)   # Establecer el renderizador en la capa de líneas
line_layer.triggerRepaint() # Actualizar la capa de líneas para aplicar el nuevo estilo

# Simbología para los nodos

# Crear un nuevo símbolo de marcador
node_symbol = QgsSymbol.defaultSymbol(node_layer.geometryType())

# Crear una capa de símbolo de marcador simple y configurar sus propiedades
node_symbol_layer = QgsSimpleMarkerSymbolLayer()
node_symbol_layer.setColor(QColor('orange'))
node_symbol_layer.setSize(2)  # El tamaño se establece en milímetros
node_symbol_layer.setShape(QgsSimpleMarkerSymbolLayer.Circle)  # Establecer la forma del marcador como un círculo

# Reemplazar la capa de símbolo por defecto con la nueva capa de símbolo de marcador simple
node_symbol.changeSymbolLayer(0, node_symbol_layer)

# Crear un renderizador para el símbolo
node_renderer = QgsSingleSymbolRenderer(node_symbol)

# Establecer el renderizador para la capa de nodos
node_layer.setRenderer(node_renderer)

# Actualizar la capa de nodos para aplicar el nuevo estilo
node_layer.triggerRepaint()

# cambios desde cursor
# cambios desde vscode