# Importar módulos necesarios
import os
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

# Directorios de salida para shapefiles
red_dir = os.path.join(project_path, "RED")
lib_dir = os.path.join(project_path, "LIB")
os.makedirs(red_dir, exist_ok=True)
os.makedirs(lib_dir, exist_ok=True)

# Crear capa de nodos MT
node_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "nodos", "memory")
node_layer_provider = node_layer.dataProvider()
node_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    #******<Parametros de resultados***************
    QgsField("kVBaseLL", QVariant.String),
    QgsField("pu1", QVariant.String)
])
node_layer.updateFields()

# Guardar la capa de nodos MT como Shapefile en la ruta del proyecto
node_layer_path = os.path.join(red_dir, 'nodos.shp')
QgsVectorFileWriter.writeAsVectorFormat(node_layer, node_layer_path, 'utf-8', node_layer.crs(), 'ESRI Shapefile')
#QgsVectorFileWriter.writeAsVectorFormat(node_mt_layer, node_mt_layer_path, 'utf-8', crs, 'ESRI Shapefile')


# Crear capa de líneas MT
line_layer = QgsVectorLayer(f"LineString?crs={crs.authid()}", "lineas", "memory")
line_layer_provider = line_layer.dataProvider()
line_layer_provider.addAttributes([
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
    #******<Parametros adicionales**************
    QgsField("linecode", QVariant.String),
    QgsField("geometry", QVariant.String),
    #QgsField("Rmatrix", QVariant.String),
    #QgsField("Xmatrix", QVariant.String),
    #QgsField("Cmatrix", QVariant.String),
    #******<Parametros de resultados***************
    QgsField("kVBaseLL", QVariant.String),
    QgsField("P.Activa", QVariant.String),
    QgsField("P.Reactiva", QVariant.String)

])
line_layer.updateFields()

# Guardar la capa de líneas MT como Shapefile en la ruta del proyecto
line_layer_path = os.path.join(red_dir, 'lineas.shp')
QgsVectorFileWriter.writeAsVectorFormat(line_layer, line_layer_path, 'utf-8', line_layer.crs(), 'ESRI Shapefile')


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
generator_layer_path = os.path.join(red_dir, 'generadores.shp')
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
pv_system_layer_path = os.path.join(red_dir, 'sistemas_fotovoltaicos.shp')
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
    QgsField("NumCust", QVariant.String),
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
load_layer_path = os.path.join(red_dir, 'cargas.shp')
QgsVectorFileWriter.writeAsVectorFormat(load_layer, load_layer_path, 'utf-8', load_layer.crs(), 'ESRI Shapefile')


# Crear capa de puntos para interruptores
switch_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "interruptores", "memory")
switch_layer_provider = switch_layer.dataProvider()
switch_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("MonObj", QVariant.String),
    QgsField("MonTerm", QVariant.String),
    QgsField("SwObj", QVariant.String),
    QgsField("SwTerm", QVariant.String),
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("Normal", QVariant.String),
    QgsField("State", QVariant.String)
    #******<Parametros adicionales**************
    # QgsField("State", QVariant.String) --> Figura un valor numérico
    #******>Parametros***************
])
switch_layer.updateFields()


# Guardar la capa de puntos de interruptores como Shapefile en la ruta del proyecto
switch_layer_path = os.path.join(red_dir, 'interruptores.shp')
QgsVectorFileWriter.writeAsVectorFormat(switch_layer, switch_layer_path, 'utf-8', switch_layer.crs(), 'ESRI Shapefile')

# Crear capa de puntos para fusibles
fuse_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "fusibles", "memory")
fuse_layer_provider = fuse_layer.dataProvider()
fuse_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("MonObj", QVariant.String),
    QgsField("MonTerm", QVariant.String),
    QgsField("SwObj", QVariant.String),
    QgsField("SwTerm", QVariant.String),
    QgsField("FuseCurve", QVariant.String),
    QgsField("RatedCurr", QVariant.String),
    QgsField("Delay", QVariant.String),
    QgsField("Normal", QVariant.String),
    QgsField("State", QVariant.String)
])
fuse_layer.updateFields()

fuse_layer_path = os.path.join(red_dir, 'fusibles.shp')
QgsVectorFileWriter.writeAsVectorFormat(fuse_layer, fuse_layer_path, 'utf-8', fuse_layer.crs(), 'ESRI Shapefile')

# Crear capa de puntos para reconectadores
recloser_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "reconectadores", "memory")
recloser_layer_provider = recloser_layer.dataProvider()
recloser_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("MonObj", QVariant.String),
    QgsField("MonTerm", QVariant.String),
    QgsField("SwObj", QVariant.String),
    QgsField("SwTerm", QVariant.String),
    QgsField("PhFast", QVariant.String),
    QgsField("PhDelay", QVariant.String),
    QgsField("PhTrip", QVariant.String),
    QgsField("PhInst", QVariant.String),
    QgsField("TDPhFast", QVariant.String),
    QgsField("TDPhDel", QVariant.String),
    QgsField("GrFast", QVariant.String),
    QgsField("GrDelay", QVariant.String),
    QgsField("GrTrip", QVariant.String),
    QgsField("GrInst", QVariant.String),
    QgsField("TDGrFast", QVariant.String),
    QgsField("TDGrDel", QVariant.String),
    QgsField("NumFast", QVariant.String),
    QgsField("Shots", QVariant.String),
    QgsField("ReclInt", QVariant.String),
    QgsField("Delay", QVariant.String),
    QgsField("Reset", QVariant.String),
    QgsField("State", QVariant.String)
])
recloser_layer.updateFields()

recloser_layer_path = os.path.join(red_dir, 'reconectadores.shp')
QgsVectorFileWriter.writeAsVectorFormat(recloser_layer, recloser_layer_path, 'utf-8', recloser_layer.crs(), 'ESRI Shapefile')

# Crear capa de puntos para reles
relay_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "reles", "memory")
relay_layer_provider = relay_layer.dataProvider()
relay_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("MonObj", QVariant.String),
    QgsField("MonTerm", QVariant.String),
    QgsField("SwObj", QVariant.String),
    QgsField("SwTerm", QVariant.String),
    QgsField("type", QVariant.String),
    QgsField("PhCurve", QVariant.String),
    QgsField("GrCurve", QVariant.String),
    QgsField("PhTrip", QVariant.String),
    QgsField("GrTrip", QVariant.String),
    QgsField("TDPhase", QVariant.String),
    QgsField("TDGround", QVariant.String),
    QgsField("PhInst", QVariant.String),
    QgsField("GrInst", QVariant.String),
    QgsField("OVCurve", QVariant.String),
    QgsField("UVCurve", QVariant.String),
    QgsField("kvbase", QVariant.String),
    QgsField("Reset", QVariant.String),
    QgsField("Shots", QVariant.String),
    QgsField("ReclInt", QVariant.String),
    QgsField("Delay", QVariant.String),
    QgsField("BrkTime", QVariant.String),
    QgsField("State", QVariant.String)
])
relay_layer.updateFields()

relay_layer_path = os.path.join(red_dir, 'reles.shp')
QgsVectorFileWriter.writeAsVectorFormat(relay_layer, relay_layer_path, 'utf-8', relay_layer.crs(), 'ESRI Shapefile')

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
transformer_layer_path = os.path.join(red_dir, 'transformadores.shp')
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
et_layer_path = os.path.join(red_dir, 'estacion_transformadora.shp')
QgsVectorFileWriter.writeAsVectorFormat(et_layer, et_layer_path, 'utf-8', et_layer.crs(), 'ESRI Shapefile')


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
capacitor_layer_path = os.path.join(red_dir, 'capacitores.shp')
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
xfmrcode_layer_path = os.path.join(lib_dir, 'xfmrcode.shp')
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
xycurve_layer_path = os.path.join(lib_dir, 'xycurve.shp')
QgsVectorFileWriter.writeAsVectorFormat(xycurve_layer, xycurve_layer_path, 'utf-8', xycurve_layer.crs(), 'ESRI Shapefile')


# Crear capa para TCC_Curve
tcccurve_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "tcccurve", "memory")
tcccurve_layer_provider = tcccurve_layer.dataProvider()
tcccurve_layer_provider.addAttributes([
    #******<Parametros esenciales no presentes en interfaz*****
    QgsField("id", QVariant.String),
    #******<Parametros esenciales***************
    QgsField("npts", QVariant.String),
    QgsField("c_array", QVariant.String),
    QgsField("t_array", QVariant.String)
    #******<Parametros adicionales**************
    #******>Parametros***************
])
tcccurve_layer.updateFields()
tcccurve_layer_path = os.path.join(lib_dir, 'tcccurve.shp')
QgsVectorFileWriter.writeAsVectorFormat(tcccurve_layer, tcccurve_layer_path, 'utf-8', tcccurve_layer.crs(), 'ESRI Shapefile')


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
tshape_layer_path = os.path.join(lib_dir, 'tshape.shp')
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
loadshape_layer_path = os.path.join(lib_dir, 'loadshape.shp')
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
linecode_layer_path = os.path.join(lib_dir, 'linecode.shp')
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
    QgsField("cncables", QVariant.String),
    QgsField("tscables", QVariant.String),
    #******<Parametros adicionales**************
    QgsField("reduce", QVariant.String)
    # QgsField("cncable", QVariant.String),
    # QgsField("emergamps", QVariant.String),
    # QgsField("h", QVariant.String),
    # QgsField("like", QVariant.String),
    # QgsField("linetype", QVariant.String),
    # QgsField("normamps", QVariant.String),
    # QgsField("ratings", QVariant.String),
    # QgsField("seasons", QVariant.String),
    # QgsField("tscable", QVariant.String),
    # QgsField("units", QVariant.String),
    # QgsField("wire", QVariant.String),
    # QgsField("wires", QVariant.String),
    # QgsField("x", QVariant.String)
    #******>Parametros***************
])
linegeometry_layer.updateFields()
# Guardar la capa como shapefile en el directorio del proyecto
linegeometry_layer_path = os.path.join(lib_dir, 'linegeometry.shp')
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
linespacing_layer_path = os.path.join(lib_dir, 'linespacing.shp')
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
    QgsField("normamps", QVariant.String)
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
wiredata_layer_path = os.path.join(lib_dir, 'wiredata.shp')
QgsVectorFileWriter.writeAsVectorFormat(wiredata_layer, wiredata_layer_path, 'utf-8', wiredata_layer.crs(), 'ESRI Shapefile')


# Crear capa para CNData
cndata_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "cndata", "memory")
cndata_layer_provider = cndata_layer.dataProvider()
cndata_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("runits", QVariant.String),
    QgsField("radunits", QVariant.String),
    QgsField("gmrunits", QVariant.String),
    QgsField("inslayer", QVariant.String),
    QgsField("diains", QVariant.String),
    QgsField("diacable", QVariant.String),
    QgsField("epsr", QVariant.String),
    QgsField("rac", QVariant.String),
    QgsField("diam", QVariant.String),
    QgsField("normamps", QVariant.String),
    QgsField("gmrac", QVariant.String),
    QgsField("rstrand", QVariant.String),
    QgsField("gmrstrand", QVariant.String),
    QgsField("diastrand", QVariant.String),
    QgsField("k", QVariant.String)
])
cndata_layer.updateFields()
cndata_layer_path = os.path.join(lib_dir, 'cndata.shp')
QgsVectorFileWriter.writeAsVectorFormat(cndata_layer, cndata_layer_path, 'utf-8', cndata_layer.crs(), 'ESRI Shapefile')


# Crear capa para TSData
tsdata_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "tsdata", "memory")
tsdata_layer_provider = tsdata_layer.dataProvider()
tsdata_layer_provider.addAttributes([
    QgsField("id", QVariant.String),
    QgsField("runits", QVariant.String),
    QgsField("radunits", QVariant.String),
    QgsField("gmrunits", QVariant.String),
    QgsField("inslayer", QVariant.String),
    QgsField("diains", QVariant.String),
    QgsField("diacable", QVariant.String),
    QgsField("epsr", QVariant.String),
    QgsField("rac", QVariant.String),
    QgsField("diam", QVariant.String),
    QgsField("normamps", QVariant.String),
    QgsField("gmrac", QVariant.String),
    QgsField("diashield", QVariant.String),
    QgsField("tapelayer", QVariant.String),
    QgsField("tapelap", QVariant.String)
])
tsdata_layer.updateFields()
tsdata_layer_path = os.path.join(lib_dir, 'tsdata.shp')
QgsVectorFileWriter.writeAsVectorFormat(tsdata_layer, tsdata_layer_path, 'utf-8', tsdata_layer.crs(), 'ESRI Shapefile')


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
settings_layer_path = os.path.join(lib_dir, 'settings.shp')
QgsVectorFileWriter.writeAsVectorFormat(settings_layer, settings_layer_path, 'utf-8', settings_layer.crs(), 'ESRI Shapefile')

# Crear nuevas instancias de capas utilizando QgsVectorLayer
node_layer = QgsVectorLayer(node_layer_path, "nodos", "ogr")
line_layer = QgsVectorLayer(line_layer_path, "lineas", "ogr")
generator_layer = QgsVectorLayer(generator_layer_path, "generadores", "ogr")
pv_system_layer = QgsVectorLayer(pv_system_layer_path, "sistemas_fotovoltaicos", "ogr")
load_layer = QgsVectorLayer(load_layer_path, "cargas", "ogr")
capacitor_layer = QgsVectorLayer(capacitor_layer_path, "capacitores", "ogr")
switch_layer = QgsVectorLayer(switch_layer_path, "interruptores", "ogr")
fuse_layer = QgsVectorLayer(fuse_layer_path, "fusibles", "ogr")
recloser_layer = QgsVectorLayer(recloser_layer_path, "reconectadores", "ogr")
relay_layer = QgsVectorLayer(relay_layer_path, "reles", "ogr")
transformer_layer = QgsVectorLayer(transformer_layer_path, "transformadores", "ogr")
et_layer = QgsVectorLayer(et_layer_path, "estacion_transformadora", "ogr")

linecode_layer = QgsVectorLayer(linecode_layer_path, "linecode", "ogr")
linegeometry_layer = QgsVectorLayer(linegeometry_layer_path, "linegeometry", "ogr")
linespacing_layer = QgsVectorLayer(linespacing_layer_path, "linespacing", "ogr")
wiredata_layer = QgsVectorLayer(wiredata_layer_path, "wiredata", "ogr")
cndata_layer = QgsVectorLayer(cndata_layer_path, "cndata", "ogr")
tsdata_layer = QgsVectorLayer(tsdata_layer_path, "tsdata", "ogr")
loadshape_layer = QgsVectorLayer(loadshape_layer_path, "loadshape", "ogr")
settings_layer = QgsVectorLayer(settings_layer_path, "settings", "ogr")
tshape_layer = QgsVectorLayer(tshape_layer_path, "tshape", "ogr")
xycurve_layer = QgsVectorLayer(xycurve_layer_path, "xycurve", "ogr")
tcccurve_layer = QgsVectorLayer(tcccurve_layer_path, "tcccurve", "ogr")
xfmrcode_layer  = QgsVectorLayer(xfmrcode_layer_path, "xfmrcode", "ogr")

# Crear y organizar grupos de capas
#project = QgsProject.instance()
root = QgsProject.instance().layerTreeRoot()

# Crear grupo para los elementos de la red
group_mt = root.addGroup("RED")
group_mt.addLayer(QgsProject.instance().addMapLayer(transformer_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(generator_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(pv_system_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(load_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(capacitor_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(et_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(node_layer, False))
switchgear_group = group_mt.addGroup("aparatos_de_maniobra")
switchgear_group.addLayer(QgsProject.instance().addMapLayer(switch_layer, False))
switchgear_group.addLayer(QgsProject.instance().addMapLayer(fuse_layer, False))
switchgear_group.addLayer(QgsProject.instance().addMapLayer(recloser_layer, False))
switchgear_group.addLayer(QgsProject.instance().addMapLayer(relay_layer, False))
group_mt.addLayer(QgsProject.instance().addMapLayer(line_layer, False))


# Crear grupo para capas LIBRERIAS
lib_group = root.addGroup("LIB")
lib_group.addLayer(QgsProject.instance().addMapLayer(linecode_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(linegeometry_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(linespacing_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(wiredata_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(cndata_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(tsdata_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(loadshape_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(tshape_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(xycurve_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(tcccurve_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(settings_layer, False))
lib_group.addLayer(QgsProject.instance().addMapLayer(xfmrcode_layer, False))

# Aplicar estilos desde archivos .qml
line_layer.loadNamedStyle(project_path + '/estilos/lineas.qml')
node_layer.loadNamedStyle(project_path + '/estilos/nodos.qml')
load_layer.loadNamedStyle(project_path + '/estilos/cargas.qml')
capacitor_layer.loadNamedStyle(project_path + '/estilos/capacitores.qml')
et_layer.loadNamedStyle(project_path + '/estilos/estacion_transformadora.qml')
generator_layer.loadNamedStyle(project_path + '/estilos/generadores.qml')
switch_layer.loadNamedStyle(project_path + '/estilos/interruptores.qml')
pv_system_layer.loadNamedStyle(project_path + '/estilos/sistemas_fotovoltaicos.qml')
transformer_layer.loadNamedStyle(project_path + '/estilos/transformadores.qml')

# Configurar la visibilidad basada en la escala para todas las capas
node_layer.setMinimumScale(10000)
node_layer.setScaleBasedVisibility(True)
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
fuse_layer.setMinimumScale(10000)
fuse_layer.setScaleBasedVisibility(True)
recloser_layer.setMinimumScale(10000)
recloser_layer.setScaleBasedVisibility(True)
relay_layer.setMinimumScale(10000)
relay_layer.setScaleBasedVisibility(True)
pv_system_layer.setMinimumScale(10000)
pv_system_layer.setScaleBasedVisibility(True)
transformer_layer.setMinimumScale(10000)
transformer_layer.setScaleBasedVisibility(True)

# Forzar la actualización de todas las capas
line_layer.triggerRepaint()
node_layer.triggerRepaint()
load_layer.triggerRepaint()
capacitor_layer.triggerRepaint()
et_layer.triggerRepaint()
generator_layer.triggerRepaint()
switch_layer.triggerRepaint()
fuse_layer.triggerRepaint()
recloser_layer.triggerRepaint()
relay_layer.triggerRepaint()
pv_system_layer.triggerRepaint()
transformer_layer.triggerRepaint()








