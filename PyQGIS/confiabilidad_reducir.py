import pandas as pd
import numpy as np
import sys,os,shutil
#print(sys.getrecursionlimit())


################################################################# FUNCION RECURSIVA #########################################################

def itera(fila,lista_eliminar,df,iteracion_nro,limite_iteraciones):

    iteracion_nro = iteracion_nro + 1 
    df_2 = df.loc[(df['id'] != fila['id']) 
                  #& (df['linecode'] == row1['linecode']) 
                  & (df['bus2'] != 'nan') 
                  & (df['bus1'] != 'nan')
                  & (( (df['bus1'] == fila['bus2']) & (df['bus2'] != fila['bus1']) ) 
                     | ( (df['bus2'] == fila['bus2']) & (df['bus1'] != fila['bus1']))
                    ) ]
    
    if len(df_2) == 1 and iteracion_nro < limite_iteraciones:
        fila2 = df_2.iloc[0]
        if (fila2['tipo'] == 'L') & ( (fila2['linecode'] == fila['linecode'] ) | (fila2['wires'] == row1['wires'])    ) & (fila2['id'] not in lista_eliminar):
            lista_eliminar.append(fila['id'])        
            #print(fila2['id'] )
            retorno = itera(fila2,lista_eliminar,df,iteracion_nro,limite_iteraciones)        
            if(len(retorno['retorno']) > 1):
                if (fila['bus1'] == retorno['retorno'][1]) | (fila['bus2'] == retorno['retorno'][1]):
                    return {"eliminar":lista_eliminar,"retorno":[retorno['retorno'][0]],"retorno_bis":[retorno['retorno_bis'][0]]  }
                else:
                    return {"eliminar":lista_eliminar,"retorno":[retorno['retorno'][1]],"retorno_bis":[retorno['retorno_bis'][1]]  }
            else:
                return {"eliminar":lista_eliminar,"retorno":retorno['retorno'],"retorno_bis":retorno['retorno_bis']}
        else:
            lista_eliminar.append(fila['id'])
            #print("ultimo: " + fila['ref1'])
            return {"eliminar":lista_eliminar,"retorno":[fila['bus1'],fila['bus2']] ,"retorno_bis":[fila['bus1_bis'],fila['bus2_bis']] }
    else:
        lista_eliminar.append(fila['id'])
        #print("ultimo: " + fila['ref1'])
        return {"eliminar":lista_eliminar,"retorno":[fila['bus1'],fila['bus2']] ,"retorno_bis":[fila['bus1_bis'],fila['bus2_bis']]}

################################################################# FUNCION RECURSIVA #########################################################

if __name__ == '__main__':
    """
        @argv1  archivo de entrada (sin reducir)
        @argv2  nombre archivo de salida (sin reducir) (no colocar extension)
                    Exporta dos archivos: uno xlsx para openDSS (mismas hojas y campos pero con menos lineas)
                                      otro csv para confiabilidad (una sola hoja con menos campos y concatenando transformadores, fuente,switch,lineas y loads)
    """
    argv = sys.argv
    argc = len(sys.argv)

    # Verifico los parametros de entrada
    existe_entrada = False
    if len(sys.argv) >= 2:
        existe_segundo_argv = True
        if os.path.exists(argv[1]):
            existe_entrada = True
        else:
            print("Archivo de Entrada Inexistente")
    else:
        print("Faltan Parametros de Entrada: Archivo_de_entrada Archivo_de_Salida")

    if existe_entrada and existe_segundo_argv:
        ############################################################# CARGA DE DATOS ##############################################################
        file = argv[1]
        salida = argv[2]
        salidaxls = salida+".xlsx"
        #replico el archivo de entrada, luego modifico la hoja Lineas
        shutil.copy(file, salidaxls)

        vsource = pd.read_excel(open(file, 'rb'),
              sheet_name='Vsource') 

        vsource['bus1'] = vsource['bus1'].str.split('.').str[0]
        vsource['bus1'] = vsource['bus1'].str.strip()
        vsource['Id_Vsource'] = vsource['Id_Vsource'].str.strip()
        vsource = vsource.rename(columns={'Id_Vsource':'id'})
        vsource.insert(0, 'tipo', 'CD1')
        vsource_red = vsource.loc[:,['id','bus1','tipo']]
        vsource = vsource.loc[:,['id','bus1','tipo']]

        transformer = pd.read_excel(open(file, 'rb'),
                    sheet_name='Transformer')
        transformer['Id_Transformer'] = transformer['Id_Transformer'].str.strip()
        transformer = transformer.rename(columns={"Id_Transformer":"id"})
        transformer.insert(0, 'tipo', 'TRANSFORMER')
        transformer
        transformer.insert(1, 'bus1', transformer['Buses'].str.split(',').str[0])
        transformer.insert(2, 'bus2', transformer['Buses'].str.split(',').str[1])
        transformer['bus1'] = transformer['bus1'].str.replace('[','',regex=True)
        transformer['bus2'] = transformer['bus2'].str.replace(']','',regex=True)
        transformer['bus1'] = transformer['bus1'].str.split('.').str[0]
        transformer['bus2'] = transformer['bus2'].str.split('.').str[0]
        transformer['bus1'] = transformer['bus1'].str.strip()
        transformer['bus2'] = transformer['bus2'].str.strip()
        transformer_red = transformer.loc[:,['id','bus1','bus2','tipo']]
        transformer = transformer.loc[:,['id','bus1','bus2','tipo']]

        line = pd.read_excel(open(file, 'rb'),
                    sheet_name='Line')
        line['Id_Line'] = line['Id_Line'].str.strip()
        line = line.rename(columns={"Id_Line":"id"})
        line['bus1_bis'] = line['bus1']
        line['bus2_bis'] = line['bus2']       
        line['bus1'] = line['bus1'].str.split('.').str[0]
        line['bus2'] = line['bus2'].str.split('.').str[0]
        line['bus1'] = line['bus1'].str.strip()
        line['bus2'] = line['bus2'].str.strip()
        line.insert(0, 'tipo', 'L')
        line

        switch = pd.read_excel(open(file ,'rb'),
                    sheet_name='Switch')
        switch['Id_Switch'] = switch['Id_Switch'].str.strip()
        switch = switch.rename(columns={"Id_Switch":"id"})
        switch['bus1'] = switch['bus1'].str.split('.').str[0]
        switch['bus2'] = switch['bus2'].str.split('.').str[0]
        switch['bus1'] = switch['bus1'].str.strip()
        switch['bus2'] = switch['bus2'].str.strip()
        #switch['length'] = 0.001
        #switch['units'] = "km"
        switch.insert(0, 'tipo', 'IC')
        switch_red = switch.loc[:,['id','bus1','bus2','tipo']]
        switch = switch.loc[:,['id','bus1','bus2','length','units','tipo']]
                            
                            
        load = pd.read_excel(open(file, 'rb'),
                            sheet_name='Load')
        load = load.rename(columns={"Id_Load":"id"})
        load['bus1'] = load['bus1'].str.split('.').str[0]
        load['bus1'] = load['bus1'].str.strip()
        #load = load.groupby(['bus1'])[['Kw','kvar','NumCust']].apply(sum).reset_index()
        load.insert(3, 'tipo', 'LOAD')
        #load['id'] = "LOAD"+load['bus1'].astype(str)
        #print(load.head())

        load_red = load.loc[:,['id','bus1','tipo']]
        load = load.loc[:,['id','bus1','kvar','Kw','NumCust','tipo']]

        #UNIFICO LOS DATAFRAMES
        df = pd.concat([vsource_red,transformer_red,line,switch_red,load_red])


        ############################################################# CARGA DE DATOS ##############################################################

        ########################################################### ARREGLO DE VARIABLES ###########################################################
        #si el switch empieza con Fus_ es un fusible
        switch.loc[switch['id'].str.contains("Fus_"),'tipo'] = 'FC'
        #switch

        df['bus2'] = df['bus2'].astype(str)
        df['bus1'] = df['bus1'].astype(str)


        indices = df['id'].tolist()
        df['indice']  = df['id'].tolist()
        df['indice'] = df['indice'].astype(str)
        df.set_index('indice', inplace=True)

        ########################################################### ARREGLO DE VARIABLES ###########################################################

        ########################################################### HAGO LA REDUCCION ##############################################################
        eliminados = []
        limite_iteraciones = 900

        #Por cada uno de los elementos
        for i, row1 in df.iterrows():
            iteracion_nro = 0
            #Si no esta en la lista de eliminar
            if row1['id'] not in eliminados:
                #Si el elemento es una linea
                if row1['tipo'] == 'L':
                    #Buscar elementos en base al segundo bus
                        # que no sea el mismo elemento
                        # no intentar vincular 'nan'
                        # que el bus2 concuerde con el 1 o el 2, pero que el bus1 no concuerde con el otro (o sea un bucle) {[( quizas meter aqui la comprovacion 'nan')]}                        
                    df_2 = df.loc[(df['id'] != row1['id']) 
                                & (df['bus2'] != 'nan') 
                                & (df['bus1'] != 'nan')
                                & (( (df['bus1'] == row1['bus2']) & (df['bus2'] != row1['bus1']) ) 
                                    | ( (df['bus2'] == row1['bus2']) & (df['bus1'] != row1['bus1']))
                                    ) ]

                    # Si no hay bifurcacion
                    if len(df_2) == 1:
                        fila2 = df_2.iloc[0]
                        #Si es una Linea y tiene el mismo tipo de material
                        if (fila2['tipo'] == 'L') & (  (fila2['linecode'] == row1['linecode'] )  | (fila2['wires'] == row1['wires'])  ):
                            #Empiezo a recorrer recursivamente
                            retorno = itera(row1,[],df,iteracion_nro,limite_iteraciones)
                            # De mi listado quito el primer nodo
                            retorno['eliminar'].remove(row1['id'])
                            #El Resto lo agrego a mi lista para eliminar
                            eliminados = [*eliminados,*retorno['eliminar']]

                            # Remplazo el bus2 de la linea inicial con el bus de la ultima linea a reducir
                            df.loc[row1['id'],'bus2'] = retorno["retorno"][0]
                            df.loc[row1['id'],'bus2_bis'] = retorno["retorno_bis"][0]
                            sumakm = 0
                            # Sumo a la linea inicial los km de las lineas reducida
                            for eliminar in retorno["eliminar"]:
                                sumakm = sumakm +  df.loc[eliminar,'length']
                            df.loc[row1['id'],'length'] = df.loc[row1['id'],'length'] + sumakm

        # Una vez que recorro todo el df, elimino los nodos reducidos
        for eliminar in eliminados:
            df = df.loc[(df['id'] != eliminar)]
   
        ################################################################## HAGO LA REDUCCION #######################################################

        ################################################################## EXPORTO LA SALIDA PARA OPENDSS ################################################
        # Del dataframe concatenado y reducido extraigo solo las lineas
        lineas_guardar = df.loc[df['tipo']=='L']
        lineas_guardar_dss = df.loc[df['tipo']=='L']

        #quito columnas extras y vuelvo a renombrar el id
        lineas_guardar_dss = lineas_guardar_dss.drop(columns=['tipo'])
        lineas_guardar_dss = lineas_guardar_dss.rename(columns={"id":"Id_Line"})

        
        lineas_guardar_dss = lineas_guardar_dss.drop(columns=['bus1','bus2'])
        lineas_guardar_dss = lineas_guardar_dss.rename(columns={"bus1_bis":"bus1"})
        lineas_guardar_dss = lineas_guardar_dss.rename(columns={"bus2_bis":"bus2"})

        cols = list(lineas_guardar_dss.columns.values)
        cols.remove("bus1")
        cols.remove("bus2")
        cols.insert(2, "bus1")
        cols.insert(3, "bus2")
        lineas_guardar_dss = lineas_guardar_dss[cols]

        



        #Remuevo la hoja linea del xlsx replicado
        #with pd.ExcelWriter(salidaxls, engine="openpyxl",mode='a') as writer:
        with pd.ExcelWriter(salidaxls, engine="openpyxl",mode='a') as writer:
            workBook = writer.book
            workBook.remove(workBook['Line'])
            writer.save()

        #Agrego denuevo la hoja linea con los nuevos datos reducidos    
        #with pd.ExcelWriter(salidaxls, engine="openpyxl",mode='a') as writer:
        with pd.ExcelWriter(salidaxls, engine="openpyxl",mode='a') as writer:
            lineas_guardar_dss.to_excel(writer, sheet_name='Line',index=False) 


        ################################################################## EXPORTO LA SALIDA PARA OPENDSS  ################################################

        ################################################################## EXPORTO LA SALIDA PARA CONFIABILIDAD  ################################################
        # Agrego Tipo del Campo y renombro el campo id
        #lineas_guardar.insert(0, 'tipo', 'L')
        #lineas_guardar = lineas_guardar.rename(columns={"Id_Line":"id"})

        
        lineas_guardar = lineas_guardar.loc[:,['id','bus1','bus2','tipo','length','units','linecode','wires','normamps']]

        # Concateno todos los elementos en un dataframe
        df_confiabilidad = pd.concat([vsource,transformer,lineas_guardar,switch,load])

        # Convierto a string los bus por las dudas
        df_confiabilidad['bus2'] = df_confiabilidad['bus2'].astype(str)
        df_confiabilidad['bus1'] = df_confiabilidad['bus1'].astype(str)

        # Creo un indice con el nombre del campo
        indices = df_confiabilidad['id'].tolist()
        df_confiabilidad['indice']  = df_confiabilidad['id'].tolist()
        df_confiabilidad['indice'] = df_confiabilidad['indice'].astype(str)
        df_confiabilidad['indice'] = df_confiabilidad['indice'].str.strip()
        df_confiabilidad.set_index('indice', inplace=True)
        df_confiabilidad  

        #Creo el excel para usar en confiabilidad
        salidacsv = salida+"para_matriz.csv"
        df_confiabilidad.to_csv(salidacsv, sep=';',decimal=",") 

        ################################################################## EXPORTO LA SALIDA PARA CONFIABILIDAD  ################################################     