import pandas as pd
import numpy as np
import statsmodels.api as sm
#import ace_tools as tools

# 1. Carga y limpieza de datos
df = pd.read_csv(r'C:\Users\LENOVO\OneDrive\src\Analisis_de_mercado\datos_prueba_tecnica_filtrados.csv')

# Selecciona solo las columnas necesarias y elimina inf/nans
df_model = df[['precio_venta', 'piso', 'area', 'habitaciones', 'estrato']].copy()
df_model.replace([np.inf, -np.inf], np.nan, inplace=True)
df_model.dropna(subset=['precio_venta', 'piso', 'area', 'habitaciones', 'estrato'], inplace=True)

# 2. Segmentación de variables en df_model
# Área en 4 cuantiles
df_model['area_seg'] = pd.qcut(
    df_model['area'], q=4, labels=['Q1','Q2','Q3','Q4']
)

# Habitaciones en rangos [1-2], [3-5], [6-21]
df_model['hab_seg'] = pd.cut(
    df_model['habitaciones'],
    bins=[1, 3, 6, 22],
    labels=['1-2','3-5','6-21'],
    right=True,
    include_lowest=True
)

# Estrato discretizado 1 a 6, intervalos (0.5,1.5], (1.5,2.5], ..., (5.5,6.5]
bins_estrato = np.arange(0.5, 7, 1)
labels_estrato = [1, 2, 3, 4, 5, 6]
df_model['estrato_seg'] = pd.cut(
    df_model['estrato'],
    bins=bins_estrato,
    labels=labels_estrato,
    right=True,
    include_lowest=True
)

# 3. Regresiones por combinación de segmentos
results = []
#group_cols = ['area_seg', 'hab_seg', 'estrato_seg']
group_cols = ['area_seg', 'estrato_seg']

for keys, group in df_model.groupby(group_cols,observed=True):
    if len(group) < 100:
        continue
    X = sm.add_constant(group['piso'])
    y = group['precio_venta']
    model = sm.OLS(y, X).fit()
    results.append({
        **dict(zip(group_cols, keys)),
        'coef_piso': model.params['piso'],
        'pval_piso': model.pvalues['piso'],
        'r2':        model.rsquared,
        'n_obs':     len(group)
    })

# 4. Resumen de resultados
summary = pd.DataFrame(results)
print(summary)
#tools.display_dataframe_to_user(name="Resultados por segmentos", dataframe=summary)