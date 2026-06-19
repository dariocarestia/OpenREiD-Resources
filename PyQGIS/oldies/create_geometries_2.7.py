# Importar módulos necesarios
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsSvgMarkerSymbolLayer, QgsSymbol, QgsSimpleLineSymbolLayer,\
      QgsRendererCategory, QgsCategorizedSymbolRenderer, QgsSimpleMarkerSymbolLayer, QgsSymbol, QgsSingleSymbolRenderer, QgsMarkerSymbol,\
          QgsMarkerLineSymbolLayer, QgsLineSymbolLayer, QgsGeometryGeneratorSymbolLayer
from PyQt5.QtCore import QVariant, QPointF, Qt
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

# Crear capa de puntos para cargas
load_layer = QgsVectorLayer("Point?crs=EPSG:4326", "cargas", "memory")
load_layer_provider = load_layer.dataProvider()
load_layer_provider.addAttributes([QgsField("id", QVariant.String), QgsField("start_node", QVariant.String)])
load_layer.updateFields()

# Guardar la capa de puntos de cargas como Shapefile en la ruta del proyecto
load_layer_path = project_path + '/cargas.shp'
QgsVectorFileWriter.writeAsVectorFormat(load_layer, load_layer_path, 'utf-8', load_layer.crs(), 'ESRI Shapefile')

# Crear capa de puntos para interruptores
switch_layer = QgsVectorLayer("Point?crs=EPSG:4326", "interruptores", "memory")
switch_layer_provider = switch_layer.dataProvider()
switch_layer_provider.addAttributes([QgsField("id", QVariant.String), QgsField("line", QVariant.String), QgsField("terminal", QVariant.String)])
switch_layer.updateFields()

# Guardar la capa de puntos de cargas como Shapefile en la ruta del proyecto
switch_layer_path = project_path + '/interruptores.shp'
QgsVectorFileWriter.writeAsVectorFormat(switch_layer, switch_layer_path, 'utf-8', switch_layer.crs(), 'ESRI Shapefile')
# ***

# Crear capa de puntos para transformadores
transformer_layer = QgsVectorLayer("Point?crs=EPSG:4326", "transformadores", "memory")
transformer_layer_provider = transformer_layer.dataProvider()
transformer_layer_provider.addAttributes([QgsField("id", QVariant.String), QgsField("wdg1_node", QVariant.String), QgsField("wdg2_node", QVariant.String)])
transformer_layer.updateFields()

# Guardar la capa de puntos de transformadores como Shapefile en la ruta del proyecto
transformer_layer_path = project_path + '/transformadores.shp'
QgsVectorFileWriter.writeAsVectorFormat(transformer_layer, transformer_layer_path, 'utf-8', transformer_layer.crs(), 'ESRI Shapefile')


# Crear capa de Estación Transformadora
et_layer = QgsVectorLayer("Point?crs=EPSG:4326", "estacion_transformadora", "memory")
et_layer_provider = et_layer.dataProvider()
et_layer_provider.addAttributes([QgsField("id", QVariant.String), QgsField("start_node", QVariant.String)])
et_layer.updateFields()

# Guardar la capa de nodos como Shapefile en la ruta del proyecto
et_layer_path = project_path + '/estacion_transformadora.shp'
QgsVectorFileWriter.writeAsVectorFormat(et_layer, et_layer_path, 'utf-8', et_layer.crs(), 'ESRI Shapefile')



# Crear capa de puntos para Setas
seta_layer = QgsVectorLayer("Point?crs=EPSG:4326", "setas", "memory")
seta_layer_provider = seta_layer.dataProvider()
seta_layer_provider.addAttributes([QgsField("id", QVariant.String), QgsField("wdg1_node", QVariant.String), QgsField("wdg2_node", QVariant.String)])
seta_layer.updateFields()

# Guardar la capa de puntos de Setas como Shapefile en la ruta del proyecto
seta_layer_path = project_path + '/setas.shp'
QgsVectorFileWriter.writeAsVectorFormat(seta_layer, seta_layer_path, 'utf-8', seta_layer.crs(), 'ESRI Shapefile')




# Crear nuevas instancias de capas utilizando QgsVectorLayer
node_layer = QgsVectorLayer(node_layer_path, "nodos", "ogr")
line_layer = QgsVectorLayer(line_layer_path, "lineas", "ogr")
generator_layer = QgsVectorLayer(generator_layer_path, "generadores", "ogr")
load_layer = QgsVectorLayer(load_layer_path, "cargas", "ogr")
switch_layer = QgsVectorLayer(switch_layer_path, "interruptores", "ogr")
transformer_layer = QgsVectorLayer(transformer_layer_path, "transformadores", "ogr")
et_layer = QgsVectorLayer(et_layer_path, "estacion_transformadora", "ogr")
seta_layer = QgsVectorLayer(seta_layer_path, "setas", "ogr")


# Agregar capas al proyecto
QgsProject.instance().addMapLayer(line_layer)
QgsProject.instance().addMapLayer(switch_layer)
QgsProject.instance().addMapLayer(generator_layer)
QgsProject.instance().addMapLayer(node_layer)
QgsProject.instance().addMapLayer(transformer_layer)
QgsProject.instance().addMapLayer(load_layer)
QgsProject.instance().addMapLayer(et_layer)
QgsProject.instance().addMapLayer(seta_layer)


# Simbología para los generadores
svg_path = project_path + '/iconos/generador.svg'  # Definir la ruta del archivo SVG
svg_marker = QgsSvgMarkerSymbolLayer(svg_path) # Crear una nueva instancia de QgsSvgMarkerSymbolLayer
svg_marker.setSize(10)  # Establecer el tamaño del marcador SVG
svg_marker.setOffset(QPointF(2.3, -5.2))  # Establecer el desplazamiento del marcador SVG
symbol = QgsSymbol.defaultSymbol(generator_layer.geometryType())    # Crear un nuevo símbolo y añadir la capa de marcador SVG
symbol.changeSymbolLayer(0, svg_marker)
generator_layer.renderer().setSymbol(symbol)    # Establecer el símbolo para la capa de generadores
generator_layer.triggerRepaint()    # Actualizar la capa de generadores


# Simbología para las líneas
line_symbol = QgsSymbol.defaultSymbol(line_layer.geometryType())    # Crear un nuevo símbolo de línea
line_symbol_layer = QgsSimpleLineSymbolLayer()  # Crear una capa de símbolo de línea simple y configurar sus propiedades
#line_symbol_layer.setColor(QColor('orange'))
line_symbol_layer.setColor(QColor(255,127,0))
line_symbol_layer.setWidth(0.7)  # La anchura se establece en milímetros
line_symbol.changeSymbolLayer(0, line_symbol_layer) # Reemplazar la capa de símbolo por defecto con la nueva capa de símbolo de línea simple
line_renderer = QgsCategorizedSymbolRenderer('', [QgsRendererCategory('', line_symbol, '')])    # Crear un nuevo renderizador utilizando el símbolo de línea definido
line_layer.setRenderer(line_renderer)   # Establecer el renderizador en la capa de líneas
line_layer.triggerRepaint() # Actualizar la capa de líneas para aplicar el nuevo estilo


# Crear un nuevo símbolo de marcador para las cargas
load_symbol = QgsMarkerSymbol()
# Remover cualquier capa de símbolo predeterminada
while load_symbol.symbolLayerCount() > 0:
    load_symbol.deleteSymbolLayer(0)
# Configurar el triángulo
triangle_load_layer = QgsSimpleMarkerSymbolLayer()
triangle_load_layer.setShape(QgsSimpleMarkerSymbolLayer.Triangle)
triangle_load_layer.setAngle(180)
triangle_load_layer.setColor(QColor('blue'))
triangle_load_layer.setOffset(QPointF(0, -3.45))
triangle_load_layer.setSize(2.4)
# Agregar el triángulo al símbolo
load_symbol.appendSymbolLayer(triangle_load_layer)
# Configurar la "línea" que es en realidad otro marcador simple
line_load_layer = QgsSimpleMarkerSymbolLayer()
line_load_layer.setShape(QgsSimpleMarkerSymbolLayer.Line)
line_load_layer.setColor(QColor('blue'))
line_load_layer.setOffset(QPointF(0, 1.5))
line_load_layer.setSize(1.5)
# Agregar la "línea" al símbolo
load_symbol.appendSymbolLayer(line_load_layer)
# Establecer el renderizador en la capa de transformadores
load_layer.setRenderer(QgsSingleSymbolRenderer(load_symbol))
# Actualizar la visualización de la capa
load_layer.triggerRepaint()


# Simbología para los interruptores
switch_symbol = QgsSymbol.defaultSymbol(switch_layer.geometryType())  # Crear un nuevo símbolo para la capa de geometría de puntos
switch_symbol_layer = QgsSimpleMarkerSymbolLayer()  # Crear una capa de símbolo de marcador simple
switch_symbol_layer.setColor(QColor('green'))  # Establecer el color del marcador a verde
switch_symbol_layer.setSize(2)  # Establecer el tamaño del marcador a 2mm
switch_symbol_layer.setShape(QgsSimpleMarkerSymbolLayer.Square)  # Establecer la forma del marcador como un cuadrado
switch_symbol.changeSymbolLayer(0, switch_symbol_layer)  # Reemplazar la capa de símbolo por defecto con la nueva capa de símbolo de marcador simple
switch_layer.setRenderer(QgsSingleSymbolRenderer(switch_symbol))  # Establecer el renderizador para la capa de interruptores
switch_layer.triggerRepaint()  # Actualizar la capa de interruptores para aplicar el nuevo estilo
switch_layer.setMinimumScale(5000) # Establece la escala mínima a 1:500
switch_layer.setScaleBasedVisibility(True)  # Establecer la visibilidad dependiente de la escala para la capa de interruptores

# Simbología para los nodos
node_symbol = QgsSymbol.defaultSymbol(node_layer.geometryType())
node_symbol_layer = QgsSimpleMarkerSymbolLayer()
node_symbol_layer.setColor(QColor('orange'))
node_symbol_layer.setSize(1.5)  # El tamaño se establece en milímetros
node_symbol_layer.setShape(QgsSimpleMarkerSymbolLayer.Circle)  # Establecer la forma del marcador como un círculo
# Reemplazar la capa de símbolo por defecto con la nueva capa de símbolo de marcador simple
node_symbol.changeSymbolLayer(0, node_symbol_layer)
# Crear un renderizador para el símbolo
node_renderer = QgsSingleSymbolRenderer(node_symbol)
# Establecer el renderizador para la capa de nodos
node_layer.setRenderer(node_renderer)
# Actualizar la capa de nodos para aplicar el nuevo estilo
node_layer.triggerRepaint()


# Simbología para la estación transformadora
et_symbol = QgsSymbol.defaultSymbol(et_layer.geometryType())  # Crear un nuevo símbolo para la capa de geometría de puntos
et_symbol_layer = QgsSimpleMarkerSymbolLayer()  # Crear una capa de símbolo de marcador simple
#et_symbol_layer.setColor(QColor('blue'))  # Establecer el color del marcador a verde
et_symbol_layer.setColor(QColor(211,158,93))
et_symbol_layer.setSize(3.0)  # Establecer el tamaño del marcador a 2mm
et_symbol_layer.setShape(QgsSimpleMarkerSymbolLayer.Square)  # Establecer la forma del marcador como un cuadrado
et_symbol.changeSymbolLayer(0, et_symbol_layer)  # Reemplazar la capa de símbolo por defecto con la nueva capa de símbolo de marcador simple
et_layer.setRenderer(QgsSingleSymbolRenderer(et_symbol))  # Establecer el renderizador para la capa de interruptores
et_layer.triggerRepaint()  # Actualizar la capa de interruptores para aplicar el nuevo estilo
#et_layer.setMinimumScale(1500) # Establece la escala mínima a 1:500
#et_layer.setScaleBasedVisibility(True)  # Establecer la visibilidad dependiente de la escala para la capa de interruptores


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


# Crear un nuevo símbolo de marcador para los transformadores
transformer_symbol = QgsMarkerSymbol()
while transformer_symbol.symbolLayerCount() > 0:
    transformer_symbol.deleteSymbolLayer(0)
circle1_layer = QgsSimpleMarkerSymbolLayer()
circle1_layer.setShape(QgsSimpleMarkerSymbolLayer.Circle)
#circle1_layer.setFillColor(QColor(0, 0, 0, 0))  # Color de relleno transparente
circle1_layer.setFillColor(QColor('white'))  # Color de relleno
circle1_layer.setStrokeColor(QColor('red'))  # Color del borde rojo
circle1_layer.setStrokeWidth(0.4)  # Ancho del borde
circle1_layer.setSize(3.0)  # Diámetro en milímetros
circle1_layer.setOffset(QPointF(0, -0.7))  # Desplazamiento vertical hacia arriba
circle2_layer = QgsSimpleMarkerSymbolLayer()
circle2_layer.setShape(QgsSimpleMarkerSymbolLayer.Circle)
circle2_layer.setFillColor(QColor(0, 0, 0, 0))  # Color de relleno transparente
#circle2_layer.setFillColor(QColor('white'))  # Color de relleno
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


