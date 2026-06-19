# Importar módulos necesarios
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsVectorFileWriter
from PyQt5.QtCore import QVariant

# Obtener la ruta del proyecto
project_path = QgsProject.instance().homePath()

# Crear capa de puntos
point_layer = QgsVectorLayer("Point?crs=EPSG:4326", "nodos", "memory")
point_layer_provider = point_layer.dataProvider()
#point_layer_provider.addAttributes([QgsField("id", QVariant.Int)])
point_layer_provider.addAttributes([QgsField("id", QVariant.String)])
point_layer.updateFields()

# Guardar la capa de puntos como Shapefile en la ruta del proyecto
point_layer_path = project_path + '/nodos.shp'
QgsVectorFileWriter.writeAsVectorFormat(point_layer, point_layer_path, 'utf-8', point_layer.crs(), 'ESRI Shapefile')

# Crear capa de líneas
line_layer = QgsVectorLayer("LineString?crs=EPSG:4326", "lineas", "memory")
line_layer_provider = line_layer.dataProvider()
#line_layer_provider.addAttributes([QgsField("id", QVariant.Int), QgsField("start_node", QVariant.Int), QgsField("end_node", QVariant.Int)])
line_layer_provider.addAttributes([QgsField("id", QVariant.String), QgsField("start_node", QVariant.String), QgsField("end_node", QVariant.String)])
line_layer.updateFields()

# Guardar la capa de líneas como Shapefile en la ruta del proyecto
line_layer_path = project_path + '/lineas.shp'
QgsVectorFileWriter.writeAsVectorFormat(line_layer, line_layer_path, 'utf-8', line_layer.crs(), 'ESRI Shapefile')

# Crear nuevas instancias de capas utilizando QgsVectorLayer
point_layer = QgsVectorLayer(point_layer_path, "nodos", "ogr")
line_layer = QgsVectorLayer(line_layer_path, "lineas", "ogr")

# Agregar capas al proyecto
QgsProject.instance().addMapLayer(point_layer)
QgsProject.instance().addMapLayer(line_layer)