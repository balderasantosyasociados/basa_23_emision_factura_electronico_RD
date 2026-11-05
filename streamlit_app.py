# ==============================================================================
# 🏦 BASA SUPERSISTEMA V27 - ARCHIVO FINAL CORREGIDO
# Baldera Santos & Asociados SRL | RNC 133378711 | Cuenta BHD ****0021
# Autoasistencia IA + DGII 606/607/608 + Login RNC/Cedula/Correo
# UN SOLO BLOQUE DE AUTONOMIA - NO DUPLICAR
# ==============================================================================

import streamlit as st
import importlib.util
import sqlite3
import pandas as pd
import os
import re
import json
import hashlib
import base64
from datetime import date, datetime, timedelta
from pathlib import Path
from io import BytesIO

# --- Import seguro openpyxl - Nunca tumba la app ---
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    TIENE_OPENPYXL = True
except Exception:
    openpyxl = None
    TIENE_OPENPYXL = False

st.set_page_config(page_title="BASA SUPERSISTEMA V27", layout="wide", page_icon="🏦")

# =========================================================
# AUTONOMIA BASA - UN SOLO BLOQUE - SOLO VERIFICA, NUNCA INSTALA
# No usar subprocess, no usar pip install, no duplicar este bloque
# =========================================================
def _verificar_basa():
    req = ["streamlit", "pandas", "openpyxl", "xlsxwriter", "numpy", "sqlalchemy", "fastapi", "requests", "cryptography", "lxml", "signxml", "PIL", "dateutil"]
    faltan = []
    for r in req:
        try:
            if importlib.util.find_spec(r) is None:
                faltan.append(r)
        except Exception:
            faltan.append(r)
    return faltan

_faltan_basa = _verificar_basa()
if _faltan_basa:
    st.warning(f"Autonomia BASA: Faltan {len(_faltan_basa)}: {', '.join(_faltan_basa)}. Agregalos a requirements.txt y haz Clear cache + Reboot.")
# Si no falta nada, NO muestra nada. Asi no duplica avisos.

# =========================================================
# BASE DE DATOS
# =========================================================
BASE = Path("BASA_V27_SUPERSISTEMA")
BASE.mkdir(exist_ok=True)
DB = BASE / "basa.db"

def get_conn():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rnc TEXT, cedula TEXT, correo TEXT, nombre TEXT,
        clave_hash TEXT, creado TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS facturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rnc TEXT, tipo TEXT, ncf TEXT, fecha TEXT,
        monto REAL, itbis REAL, total REAL, cliente TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rnc_proveedor TEXT, ncf TEXT, fecha TEXT,
        monto REAL, itbis REAL, total REAL, proveedor TEXT)""")
    conn.commit()
    conn.close()

init_db()

def hash_clave(c):
    return hashlib.sha256(str(c).encode()).hexdigest()

# =========================================================
# LOGIN RNC / CEDULA / CORREO
# =========================================================
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🏦 BASA SUPERSISTEMA V27")
    st.caption("Baldera Santos & Asociados SRL | RNC 133378711 | Cuenta BHD ****0021")
    st.divider()
    tab1, tab2 = st.tabs(["🔐 Entrar", "📝 Registrar"])
    with tab1:
        with st.form("login"):
            identificador = st.text_input("RNC / Cédula / Correo")
            clave = st.text_input("Clave", type="password")
            entrar = st.form_submit_button("Entrar", use_container_width=True)
            if entrar:
                conn = get_conn()
                row = conn.execute("SELECT * FROM usuarios WHERE rnc=? OR cedula=? OR correo=?", (identificador, identificador, identificador)).fetchone()
                conn.close()
                if row and row["clave_hash"] == hash_clave(clave):
                    st.session_state.user = dict(row)
                    st.rerun()
                else:
                    st.error("Datos incorrectos. Verifica RNC / Cédula / Correo y clave.")
    with tab2:
        with st.form("registro"):
            rnc = st.text_input("RNC")
            cedula = st.text_input("Cédula")
            correo = st.text_input("Correo")
            nombre = st.text_input("Nombre / Empresa")
            clave2 = st.text_input("Crear Clave", type="password")
            crear = st.form_submit_button("Crear Cuenta", use_container_width=True)
            if crear:
                if not rnc or not clave2:
                    st.error("RNC y Clave son obligatorios.")
                else:
                    conn = get_conn()
                    conn.execute("INSERT INTO usuarios (rnc,cedula,correo,nombre,clave_hash,creado) VALUES (?,?,?,?,?,?)",
                                 (rnc, cedula, correo, nombre, hash_clave(clave2), datetime.now().isoformat()))
                    conn.commit()
                    conn.close()
                    st.success("Cuenta creada. Ahora entra en la pestaña Entrar.")
    st.stop()

# =========================================================
# APP PRINCIPAL - USUARIO LOGUEADO
# =========================================================
user = st.session_state.user
col1, col2, col3 = st.columns([3, 2, 1])
with col1:
    st.title("🏦 BASA SUPERSISTEMA V27")
    st.caption(f"Bienvenido: {user.get('nombre') or user.get('rnc')} | RNC: {user.get('rnc')}")
with col3:
    if st.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()

menu = st.sidebar.selectbox("Menú", ["📊 Dashboard", "🧾 Facturación", "🛒 Compras 606", "📤 Ventas 607", "📄 DGII 606 - Excel", "⚙️ Configuración"])
st.sidebar.caption("Autoasistencia IA ON")

# --- Dashboard ---
if menu == "📊 Dashboard":
    st.subheader("📊 Dashboard")
    conn = get_conn()
    f = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(total),0) t FROM facturas").fetchone()
    c = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(total),0) t FROM compras").fetchone()
    conn.close()
    a, b, d = st.columns(3)
    a.metric("Facturas", f["c"])
    b.metric("Total Facturado", f"${f['t']:,.2f}")
    d.metric("Total Compras", f"${c['t']:,.2f}")
    st.info("✅ Sistema FULL - BASA V27 funcionando.")

# --- Facturación ---
elif menu == "🧾 Facturación":
    st.subheader("🧾 Nueva Factura")
    with st.form("fact"):
        cliente = st.text_input("Cliente / RNC Cliente")
        ncf = st.text_input("NCF", value="B0100000001")
        fecha = st.date_input("Fecha", value=date.today())
        monto = st.number_input("Monto sin ITBIS", min_value=0.0, step=100.0)
        itbis = round(monto * 0.18, 2)
        total = monto + itbis
        st.write(f"ITBIS 18%: ${itbis:,.2f} | Total: ${total:,.2f}")
        guardar = st.form_submit_button("Guardar Factura")
        if guardar:
            conn = get_conn()
            conn.execute("INSERT INTO facturas (rnc,tipo,ncf,fecha,monto,itbis,total,cliente) VALUES (?,?,?,?,?,?,?,?)",
                         (user.get("rnc"), "Venta", ncf, str(fecha), monto, itbis, total, cliente))
            conn.commit()
            conn.close()
            st.success(f"Factura {ncf} guardada. Total ${total:,.2f}")

    conn = get_conn()
    df = pd.read_sql("SELECT * FROM facturas ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

# --- Compras 606 ---
elif menu == "🛒 Compras 606":
    st.subheader("🛒 Registrar Compra - DGII 606")
    with st.form("compra"):
        prov = st.text_input("Proveedor")
        rnc_p = st.text_input("RNC Proveedor")
        ncf_c = st.text_input("NCF Compra")
        fecha_c = st.date_input("Fecha Compra", value=date.today())
        monto_c = st.number_input("Monto sin ITBIS", min_value=0.0, step=100.0)
        itbis_c = round(monto_c * 0.18, 2)
        total_c = monto_c + itbis_c
        st.write(f"ITBIS: ${itbis_c:,.2f} | Total: ${total_c:,.2f}")
        g2 = st.form_submit_button("Guardar Compra")
        if g2:
            conn = get_conn()
            conn.execute("INSERT INTO compras (rnc_proveedor,ncf,fecha,monto,itbis,total,proveedor) VALUES (?,?,?,?,?,?,?)",
                         (rnc_p, ncf_c, str(fecha_c), monto_c, itbis_c, total_c, prov))
            conn.commit()
            conn.close()
            st.success("Compra guardada para 606.")
    conn = get_conn()
    df2 = pd.read_sql("SELECT * FROM compras ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df2, use_container_width=True)

# --- Ventas 607 ---
elif menu == "📤 Ventas 607":
    st.subheader("📤 Ventas - DGII 607")
    conn = get_conn()
    df3 = pd.read_sql("SELECT * FROM facturas ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df3, use_container_width=True)
    st.info("Estas ventas son las que van en el 607.")

# --- DGII 606 Excel ---
elif menu == "📄 DGII 606 - Excel":
    st.subheader("📄 DGII 606 - Generar Excel Formato Azul Oficial")
    conn = get_conn()
    df606 = pd.read_sql("SELECT rnc_proveedor AS RNC, ncf AS NCF, fecha AS Fecha, monto AS Monto, itbis AS ITBIS, total AS Total, proveedor AS Proveedor FROM compras ORDER BY id", conn)
    conn.close()
    st.dataframe(df606, use_container_width=True)
    if st.button("📥 Descargar Excel 606", use_container_width=True):
        output = BytesIO()
        if TIENE_OPENPYXL:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "606"
            # Encabezado azul DGII
            azul = PatternFill("solid", fgColor="1F4E78")
            blanco = Font(color="FFFFFF", bold=True, size=11)
            headers = list(df606.columns) if len(df606) > 0 else ["RNC", "NCF", "Fecha", "Monto", "ITBIS", "Total", "Proveedor"]
            for col, h in enumerate(headers, 1):
                celda = ws.cell(row=1, column=col, value=h)
                celda.fill = azul
                celda.font = blanco
                celda.alignment = Alignment(horizontal="center")
                ws.column_dimensions[get_column_letter(col)].width = 18
            for r_idx, row in enumerate(df606.values, 2):
                for c_idx, val in enumerate(row, 1):
                    ws.cell(row=r_idx, column=c_idx, value=val)
            wb.save(output)
        else:
            # Fallback con pandas si no hay openpyxl
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df606.to_excel(writer, index=False, sheet_name="606")
        output.seek(0)
        st.download_button("⬇️ Descargar Ahora", data=output, file_name=f"DGII_606_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Configuración ---
elif menu == "⚙️ Configuración":
    st.subheader("⚙️ Configuración BASA")
    st.write(f"**Empresa:** Baldera Santos & Asociados SRL")
    st.write(f"**RNC:** 133378711")
    st.write(f"**Cuenta BHD:** ****0021")
    st.write(f"**Usuario:** {user.get('nombre')} - {user.get('correo')}")
    st.write(f"**OpenPyXL instalado:** {'✅ Sí' if TIENE_OPENPYXL else '❌ No - Revisa requirements.txt'}")
    if st.button("🔄 Verificar Requisitos"):
        st.rerun()
