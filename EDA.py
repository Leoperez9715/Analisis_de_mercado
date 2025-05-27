import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm

path = r"C:\Users\LENOVO\OneDrive\src\Analisis_de_mercado\datos_prueba_técnica- Data.csv"
df = pd.read_csv(path, encoding='utf-8')

#print(df.info())
# ANALISIS DE FILAS DUPLICADAS
# Sort sobre las propiedades para conservar el ultimo actualizado
df = df.sort_values('last_edited', ascending=True)
mask = df.duplicated(subset=(["id","codigo_web","tipo_inmueble","nombre_publicacion","last_edited"]))
print(f"Cantidad de propiedades duplicadas: {mask.sum()}")
# Función de df para eliminar las filas duplicadas de acuerdo a columnas especificas. 
df = df.drop_duplicates(subset=["id","codigo_web","tipo_inmueble","nombre_publicacion","last_edited"])#, keep='last')
#print(df["id"].count())

# Analisis preliminar para determinar cuales columnas debo normalizar
ciudad = set(df["ciudad"]) # {'Bogota DC', 'bogota', 'bogotá dc.', 'Bogotá', 'bogotá D.C', 'bogota d.c.', 'BOGOTÁ'}
portal_inm = set(df["portal_inmobiliario"]) # {'Fincaraiz', 'Habi', 'Metro Cuadrado', 'CienCuadras', 'MercadoLibre'}
tipo_inmueble = set(df["tipo_inmueble"]) #{'APARTAMENTO', 'Apartamento', 'Casa'}
tipo_negocio = set(df["tipo_negocio"]) # {'FOR_SALE'}
departamento = set(df["departamento"]) #{'Cundinamarca', 'CUNDINAMARCA'}
subzona = sorted(set(df["subzona"]))
# ['Antonio Nariño', 'Barrios Unidos', 'Bosa', 'Chapinero', 'Ciudad Bolivar', 'Engativá', 'Fontibón', 'Kennedy', 'La Candelaria', 
# 'Los Mártires', 'Puente Aranda', 'Rafael Uribe', 'San Cristóbal', 'Santa Fé', 'Suba', 'Sumapaz', 
# 'Teusaquillo', 'Tunjuelito', 'Usaquén', 'Usme']

print(f"{ciudad}\n{portal_inm}\n{tipo_inmueble}\n{tipo_negocio}\n{departamento}\n{subzona}")
# Solo las columnas de ciudad, tipo_inmueble, departamento deben ser normalizadas en texto. 

# LIMPIEZA DE DATOS - normalización formato de texto
# Ciudad
df['ciudad'] = df['ciudad'].str.upper().str.strip()
patron_ciudad = r"^(?=.*[AÁÉÍÓÚÜÑ]|\bD\.?C\.?\b).*$"
df['ciudad'] = df['ciudad'].str.replace(
    patron_ciudad,
    'BOGOTA',
    regex=True
)
df["tipo_inmueble"] = df["tipo_inmueble"].str.upper()
df["departamento"] = df["departamento"].str.upper()

#** check normalizado 
ciudad = set(df["ciudad"]) # {'BOGOTA'}
tipo_inmueble = set(df["tipo_inmueble"]) #{'CASA', 'APARTAMENTO'}
departamento = set(df["departamento"]) #{'CUNDINAMARCA'}
#print(f"{ciudad}\n{tipo_inmueble}\n{departamento}")


# LIMPIEZA DE DATOS - cambio de formato, fechas
dates = ["fecha_insercion_third_party",'fecha_publicacion', 'last_edited']
df[dates] = df[dates].apply(lambda col: pd.to_datetime(col, format='%Y-%m-%d', errors='coerce'))
df['fecha_insercion_interna'] = pd.to_datetime(df['fecha_insercion_interna'],format='%Y-%m-%d %H:%M:%S.%f',errors='coerce')
#print(df.info())
#print(df[["id",'precio_venta','precio_usd','precio_admon','fecha_insercion_third_party','fecha_publicacion','fecha_insercion_interna', 'last_edited']].head(2))

# LIMPIEZA DE DATOS - Eliminar valores sin sentido
# En primer Lugar, se realiza un analisis sobre los datos con .describe().T para analizar que datos tienen y cuales no tienen sentido fisico sobre las columnas numericas
print(df.shape[0]) # Tamaño de la matriz antes de la limpieza # filas 
col_numericas = ['latitud', 'longitud','area', 'area_total','habitaciones', 'banios', 'parqueaderos', 'precio_venta', 'precio_usd',
       'estrato', 'precio_admon','precio_admon_incluido', 'anhio_construccion', 'pisos_edificio', 'piso', 'ascensor']
print(df[col_numericas].describe().T)
    #** Latitud y longitud estan fuera de los rangos para la ciudad de bogota
    #** Los precios de venta tienen valores muy pequeños - pero pueden ser no irreales
    #** El año de construcción esta mal listado el minimo no puede ser 2
    #** Los estratos en bogotá van de 1 a 6 
    #** El edificio mas alto en bogota tiene 67 pisos y es el bacata
# Se realiza el filtrado de estos elementos teniendo en cuenta: 
latitud_bogota = [4.4,4.86] #lb, ub
longitud_bogota = [-76.63542,-73.97] #lb,ub
anhio_edificacion = [1580,2025] #año donde se fundo el Palacio de San Carlos
estratos = [1,6] #lb, ub
pisos_max = 67.0

mask = (
    (df['latitud'] >= latitud_bogota[0]) & (df['latitud'] <= latitud_bogota[1]) &
    (df['longitud'] >= longitud_bogota[0]) & (df['longitud'] <= longitud_bogota[1]) &
    (df['anhio_construccion'] >= anhio_edificacion[0]) & (df['anhio_construccion'] <= anhio_edificacion[1]) &
    (df['estrato'] >= estratos[0]) & (df['estrato'] <= estratos[1]) &
    (df["piso"]<= pisos_max)
)
# Aplicar la máscara al DataFrame
df_filtrado = df[mask]
print(df_filtrado.shape)
print(f"Elementos filtrados: {df.shape[0]-df_filtrado.shape[0]}")
print(df_filtrado[col_numericas].describe().T)


# LIMPIEZA DE DATOS - Eliminar outliers
# Ahora, con el df filtrado de valores "irreales" se procede a eliminar los outliers considerando las siguientes columnas: 
col_estadisticos = ["precio_venta", "area",'precio_admon']
# Revision general

#print(datos_estadisticos)
#Vizualización preliminar
#df_filtrado[col_numericas].hist(bins=50, figsize=(16,12))
#plt.show()
#df[col_estadisticos].plot(kind="box",figsize=(16,12))
#plt.xticks(rotation=90)
#plt.show()
print("done")

# Ajuste outliers 
def eliminar_atipicos(df,columnas=col_estadisticos):
    if columnas is None:
        columnas = df.select_dtypes(include=["number"]).columns
    df_sin_atipicos = df.copy()

    for column in columnas:
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1

        lower_b = Q1 - 1.5*IQR
        upper_b = Q3 + 1.5*IQR
        df_sin_atipicos = df_sin_atipicos[(df_sin_atipicos[column]>= lower_b) & (df_sin_atipicos[column]<= upper_b)]

    return df_sin_atipicos
print(col_estadisticos[0:1])
print(col_estadisticos[1:3])
for i in range(3):
    new_df =eliminar_atipicos(df_filtrado,columnas=col_estadisticos[1:3])
print(new_df.shape[0])
for i in range(3):
    new_df =eliminar_atipicos(new_df,columnas=col_estadisticos[0:1])
print(new_df.shape[0])

#new_df.plot(kind="box",figsize=(16,12))
#plt.xticks(rotation=90)
#plt.show()
#new_df.hist(bins=50, figsize=(10,10))
#plt.show()
new_df.to_csv("datos_prueba_tecnica_filtrados.csv", index=False)


# preparacion de datos
df_model = new_df[['precio_venta', 'piso']].copy()
df_model.replace([np.inf, -np.inf], np.nan, inplace=True)
df_model.dropna(subset=['precio_venta','piso'], inplace=True)

df_model['log_precio'] = np.log(df_model['precio_venta'])
df_model['log_piso'] = np.log(df_model['piso'])

df_model.hist(bins=50, figsize=(10,10))
plt.show()

## ANALISIS DE REGRESION 
# x = piso, y = precio_venta
X = sm.add_constant(df_model["log_piso"])
y = df_model['log_precio']


model = sm.OLS(y, X).fit()
print(model.summary())