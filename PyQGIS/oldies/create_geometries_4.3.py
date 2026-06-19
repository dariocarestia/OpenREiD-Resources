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
    QgsField("start_ph", QVariant.String),
    QgsField("end_node", QVariant.String),
    QgsField("end_ph", QVariant.String),
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
line_bt_layer_provider.addAttributes([QgsField("id", QVariant.String), QgsField("start_node", QVariant.String), QgsField("start_ph", QVariant.String), QgsField("end_node", QVariant.String), QgsField("end_ph", QVariant.String)])
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
    QgsField("start_ph", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("Phases", QVariant.String),
    QgsField("kV", QVariant.String),
    QgsField("kW", QVariant.String),
    QgsField("PF", QVariant.String),
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("daily", QVariant.String)
    #******<Parametros adicionales**************
    # ...... Son un montón
    # ......
    #******<Parametros de resultados***************
    #QgsField("pu1", QVariant.String)
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
    QgsField("start_ph", QVariant.String),
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
    QgsField("start_ph", QVariant.String),
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
    QgsField("wdg1_ph", QVariant.String),
    QgsField("wdg2_node", QVariant.String),
    QgsField("wdg2_ph", QVariant.String),
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
    QgsField("ppm_afloat", QVariant.String),
    #******<Parametros adicionales**************
    QgsField("nwindings", QVariant.String),
    QgsField("xfmrcode", QVariant.String),
    QgsField("tap", QVariant.String)
    #QgsField("coretype", QVariant.String),
    #QgsField("isdelta", QVariant.String),
    #QgsField("maxtap", QVariant.String),
    #QgsField("mintap", QVariant.String),
    #QgsField("numtaps", QVariant.String),
    #QgsField("r", QVariant.String),
    #QgsField("rdcohms1", QVariant.String), #<-depende del Wdg
    #QgsField("rdcohms2", QVariant.String), #<-depende del Wdg
    #QgsField("rneut", QVariant.String),
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
    QgsField("start_ph", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("pu", QVariant.String),
    QgsField("basekv", QVariant.String),
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("phases", QVariant.String),
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
    QgsField("wdg1_ph", QVariant.String),
    QgsField("wdg2_node", QVariant.String),
    QgsField("wdg2_ph", QVariant.String)
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
    QgsField("start_ph", QVariant.String),
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



# Crear capa para XfmrCode
xfmrcode_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "xfmrcode", "memory")
xfmrcode_layer_provider = xfmrcode_layer.dataProvider()
xfmrcode_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("phases", QVariant.String),
    QgsField("windings", QVariant.String),
    QgsField("kvs", QVariant.String),
    QgsField("kvas", QVariant.String),
    QgsField("conns", QVariant.String),
    QgsField("%rs", QVariant.String),
    QgsField("xhl", QVariant.String),
    QgsField("xht", QVariant.String),
    QgsField("xlt", QVariant.String),
    QgsField("maxtap", QVariant.String),
    QgsField("mintap", QVariant.String),
    QgsField("%loadloss", QVariant.String),
    QgsField("%nloadloss", QVariant.String),
    QgsField("ppm_afloat", QVariant.String),
    QgsField("%imag", QVariant.String)
    #******>Parametros***************
])
xfmrcode_layer.updateFields()
xfmrcode_layer_path = project_path + '/xfmrcode.shp'
QgsVectorFileWriter.writeAsVectorFormat(xfmrcode_layer, xfmrcode_layer_path, 'utf-8', xfmrcode_layer.crs(), 'ESRI Shapefile')



# Crear capa para XYCurve
xycurve_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "xycurve", "memory")
xycurve_layer_provider = xycurve_layer.dataProvider()
xycurve_layer_provider.addAttributes([
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("id", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("npts", QVariant.String),
    QgsField("points", QVariant.String),
    QgsField("csvfile", QVariant.String)
    #******<Parametros adicionales**************
    #******>Parametros***************
])
xycurve_layer.updateFields()
xycurve_layer_path = project_path + '/xycurve.shp'
QgsVectorFileWriter.writeAsVectorFormat(xycurve_layer, xycurve_layer_path, 'utf-8', xycurve_layer.crs(), 'ESRI Shapefile')


# Crear capa para TShapes
tshape_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "tshape", "memory")
tshape_layer_provider = tshape_layer.dataProvider()
tshape_layer_provider.addAttributes([
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("id", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("npts", QVariant.String),
    QgsField("temp", QVariant.String),
    QgsField("csvfile", QVariant.String)
    #******<Parametros adicionales**************
    #******>Parametros***************
])
tshape_layer.updateFields()
tshape_layer_path = project_path + '/tshape.shp'
QgsVectorFileWriter.writeAsVectorFormat(tshape_layer, tshape_layer_path, 'utf-8', tshape_layer.crs(), 'ESRI Shapefile')


# Crear capa para LoadShapes
#loadshape_layer = QgsVectorLayer("None", "LoadShape", "memory")
loadshape_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "loadshape", "memory")
loadshape_layer_provider = loadshape_layer.dataProvider()
loadshape_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("npts", QVariant.String),
    QgsField("interval", QVariant.String),
    QgsField("mult", QVariant.String),
    QgsField("csvfile", QVariant.String)
    #******<Parametros esenciales no presentes en interfaz*****
    #******<Parametros adicionales**************
    #******>Parametros***************
])
loadshape_layer.updateFields()
loadshape_layer_path = project_path + '/loadshape.shp'
QgsVectorFileWriter.writeAsVectorFormat(loadshape_layer, loadshape_layer_path, 'utf-8', loadshape_layer.crs(), 'ESRI Shapefile')


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
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("id", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("nconds", QVariant.String),
    QgsField("nphases", QVariant.String),
    QgsField("spacing", QVariant.String),
    QgsField("wires", QVariant.String),
    #******<Parametros adicionales**************
    QgsField("reduce", QVariant.String)
    # QgsField("cncable", QVariant.String),
    # QgsField("cncables", QVariant.String),
    # QgsField("emergamps", QVariant.String),
    # QgsField("h", QVariant.String),
    # QgsField("like", QVariant.String),
    # QgsField("linetype", QVariant.String),
    # QgsField("normamps", QVariant.String),
    # QgsField("ratings", QVariant.String),
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
    #******<Parametros esenciales no presentes en interfaz*****
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
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("id", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("rdc", QVariant.String),
    QgsField("runits", QVariant.String),
    QgsField("diam", QVariant.String),
    QgsField("radunits", QVariant.String),
    QgsField("emergamps", QVariant.String)
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

# Crear capa para Settings
settings_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "settings", "memory")
settings_layer_provider = settings_layer.dataProvider()
settings_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("frequency", QVariant.String),
    QgsField("voltbases", QVariant.String),
    QgsField("solu_mode", QVariant.String)
])
settings_layer.updateFields()
settings_layer_path = project_path + '/settings.shp'
QgsVectorFileWriter.writeAsVectorFormat(settings_layer, settings_layer_path, 'utf-8', settings_layer.crs(), 'ESRI Shapefile')

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
loadshape_layer = QgsVectorLayer(loadshape_layer_path, "loadshape", "ogr")
settings_layer = QgsVectorLayer(settings_layer_path, "settings", "ogr")
tshape_layer = QgsVectorLayer(tshape_layer_path, "tshape", "ogr")
xycurve_layer = QgsVectorLayer(xycurve_layer_path, "xycurve", "ogr")
xfmrcode_layer  = QgsVectorLayer(xfmrcode_layer_path, "xfmrcode", "ogr")

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
lib_group.addLayer(QgsProject.instance().addMapLayer(loadshape_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(tshape_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(xycurve_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(settings_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(xfmrcode_layer, False))

# Aplicar estilos desde archivos .qml
line_mt_layer.loadNamedStyle(project_path + '/estilos/lineas_mt.qml')
node_mt_layer.loadNamedStyle(project_path + '/estilos/nodos_mt.qml')
load_layer.loadNamedStyle(project_path + '/estilos/cargas.qml')
capacitor_layer.loadNamedStyle(project_path + '/estilos/capacitores.qml')
et_layer.loadNamedStyle(project_path + '/estilos/estacion_transformadora.qml')
generator_layer.loadNamedStyle(project_path + '/estilos/generadores.qml')
switch_layer.loadNamedStyle(project_path + '/estilos/interruptores.qml')
line_bt_layer.loadNamedStyle(project_path + '/estilos/lineas_bt.qml')
node_bt_layer.loadNamedStyle(project_path + '/estilos/nodos_bt.qml')
seta_layer.loadNamedStyle(project_path + '/estilos/setas.qml')
pv_system_layer.loadNamedStyle(project_path + '/estilos/sistemas_fotovoltaicos.qml')
transformer_layer.loadNamedStyle(project_path + '/estilos/transformadores.qml')

# Configurar la visibilidad basada en la escala para todas las capas
#line_mt_layer.setMinimumScale(10000)
#line_mt_layer.setScaleBasedVisibility(True)
node_mt_layer.setMinimumScale(10000)
node_mt_layer.setScaleBasedVisibility(True)
load_layer.setMinimumScale(10000)
load_layer.setScaleBasedVisibility(True)
capacitor_layer.setMinimumScale(10000)
capacitor_layer.setScaleBasedVisibility(True)
#et_layer.setMinimumScale(10000)
#et_layer.setScaleBasedVisibility(True)
generator_layer.setMinimumScale(10000)
generator_layer.setScaleBasedVisibility(True)
switch_layer.setMinimumScale(10000)
switch_layer.setScaleBasedVisibility(True)
line_bt_layer.setMinimumScale(10000)
line_bt_layer.setScaleBasedVisibility(True)
node_bt_layer.setMinimumScale(5000)
node_bt_layer.setScaleBasedVisibility(True)
seta_layer.setMinimumScale(10000)
seta_layer.setScaleBasedVisibility(True)
pv_system_layer.setMinimumScale(10000)
pv_system_layer.setScaleBasedVisibility(True)
transformer_layer.setMinimumScale(10000)
transformer_layer.setScaleBasedVisibility(True)

# Forzar la actualización de todas las capas
line_mt_layer.triggerRepaint()
node_mt_layer.triggerRepaint()
load_layer.triggerRepaint()
capacitor_layer.triggerRepaint()
et_layer.triggerRepaint()
generator_layer.triggerRepaint()
switch_layer.triggerRepaint()
line_bt_layer.triggerRepaint()
node_bt_layer.triggerRepaint()
seta_layer.triggerRepaint()
pv_system_layer.triggerRepaint()
transformer_layer.triggerRepaint()








