# Importar módulos necesarios
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsSvgMarkerSymbolLayer, QgsSymbol, QgsSimpleLineSymbolLayer,\
      QgsRendererCategory, QgsCategorizedSymbolRenderer, QgsSimpleMarkerSymbolLayer, QgsSingleSymbolRenderer, QgsMarkerSymbol,\
          QgsCoordinateReferenceSystem, QgsPalLayerSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling, QgsRuleBasedRenderer
from PyQt5.QtCore import QVariant, QPointF, Qt
from PyQt5.QtGui import QColor, QFont
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
node_mt_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    #******<Parametros de resultados***************
    QgsField("pu1", QVariant.String)
])
node_mt_layer.updateFields()

# Guardar la capa de nodos MT como Shapefile en la ruta del proyecto
node_mt_layer_path = project_path + '/nodos_mt.shp'
QgsVectorFileWriter.writeAsVectorFormat(node_mt_layer, node_mt_layer_path, 'utf-8', node_mt_layer.crs(), 'ESRI Shapefile')
#QgsVectorFileWriter.writeAsVectorFormat(node_mt_layer, node_mt_layer_path, 'utf-8', crs, 'ESRI Shapefile')

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
    QgsField("enabled", QVariant.String),
    #******<Parametros adicionales**************
    QgsField("linecode", QVariant.String),
    QgsField("geometry", QVariant.String),
    #QgsField("Rmatrix", QVariant.String),
    #QgsField("Xmatrix", QVariant.String),
    #QgsField("Cmatrix", QVariant.String),
    #******<Parametros de resultados***************
    QgsField("P.Activa", QVariant.String)
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
generator_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("start_node", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("Phases", QVariant.String),
    QgsField("kV", QVariant.String),
    QgsField("kW", QVariant.String),
    QgsField("PF", QVariant.String),
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("daily", QVariant.String),
    #******<Parametros adicionales**************
    # ...... Son un montón
    # ......
    #******<Parametros de resultados***************
    QgsField("pu1", QVariant.String)
])
generator_layer.updateFields()

# Guardar la capa de puntos de generadores como Shapefile en la ruta del proyecto
generator_layer_path = project_path + '/generadores.shp'
QgsVectorFileWriter.writeAsVectorFormat(generator_layer, generator_layer_path, 'utf-8', generator_layer.crs(), 'ESRI Shapefile')

# Crear capa de puntos para sistemas fotovoltaicos
pv_system_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "sistemas_fotovoltaicos", "memory")
pv_system_layer_provider = pv_system_layer.dataProvider()
pv_system_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("start_node", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("Irradiance", QVariant.String),
    QgsField("Pmpp", QVariant.String),
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("phases", QVariant.String),
    QgsField("kv", QVariant.String),
    QgsField("Temperatur", QVariant.String),    # Ojo que el atributo en Opendss es Temperature, pero qgis permite solo 10 caracteres
    QgsField("kVA", QVariant.String),
    QgsField("EffCurve", QVariant.String),
    QgsField("daily", QVariant.String),
    QgsField("Tdaily", QVariant.String)
    #******<Parametros adicionales**************
    # ...... Son un montón
    # ......
])
pv_system_layer.updateFields()

# Guardar la capa de puntos de sistemas fotovoltaicos como Shapefile en la ruta del proyecto
pv_system_layer_path = project_path + '/sistemas_fotovoltaicos.shp'
QgsVectorFileWriter.writeAsVectorFormat(pv_system_layer, pv_system_layer_path, 'utf-8', pv_system_layer.crs(), 'ESRI Shapefile')

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
    QgsField("conn", QVariant.String),
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
    #******<Parametros de resultados***************
    QgsField("P.Activa", QVariant.String),
    QgsField("P.Reactiva", QVariant.String)
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
seta_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("wdg1_node", QVariant.String),
    QgsField("wdg2_node", QVariant.String)
])
seta_layer.updateFields()

# Guardar la capa de puntos de Setas como Shapefile en la ruta del proyecto
seta_layer_path = project_path + '/setas.shp'
QgsVectorFileWriter.writeAsVectorFormat(seta_layer, seta_layer_path, 'utf-8', seta_layer.crs(), 'ESRI Shapefile')


# Crear capa de puntos para capacitores
capacitor_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "capacitores", "memory")
capacitor_layer_provider = capacitor_layer.dataProvider()
capacitor_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("start_node", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("kv", QVariant.String),
    QgsField("kvar", QVariant.String),
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("phases", QVariant.String),
    #******<Parametros adicionales**************
    #QgsField("conn", QVariant.String),
    #QgsField("cmatrix", QVariant.String),
    #QgsField("cuf", QVariant.String),
    #QgsField("R", QVariant.String),
    #QgsField("XL", QVariant.String),
    #QgsField("Harm", QVariant.String),
    #QgsField("Numsteps", QVariant.String),
    #QgsField("states", QVariant.String),
    #QgsField("normamps", QVariant.String),
    #QgsField("emergeamps", QVariant.String),
    #QgsField("faulrate", QVariant.String),
    #QgsField("pctperm", QVariant.String),
    #QgsField("repair", QVariant.String),
    #QgsField("basefreq", QVariant.String),
    #QgsField("enabled", QVariant.String),
    #QgsField("like", QVariant.String),
    #******>Parametros***************
])
capacitor_layer.updateFields()
# Guardar la capa de puntos de capacitores como Shapefile en la ruta del proyecto
capacitor_layer_path = project_path + '/capacitores.shp'
QgsVectorFileWriter.writeAsVectorFormat(capacitor_layer, capacitor_layer_path, 'utf-8', capacitor_layer.crs(), 'ESRI Shapefile')


# Crear capa para LineCode
#linecode_layer = QgsVectorLayer("None", "linecode", "memory")
linecode_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "linecode", "memory")
linecode_layer_provider = linecode_layer.dataProvider()
linecode_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("nphases", QVariant.String),
    QgsField("r1", QVariant.String),
    QgsField("r0", QVariant.String),
    QgsField("x1", QVariant.String),
    QgsField("x0", QVariant.String),
    QgsField("c1", QVariant.String),
    QgsField("c0", QVariant.String)
    #******<Parametros esenciales no presentes en interfaz*****
    #******<Parametros adicionales**************
    # QgsField("b0", QVariant.String),
    # QgsField("b1", QVariant.String),
    # QgsField("basefreq", QVariant.String),
    # QgsField("cmatrix", QVariant.String),
    # QgsField("emergamps", QVariant.String),
    # QgsField("faultrate", QVariant.String),
    # QgsField("kron", QVariant.String),
    # QgsField("like", QVariant.String),
    # QgsField("linetype", QVariant.String),
    # QgsField("neutral", QVariant.String),
    # QgsField("normamps", QVariant.String),
    # QgsField("pctperm", QVariant.String),
    # QgsField("phases", QVariant.String),
    # QgsField("ratings", QVariant.String),
    # QgsField("rmatrix", QVariant.String),
    # QgsField("seasons", QVariant.String),
    # QgsField("units", QVariant.String),
    # QgsField("xg", QVariant.String),
    # QgsField("xmatrix", QVariant.String)
    #******>Parametros***************
])
linecode_layer.updateFields()
linecode_layer_path = project_path + '/linecode.shp'
QgsVectorFileWriter.writeAsVectorFormat(linecode_layer, linecode_layer_path, 'utf-8', linecode_layer.crs(), 'ESRI Shapefile')


# Crear capa para LineGeometry
#linegeometry_layer = QgsVectorLayer("None", "linegeometry", "memory")
linegeometry_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "linegeometry", "memory")
linegeometry_layer_provider = linegeometry_layer.dataProvider()
linegeometry_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("nconds", QVariant.String),
    QgsField("nphases", QVariant.String),
    QgsField("spacing", QVariant.String),
    QgsField("wires", QVariant.String)
    #******<Parametros esenciales no presentes en interfaz*****
    #******<Parametros adicionales**************
    # QgsField("cncable", QVariant.String),
    # QgsField("cncables", QVariant.String),
    # QgsField("emergamps", QVariant.String),
    # QgsField("h", QVariant.String),
    # QgsField("like", QVariant.String),
    # QgsField("linetype", QVariant.String),
    # QgsField("normamps", QVariant.String),
    # QgsField("ratings", QVariant.String),
    # QgsField("reduce", QVariant.String),
    # QgsField("seasons", QVariant.String),
    # QgsField("tscable", QVariant.String),
    # QgsField("tscables", QVariant.String),
    # QgsField("units", QVariant.String),
    # QgsField("wire", QVariant.String),
    # QgsField("wires", QVariant.String),
    # QgsField("x", QVariant.String)
    #******>Parametros***************
])
linegeometry_layer.updateFields()
# Guardar la capa como shapefile en el directorio del proyecto
linegeometry_layer_path = project_path + '/linegeometry.shp'
QgsVectorFileWriter.writeAsVectorFormat(linegeometry_layer, linegeometry_layer_path, 'utf-8', linegeometry_layer.crs(), 'ESRI Shapefile')


# Crear capa para LineSpacing
#linespacing_layer = QgsVectorLayer("None", "linespacing", "memory")
linespacing_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "linespacing", "memory")
linespacing_layer_provider = linespacing_layer.dataProvider()
linespacing_layer_provider.addAttributes([
    QgsField("id", QVariant.String),  # Campo para el nombre
    #******<Parametros esenciales***************
    QgsField("nconds", QVariant.String),
    QgsField("nphases", QVariant.String),
    QgsField("units", QVariant.String),
    QgsField("x", QVariant.String),
    QgsField("h", QVariant.String)
])
linespacing_layer.updateFields()
linespacing_layer_path = project_path + '/linespacing.shp'
QgsVectorFileWriter.writeAsVectorFormat(linespacing_layer, linespacing_layer_path, 'utf-8', linespacing_layer.crs(), 'ESRI Shapefile')


# Crear capa para WireData
#wiredata_layer = QgsVectorLayer("None", "wiredata", "memory")
wiredata_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "wiredata", "memory")
wiredata_layer_provider = wiredata_layer.dataProvider()
wiredata_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("rdc", QVariant.String),
    QgsField("runits", QVariant.String),
    QgsField("diam", QVariant.String),
    QgsField("radunits", QVariant.String),
    QgsField("emergamps", QVariant.String)
    #******<Parametros esenciales no presentes en interfaz*****
    #******<Parametros adicionales**************
    # QgsField("capradius", QVariant.String),
    # QgsField("gmrac", QVariant.String),
    # QgsField("gmrunits", QVariant.String),
    # QgsField("like", QVariant.String),
    # QgsField("normamps", QVariant.String),
    # QgsField("rac", QVariant.String),
    # QgsField("radius", QVariant.String),
    # QgsField("ratings", QVariant.String),
    # QgsField("seasons", QVariant.String)
    #******>Parametros***************
])
wiredata_layer.updateFields()
wiredata_layer_path = project_path + '/wiredata.shp'
QgsVectorFileWriter.writeAsVectorFormat(wiredata_layer, wiredata_layer_path, 'utf-8', wiredata_layer.crs(), 'ESRI Shapefile')



# Crear nuevas instancias de capas utilizando QgsVectorLayer
node_mt_layer = QgsVectorLayer(node_mt_layer_path, "nodos_mt", "ogr")
node_bt_layer = QgsVectorLayer(node_bt_layer_path, "nodos_bt", "ogr")
line_mt_layer = QgsVectorLayer(line_mt_layer_path, "lineas_mt", "ogr")
line_bt_layer = QgsVectorLayer(line_bt_layer_path, "lineas_bt", "ogr")
generator_layer = QgsVectorLayer(generator_layer_path, "generadores", "ogr")
pv_system_layer = QgsVectorLayer(pv_system_layer_path, "sistemas_fotovoltaicos", "ogr")
load_layer = QgsVectorLayer(load_layer_path, "cargas", "ogr")
capacitor_layer = QgsVectorLayer(capacitor_layer_path, "capacitores", "ogr")
switch_layer = QgsVectorLayer(switch_layer_path, "interruptores", "ogr")
transformer_layer = QgsVectorLayer(transformer_layer_path, "transformadores", "ogr")
et_layer = QgsVectorLayer(et_layer_path, "estacion_transformadora", "ogr")
seta_layer = QgsVectorLayer(seta_layer_path, "setas", "ogr")
linecode_layer = QgsVectorLayer(linecode_layer_path, "linecode", "ogr")
linegeometry_layer = QgsVectorLayer(linegeometry_layer_path, "linegeometry", "ogr")
linespacing_layer = QgsVectorLayer(linespacing_layer_path, "linespacing", "ogr")
wiredata_layer = QgsVectorLayer(wiredata_layer_path, "wiredata", "ogr")



# Crear y organizar grupos de capas
#project = QgsProject.instance()
root = QgsProject.instance().layerTreeRoot()

# Crear grupo para capas de Media Tensión (MT)
group_mt = root.addGroup("Media Tensión")
group_mt.addLayer(QgsProject.instance().addMapLayer(seta_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(transformer_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(generator_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(pv_system_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(load_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(capacitor_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(et_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(node_mt_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(switch_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(line_mt_layer, False))

# Crear grupo para capas de Baja Tensión (BT)
group_bt = root.addGroup("Baja Tensión")
group_bt.addLayer(QgsProject.instance().addMapLayer(node_bt_layer, False))
group_bt.addLayer(QgsProject.instance().addMapLayer(line_bt_layer, False))

# Crear grupo para capas LIB
lib_group = root.addGroup("LIB")
lib_group.addLayer(QgsProject.instance().addMapLayer(linecode_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(linegeometry_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(linespacing_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(wiredata_layer, False))


# Simbología para los generadores
svg_path = project_path + '/iconos/generador.svg'  # Definir la ruta del archivo SVG
svg_marker = QgsSvgMarkerSymbolLayer(svg_path)  # Crear una nueva instancia de QgsSvgMarkerSymbolLayer
svg_marker.setSize(10)  # Establecer el tamaño del marcador SVG
svg_marker.setOffset(QPointF(2.3, -5.2))  # Establecer el desplazamiento del marcador SVG
symbol = QgsMarkerSymbol()  # Crear un nuevo símbolo de marcador
symbol.appendSymbolLayer(svg_marker)  # Añadir la capa de marcador SVG
generator_layer.renderer().setSymbol(symbol)  # Establecer el símbolo para la capa de generadores
generator_layer.triggerRepaint()  # Actualizar la capa de generadores
generator_layer.setMinimumScale(10000)
generator_layer.setScaleBasedVisibility(True)

# Simbología para los sistemas fotovoltaicos
pv_svg_path = project_path + '/iconos/sistema_fotovoltaico.svg'  # Definir la ruta del archivo SVG
pv_svg_marker = QgsSvgMarkerSymbolLayer(pv_svg_path)  # Crear una nueva instancia de QgsSvgMarkerSymbolLayer
pv_svg_marker.setSize(10)  # Establecer el tamaño del marcador SVG
pv_svg_marker.setOffset(QPointF(2.3, -5.2))  # Establecer el desplazamiento del marcador SVG
pv_symbol = QgsMarkerSymbol()  # Crear un nuevo símbolo de marcador
pv_symbol.appendSymbolLayer(pv_svg_marker)  # Añadir la capa de marcador SVG
pv_system_layer.renderer().setSymbol(pv_symbol)  # Establecer el símbolo para la capa de sistemas fotovoltaicos
pv_system_layer.triggerRepaint()  # Actualizar la capa de sistemas fotovoltaicos
pv_system_layer.setMinimumScale(10000)
pv_system_layer.setScaleBasedVisibility(True)

# Simbología para las líneas MT
line_mt_symbol = QgsSymbol.defaultSymbol(line_mt_layer.geometryType())  # Crear un nuevo símbolo de línea
line_mt_symbol_layer = QgsSimpleLineSymbolLayer()  # Crear una capa de símbolo de línea simple y configurar sus propiedades
line_mt_symbol_layer.setColor(QColor(255, 127, 0))
line_mt_symbol_layer.setWidth(0.7)  # La anchura se establece en milímetros
line_mt_symbol.changeSymbolLayer(0, line_mt_symbol_layer)  # Reemplazar la capa de símbolo por defecto con la nueva capa de símbolo de línea simple
line_mt_renderer = QgsCategorizedSymbolRenderer('', [QgsRendererCategory('', line_mt_symbol, '')])  # Crear un nuevo renderizador utilizando el símbolo de línea definido
line_mt_layer.setRenderer(line_mt_renderer)  # Establecer el renderizador en la capa de líneas
line_mt_layer.triggerRepaint()  # Actualizar la capa de líneas para aplicar el nuevo estilo

# Simbología para las líneas MT
line_mt_symbol = QgsSymbol.defaultSymbol(line_mt_layer.geometryType())  # Crear un nuevo símbolo de línea
# Crear un renderizador basado en reglas
rule_based_renderer = QgsRuleBasedRenderer(line_mt_symbol)
# Obtener la raíz del renderizador
root_rule = rule_based_renderer.rootRule()

# Regla para cuando P.Activa es NULL
rule_default = root_rule.children()[0].clone()
rule_default.setFilterExpression('"P.Activa" IS NULL')
rule_default.symbol().changeSymbolLayer(0, QgsSimpleLineSymbolLayer(color=QColor(255, 127, 0), width=0.5))  # Color naranja, grosor por defecto
rule_default.setLabel("P.Activa is NULL")
root_rule.appendChild(rule_default)

# Definir reglas para diferentes rangos de P.Activa
rule1 = root_rule.children()[0].clone()
rule1.setFilterExpression('"P.Activa" <= 10')
rule1.symbol().changeSymbolLayer(0, QgsSimpleLineSymbolLayer(color=QColor('gray'), width=0.5))
rule1.setLabel("P.Activa <= 10")
root_rule.appendChild(rule1)

rule2 = root_rule.children()[0].clone()
rule2.setFilterExpression('"P.Activa" > 10 AND "P.Activa" <= 50')
rule2.symbol().changeSymbolLayer(0, QgsSimpleLineSymbolLayer(color=QColor(255, 127, 0), width=1.0))
rule2.setLabel("10 < P.Activa <= 50")
root_rule.appendChild(rule2)

rule3 = root_rule.children()[0].clone()
rule3.setFilterExpression('"P.Activa" > 50 AND "P.Activa" <= 100')
rule3.symbol().changeSymbolLayer(0, QgsSimpleLineSymbolLayer(color=QColor(255, 127, 0), width=1.5))
rule3.setLabel("50 < P.Activa <= 100")
root_rule.appendChild(rule3)

rule4 = root_rule.children()[0].clone()
rule4.setFilterExpression('"P.Activa" > 100 AND "P.Activa" <= 500')
rule4.symbol().changeSymbolLayer(0, QgsSimpleLineSymbolLayer(color=QColor(255, 127, 0), width=2.0))
rule4.setLabel("100 < P.Activa <= 500")
root_rule.appendChild(rule4)

rule5 = root_rule.children()[0].clone()
rule5.setFilterExpression('"P.Activa" > 500 AND "P.Activa" <= 1000')
rule5.symbol().changeSymbolLayer(0, QgsSimpleLineSymbolLayer(color=QColor(255, 127, 0), width=2.5))
rule5.setLabel("500 < P.Activa <= 1000")
root_rule.appendChild(rule5)

rule6 = root_rule.children()[0].clone()
rule6.setFilterExpression('"P.Activa" > 1000')
rule6.symbol().changeSymbolLayer(0, QgsSimpleLineSymbolLayer(color=QColor(255, 127, 0), width=3.0))
rule6.setLabel("P.Activa > 1000")
root_rule.appendChild(rule6)

# Establecer el renderizador en la capa de líneas
line_mt_layer.setRenderer(rule_based_renderer)

# Configurar el etiquetado para las líneas MT
label_settings = QgsPalLayerSettings()
label_settings.fieldName = "\"P.Activa\" || ' kW'"  # Concatenar el valor del campo "P.Activa" con el texto ' kW'
label_settings.enabled = True

# Crear un objeto de texto para las etiquetas
text_format = QgsTextFormat()
text_format.setFont(QFont('Arial', 10))
text_format.setSize(10)
text_format.setColor(QColor('black'))

# Asignar el formato de texto al etiquetado
label_settings.setFormat(text_format)

# Aplicar el etiquetado a la capa de líneas MT
labeling = QgsVectorLayerSimpleLabeling(label_settings)
line_mt_layer.setLabeling(labeling)
line_mt_layer.setLabelsEnabled(True)
line_mt_layer.triggerRepaint()



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


# Configurar el etiquetado para las cargas
load_label_settings = QgsPalLayerSettings()
load_label_settings.fieldName = "\"P.Activa\" || ' kW'"  # Concatenar el valor del campo "P.Activa" con el texto ' kW'
load_label_settings.enabled = True

# Crear un objeto de texto para las etiquetas
load_text_format = QgsTextFormat()
load_text_format.setFont(QFont('Arial', 10))
load_text_format.setSize(10)
load_text_format.setColor(QColor('blue'))

# Asignar el formato de texto al etiquetado
load_label_settings.setFormat(load_text_format)

# Aplicar el etiquetado a la capa de cargas
load_labeling = QgsVectorLayerSimpleLabeling(load_label_settings)
load_layer.setLabeling(load_labeling)
load_layer.setLabelsEnabled(True)

# Forzar la actualización de la capa
load_layer.triggerRepaint()




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
# Forzar la actualización de la capa
node_mt_layer.triggerRepaint()

# Configurar la visibilidad basada en la escala
node_mt_layer.setMinimumScale(10000)
node_mt_layer.setScaleBasedVisibility(True)


# Configurar el etiquetado para la capa de nodos MT
label_settings = QgsPalLayerSettings()
#label_settings.fieldName = "pu1"  # Usar directamente el campo "pu1"
label_settings.fieldName = "\"pu1\" || ' V.pu'"  # Concatenar el valor del campo "pu1" con el texto ' [V.pu]'
#label_settings.fieldName = "concat(\"pu1\", ' [V.pu]')"
label_settings.enabled = True

# Crear un objeto de texto para las etiquetas
text_format = QgsTextFormat()
text_format.setFont(QFont('Arial', 10))
text_format.setSize(10)
text_format.setColor(QColor('orange'))

# Asignar el formato de texto al etiquetado
label_settings.setFormat(text_format)

# Aplicar el etiquetado a la capa de nodos MT
labeling = QgsVectorLayerSimpleLabeling(label_settings)
node_mt_layer.setLabeling(labeling)
node_mt_layer.setLabelsEnabled(True)

# Forzar la actualización de la capa
node_mt_layer.triggerRepaint()



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


# Simbología para los capacitores
capacitor_symbol = QgsMarkerSymbol()
while capacitor_symbol.symbolLayerCount() > 0:
    capacitor_symbol.deleteSymbolLayer(0)

# Capa de símbolo para la línea oblicua del capacitor
line_o1_layer = QgsSimpleMarkerSymbolLayer()
line_o1_layer.setShape(QgsSimpleMarkerSymbolLayer.Line)
line_o1_layer.setColor(QColor('green'))
line_o1_layer.setSize(4.0)
line_o1_layer.setAngle(45)
line_o1_layer.setOffset(QPointF(-0.2, 2.4))
# Capa de símbolo para la primera línea horizontal del capacitor
line_h1_layer = QgsSimpleMarkerSymbolLayer()
line_h1_layer.setShape(QgsSimpleMarkerSymbolLayer.Line)
line_h1_layer.setColor(QColor('green'))
line_h1_layer.setSize(4.0)
line_h1_layer.setAngle(90)
line_h1_layer.setOffset(QPointF(3.4, 3.4))
# Capa de símbolo para la segunda línea horizontal del capacitor
line_h2_layer = QgsSimpleMarkerSymbolLayer()
line_h2_layer.setShape(QgsSimpleMarkerSymbolLayer.Line)
line_h2_layer.setColor(QColor('green'))
line_h2_layer.setSize(4.0)
line_h2_layer.setAngle(90)
line_h2_layer.setOffset(QPointF(4.2, 3.4))
# Capa de símbolo para la linea vertical del capacitor
line_v1_layer = QgsSimpleMarkerSymbolLayer()
line_v1_layer.setShape(QgsSimpleMarkerSymbolLayer.Line)
line_v1_layer.setColor(QColor('green'))
line_v1_layer.setSize(1.6)
line_v1_layer.setAngle(0)
line_v1_layer.setOffset(QPointF(-3.2, 5.4))
# Capa de símbolo para la línea de tierra
line_h3_layer = QgsSimpleMarkerSymbolLayer()
line_h3_layer.setShape(QgsSimpleMarkerSymbolLayer.Line)
line_h3_layer.setColor(QColor('green'))
line_h3_layer.setSize(3.0)
line_h3_layer.setAngle(90)
line_h3_layer.setOffset(QPointF(6.2, 3.4))
# Añadir las capas de símbolo al símbolo del capacitor
capacitor_symbol.appendSymbolLayer(line_o1_layer)
capacitor_symbol.appendSymbolLayer(line_h1_layer)
capacitor_symbol.appendSymbolLayer(line_h2_layer)
capacitor_symbol.appendSymbolLayer(line_v1_layer)
capacitor_symbol.appendSymbolLayer(line_h3_layer)
# Establecer el renderizador para la capa de capacitores
capacitor_layer.setRenderer(QgsSingleSymbolRenderer(capacitor_symbol))
capacitor_layer.triggerRepaint()
capacitor_layer.setMinimumScale(10000)
capacitor_layer.setScaleBasedVisibility(True)








