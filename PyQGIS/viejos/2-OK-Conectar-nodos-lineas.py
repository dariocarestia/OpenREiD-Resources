# Importar módulos necesarios
from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsExpression

# Obtener las capas existentes por nombre
point_layer = QgsProject.instance().mapLayersByName('nodos')[0]
line_layer = QgsProject.instance().mapLayersByName('lineas')[0]

# Obtener los índices de campo
start_node_field_index = line_layer.fields().lookupField('start_node')
end_node_field_index = line_layer.fields().lookupField('end_node')

# Crear un diccionario para mapear las coordenadas de los nodos a sus IDs
node_coordinates = {}
for feature in point_layer.getFeatures():
    node_id = feature['id']
    node_coordinates[node_id] = feature.geometry().asPoint()

# Actualizar los atributos de las líneas con los IDs de inicio y fin
with edit(line_layer):
    for feature in line_layer.getFeatures():
        start_point = feature.geometry().asPolyline()[0]
        end_point = feature.geometry().asPolyline()[-1]

        # Buscar el ID del nodo más cercano al punto de inicio
        start_node_id = min(node_coordinates, key=lambda k: start_point.sqrDist(QgsPointXY(node_coordinates[k])))

        # Buscar el ID del nodo más cercano al punto final
        end_node_id = min(node_coordinates, key=lambda k: end_point.sqrDist(QgsPointXY(node_coordinates[k])))

        # Actualizar los valores de los campos start_node y end_node
        feature.setAttribute(start_node_field_index, start_node_id)
        feature.setAttribute(end_node_field_index, end_node_id)

        # Guardar los cambios en la capa
        line_layer.updateFeature(feature)

# Actualizar la capa en la interfaz de QGIS (opcional)
line_layer.triggerRepaint()

# Informar que se han realizado los cambios
print("Se han asignado los valores de start_node y end_node a las líneas.")
