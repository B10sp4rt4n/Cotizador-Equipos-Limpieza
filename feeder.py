# feeder.py
# Este archivo puede usarse para pruebas locales o carga manual de archivos Excel

from app import CotizadorKarcher, DBKarcher
import pandas as pd

if __name__ == "__main__":
    cot = CotizadorKarcher(descuento_fabricante=0.32)
    db = DBKarcher()
    ruta = "LP Div Prof Hoja 2 Sep25.xlsx"  # Cambia por el nombre de tu archivo en el repo
    df = cot.cargar_archivo(ruta)
    if df is not None:
        db.cargar_catalogo(df, usuario="feeder-local")
        resultado = cot.calcular_precio(
            numero_parte=df["NO. DE PARTE"].iloc[0],
            margen_sobre_costo=0.25
        )
        print(resultado)
        db.guardar_cotizacion(resultado, usuario="feeder-local")
    else:
        print("No se pudo cargar el archivo.")
