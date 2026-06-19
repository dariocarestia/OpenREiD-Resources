# Importar módulos necesarios
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry

# Crear capa de puntos
point_layer = QgsVectorLayer("Point", "nodos", "memory")
point_layer_provider = point_layer.dataProvider()
point_layer_provider.addAttributes([QgsField("id", QVariant.Int)])
point_layer.updateFields()

# Crear capa de líneas
line_layer = QgsVectorLayer("LineString", "lineas", "memory")
line_layer_provider = line_layer.dataProvider()
line_layer_provider.addAttributes([QgsField("id", QVariant.Int), QgsField("start_node", QVariant.Int), QgsField("end_node", QVariant.Int)])
line_layer.updateFields()

# Agregar capas al proyecto
QgsProject.instance().addMapLayers([point_layer, line_layer])
