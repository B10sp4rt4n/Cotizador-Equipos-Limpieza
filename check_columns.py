import pandas as pd

df = pd.read_excel("LP Div Prof Hoja 2 Sep25.xlsx")
df = df.rename(columns=lambda x: str(x).strip().replace('\n', ' ').upper())

print("Columnas en el archivo Excel:")
for i, col in enumerate(df.columns, 1):
    print(f"{i}. '{col}'")
    
print(f"\nTotal de columnas: {len(df.columns)}")
print(f"Total de filas: {len(df)}")

# Verificar valores únicos en columnas clave
if "TIPO" in df.columns:
    print(f"\nValores únicos en TIPO: {df['TIPO'].dropna().unique().tolist()}")
if "CLASIFICACION" in df.columns:
    print(f"Valores únicos en CLASIFICACION: {df['CLASIFICACION'].dropna().unique().tolist()}")
if "MODELO" in df.columns:
    print(f"Valores únicos en MODELO: {df['MODELO'].dropna().unique().tolist()}")
