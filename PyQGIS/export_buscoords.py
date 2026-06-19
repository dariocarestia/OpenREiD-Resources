#Procedimiento previo para traer red generada por el plugin de zarsavilla-robles
# 1) Usar el plugin (los 3 pasos) para generar los dss
# 2) Usar la funcion para exportar las coordenadas de nodos coordenadas_faltantes.txt (C:\programas-python\Repo5\Tutorial-1\Script-Prueba-Openreid.py)
# 3) Agregar esas coordenadas (x_123..) al archivo de coordenadas original Bus.txt
# 4) Volver a corerr el Script-Prueba-Openreid.py para contabilizar si hay nodos sin coordenadas


# 5) Me encontre que el plugin cuando seleccionas un solo alimentador, igualmente exporta todas las cargas.
# 6) Para eliminar las cargas segui el siguiente procedimiento:
#   a) Exporte en csv las cargas validas de la capa de qgis
#   b) Importe con separador de espacios en Calc el archivo de demanda (cargas) dss, lo ordené y marque a mano los validos, luego los borre y guarde el archivo modificado.
#   c) continué con el paso 2


# El procedimiento para exportar los nodos que estan en POSGAR 94 a WGS 84 es el siguiente:
# 1) Primero crear las capas con el script pero en el SRC POSGAR 94 (EPSG:22182)
# 2) Luego importar Dss (En el master chequear que el archivo de coordenadas esté invocado con BusCoords y no LatLongCoords)
# 3) Una vez que tengo la capa nodos_mt en POSGAR 94, usar este script para exportar en csv con SRC WGS84 (EPSG:4326) (ojo aqui tuve que cerrar y volver a abrir qgis porque no reconocía bien el src)
# 4) Una vez teniendo nodos_wgs84.csv -> Ordenarlo-> (nodos_wgs84_ordenado.csv), modificar el master para que tome este archivo
# 5) Volver a crear las capas pero esta vez en WGS84 y volver a importar Dss

import csv
from qgis.core import QgsCoordinateTransform, QgsProject, QgsCoordinateReferenceSystem

# Obtener la capa de nodos
node_layer = QgsProject.instance().mapLayersByName("nodos_mt")[0]

# Definir la transformación de coordenadas a WGS84
crs_src = node_layer.crs()
crs_dest = QgsCoordinateReferenceSystem('EPSG:4326')
transform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())

# Ruta del archivo CSV de salida
output_file = "nodos_wgs84.csv"

# Abrir el archivo CSV en modo escritura
with open(output_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["id", "latitud", "longitud"])

    # Iterar sobre los nodos y escribir sus coordenadas transformadas en el archivo CSV
    for feature in node_layer.getFeatures():
        node_id = feature["id"]
        x = feature.geometry().asPoint().x()
        y = feature.geometry().asPoint().y()

        # Transformar las coordenadas a WGS84
        wgs_coords = transform.transform(x, y)

        # Escribir la fila en el archivo CSV
        writer.writerow([node_id, wgs_coords.y(), wgs_coords.x()])

print(f"Coordenadas de los nodos exportadas a '{output_file}' en formato WGS84.")