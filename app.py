import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

# ============================================================
#  MODULO STREAMLIT - COTIZADOR KARCHER
# ============================================================

st.set_page_config(
    page_title="Cotizador Karcher - SynAppsSys",
    layout="wide"
)

# ============================================================
#  Clase de cálculo (mismo motor que el prototipo)
# ============================================================

############################################################
#   BASE SQLITE
############################################################

class DBKarcher:
    def __init__(self, db_path="cotizador_karcher.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        # Catálogo de productos
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_parte TEXT UNIQUE,
                modelo TEXT,
                descripcion TEXT,
                precio_lista REAL
            )
        """)

        # Cotizaciones generadas
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cotizaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_parte TEXT,
                precio_lista REAL,
                costo_base REAL,
                precio_final REAL,
                margen_real REAL,
                descuento_visible REAL,
                usuario TEXT,
                timestamp TEXT
            )
        """)

        # Auditoría estructural
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                accion TEXT,
                detalle TEXT,
                usuario TEXT,
                timestamp TEXT
            )
        """)

        self.conn.commit()

    # ---------------------------------------------------------
    #   CARGA DE CATÁLOGO
    # ---------------------------------------------------------
    def cargar_catalogo(self, df, usuario="system"):
        for _, row in df.iterrows():
            try:
                self.cursor.execute("""
                    INSERT OR REPLACE INTO productos (numero_parte, modelo, descripcion, precio_lista)
                    VALUES (?, ?, ?, ?)
                """, (
                    str(row["NO. DE PARTE"]).strip(),
                    str(row.get("MODELO", "")),
                    str(row.get("DESCRIPCIÓN", "")),
                    float(row["PRECIO_LISTA"])
                ))
            except Exception as e:
                print("Error guardando:", e)

        self.conn.commit()
        self.registrar_auditoria("CARGA_CATALOGO", f"{len(df)} productos cargados", usuario)

    # ---------------------------------------------------------
    #   ALMACENAR COTIZACIÓN
    # ---------------------------------------------------------
    def guardar_cotizacion(self, datos, usuario="system"):
        self.cursor.execute("""
            INSERT INTO cotizaciones (numero_parte, precio_lista, costo_base, precio_final,
                                      margen_real, descuento_visible, usuario, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos["NO_PARTE"],
            datos["PRECIO_LISTA"],
            datos["COSTO_BASE"],
            datos["PRECIO_FINAL"],
            datos["MARGEN_REAL_COSTO"],
            datos["DESCUENTO_VISIBLE"],
            usuario,
            datetime.now().isoformat()
        ))
        self.conn.commit()

    def registrar_auditoria(self, accion, detalle, usuario="system"):
        self.cursor.execute("""
            INSERT INTO auditoria (accion, detalle, usuario, timestamp)
            VALUES (?, ?, ?, ?)
        """, (accion, detalle, usuario, datetime.now().isoformat()))
        self.conn.commit()
class CotizadorKarcher:
    def __init__(self, descuento_fabricante=0.30):
        self.descuento_fabricante = descuento_fabricante
        self.df = None

    def cargar_archivo(self, archivo):
        try:
            df = pd.read_excel(archivo)
            df = df.rename(columns=lambda x: str(x).strip().upper())
            df = df.rename(columns={"PRECIO MXN": "PRECIO_LISTA"})
            self.df = df
            return df
        except Exception as e:
            st.error(f"Error al cargar archivo: {e}")
            return None

    def calcular_precio(self, numero_parte, margen_sobre_costo=None, precio_objetivo=None):
        df = self.df
        producto = df[df["NO. DE PARTE"] == numero_parte]

        if producto.empty:
            return {"error": "Producto no encontrado"}

        precio_lista = float(producto["PRECIO_LISTA"].values[0])
        costo_base = precio_lista * (1 - self.descuento_fabricante)

        # Cálculo por margen
        if margen_sobre_costo is not None:
            precio_final = costo_base / (1 - margen_sobre_costo)

        # Cálculo por precio objetivo
        elif precio_objetivo is not None:
            precio_final = precio_objetivo

        else:
            return {"error": "Debes especificar margen_sobre_costo o precio_objetivo"}

        margen_real_sobre_costo = (precio_final - costo_base) / costo_base
        descuento_visible = 1 - (precio_final / precio_lista)

        alerta = None
        if precio_final < costo_base:
            alerta = "PRECIO POR DEBAJO DEL COSTO (NO PERMITIDO)"

        return {
            "NO_PARTE": numero_parte,
            "PRECIO_LISTA": precio_lista,
            "COSTO_BASE": round(costo_base, 2),
            "PRECIO_FINAL": round(precio_final, 2),
            "MARGEN_REAL_COSTO": round(margen_real_sobre_costo * 100, 2),
            "DESCUENTO_VISIBLE": round(descuento_visible * 100, 2),
            "ALERTA": alerta
        }


# ============================================================
#  INTERFAZ STREAMLIT
# ============================================================

st.title("🟡 Cotizador Karcher - SynAppsSys (Prototipo AUP-EXO)")
st.markdown("Carga la lista de precios de Karcher y genera cotizaciones con reglas inteligentes.")


# Instancia de la base de datos
db = DBKarcher()
cotizador = CotizadorKarcher()

# -------------------------
# Subir archivo
# -------------------------

# Subir archivo
archivo = st.file_uploader("Sube la lista de precios", type=["xlsx"])

# Intentar cargar automáticamente el archivo si existe en el repositorio
default_xlsx = "LP Div Prof Hoja 2 Sep25.xlsx"
df = None
if os.path.exists(default_xlsx):
    df = cotizador.cargar_archivo(default_xlsx)
    if df is not None:
        db.cargar_catalogo(df, usuario="auto-repo")

# Si el usuario sube un archivo, se sobreescribe el DataFrame
if archivo:
    df = cotizador.cargar_archivo(archivo)
    if df is not None:
        st.success("Archivo cargado correctamente.")
        st.dataframe(df, height=300)
        db.cargar_catalogo(df, usuario="streamlit")

# Buscador dinámico de inicio si hay lista cargada
if df is not None:
    st.markdown("### 🔍 Buscar y cotizar producto")
    busqueda = st.text_input("Buscar por No. de Parte, Modelo o Descripción")

    if busqueda:
        filtro = df[
            df["NO. DE PARTE"].astype(str).str.contains(busqueda, case=False, na=False) |
            df.get("MODELO", pd.Series(["" for _ in range(len(df))])).astype(str).str.contains(busqueda, case=False, na=False) |
            df.get("DESCRIPCIÓN", pd.Series(["" for _ in range(len(df))])).astype(str).str.contains(busqueda, case=False, na=False)
        ]
        st.dataframe(filtro, height=200)
        lista_partes = sorted(filtro["NO. DE PARTE"].dropna().unique())
    else:
        lista_partes = sorted(df["NO. DE PARTE"].dropna().unique())

    if lista_partes:
        numero_parte = st.selectbox("Selecciona No. de Parte", lista_partes)

        descuento_fab = st.slider("Descuento del fabricante (%)", 0, 60, 30)
        cotizador.descuento_fabricante = descuento_fab / 100

        modo = st.radio("Método de cálculo:", ["Margen sobre costo", "Precio objetivo"])

        margen = None
        precio_objetivo = None

        if modo == "Margen sobre costo":
            margen = st.slider("Margen deseado (%)", 5, 80, 25) / 100
        else:
            precio_objetivo = st.number_input("Precio objetivo (MXN)", min_value=0.0, step=1.0)

        if st.button("Calcular Precio Final"):
            resultado = cotizador.calcular_precio(
                numero_parte=numero_parte,
                margen_sobre_costo=margen,
                precio_objetivo=precio_objetivo
            )

            st.subheader("Resultado de Cálculo")

            if "error" in resultado:
                st.error(resultado["error"])
            else:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Precio Lista", f"${resultado['PRECIO_LISTA']:,}")
                col2.metric("Costo Base", f"${resultado['COSTO_BASE']:,}")
                col3.metric("Precio Final", f"${resultado['PRECIO_FINAL']:,}")
                col4.metric("Margen Real (%)", f"{resultado['MARGEN_REAL_COSTO']}%")

                st.write(f"**Descuento visible sobre lista:** {resultado['DESCUENTO_VISIBLE']}%")

                if resultado.get("ALERTA"):
                    st.error(resultado["ALERTA"])
                else:
                    st.success("Precio válido y dentro de rango comercial.")
                db.guardar_cotizacion(resultado, usuario="streamlit")

