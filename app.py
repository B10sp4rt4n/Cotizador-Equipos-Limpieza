import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os
from io import BytesIO

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="Cotizador Karcher - SynAppsSys",
    layout="wide"
)

st.title("🟡 Cotizador Karcher - SynAppsSys (AUP-EXO)")
st.markdown("Sistema de selección jerárquica basado en tu estructura A → B → C.")


# ============================================================
# CARGA DEL EXCEL TAL CUAL (SIN MODIFICAR NOMBRES)
# ============================================================

EXCEL_PATH = "LP Div Prof Hoja 2 Sep25.xlsx"

if not os.path.exists(EXCEL_PATH):
    st.error(f"No se encontró el archivo: {EXCEL_PATH}")
    st.stop()

df = pd.read_excel(EXCEL_PATH)
df.columns = [c.strip() for c in df.columns]  # Limpieza ligera

# Asegurar que las columnas existan
columnas_requeridas = ["CATEGORIA", "CLASE", "MODELO", "NO. DE PARTE", "DESCRIPCIÓN", "PRECIO MXN"]

for col in columnas_requeridas:
    if col not in df.columns:
        st.error(f"Falta la columna requerida en el Excel: {col}")
        st.stop()

# Convertir precios a número si vienen como texto
df["PRECIO"] = (
    df["PRECIO MXN"]
    .astype(str)
    .str.replace("$", "")
    .str.replace(",", "")
    .str.strip()
    .astype(float)
)

# ============================================================
# DROPDOWNS A → B → C
# ============================================================

st.subheader("🔽 Selección jerárquica")

# 1. Dropdown A
categorias = sorted(df["CATEGORIA"].dropna().unique())
sel_A = st.selectbox("Selecciona CATEGORIA", categorias)

dfA = df[df["CATEGORIA"] == sel_A]

# 2. Dropdown B
clases = sorted(dfA["CLASE"].dropna().unique())
sel_B = st.selectbox("Selecciona CLASE", clases)

dfB = dfA[dfA["CLASE"] == sel_B]

# 3. Dropdown C
modelos = sorted(dfB["MODELO"].dropna().unique())
sel_C = st.selectbox("Selecciona MODELO", modelos)

dfC = dfB[dfB["MODELO"] == sel_C]

st.write("### Resultado filtrado:")
st.dataframe(dfC, height=250)

# ============================================================
# CALCULADORA DE PRECIOS (OPCIONAL)
# ============================================================

if not dfC.empty:
    producto = dfC.iloc[0]
    precio_lista = producto["PRECIO"]
    no_parte = producto["NO. DE PARTE"]
    descripcion = producto["DESCRIPCIÓN"]

    st.subheader("🧮 Cálculo de Precio")
    st.write(f"**Producto:** {sel_C}")
    st.write(f"**SKU:** {no_parte}")
    st.write(f"**Descripción:** {descripcion}")
    st.write(f"**Precio lista:** ${precio_lista:,.2f}")

    descuento = st.slider("Descuento (%)", 0, 80, 30)
    precio_final = precio_lista * (1 - descuento / 100)

    st.metric("Precio Final", f"${precio_final:,.2f}", f"-{descuento}%")

    st.success("Cálculo realizado correctamente.")


# ============================================================
# EXPORTADOR
# ============================================================

buffer = BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    dfC.to_excel(writer, index=False, sheet_name='Selección')

st.download_button(
    label="⬇ Descargar selección como Excel",
    data=buffer.getvalue(),
    file_name=f"Seleccion_{sel_C.replace(' ', '_')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

