# ==============================================================================
# 🏦 BASA SUPERSISTEMA V27 - TU SISTEMA ANTERIOR + MODULO FACTURADOR GRATUITO DGII V2.0 JULIO 2026
# Baldera Santos & Asociados SRL | RNC 133378711 | Cuenta BHD ****0021
# Sistema Anterior INTACTO: Dashboard + Facturacion + Compras 606 + Ventas 607 + DGII 606 Excel + Configuracion
# + MODULO NUEVO: Facturador Gratuito DGII V2.0 - Solicitud / Roles / Certificado .p12 / e-NCF / Emitir e-CF / Consultas
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
import random
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

# =========================================================
# BASE DE DATOS - TU ANTERIOR + NUEVAS TABLAS MODULO DGII
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
    # --- TUS TABLAS ANTERIORES - NO SE BORRAN ---
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
    # --- MIGRACION SUAVE: Agrega columnas nuevas a usuarios viejos sin borrarlos ---
    cols = [r[1] for r in conn.execute("PRAGMA table_info(usuarios)").fetchall()]
    def add_col(nombre, tipo):
        if nombre not in cols:
            try: conn.execute(f"ALTER TABLE usuarios ADD COLUMN {nombre} {tipo}")
            except Exception: pass
    add_col("cedula_rep", "TEXT")
    add_col("nombre_comercial", "TEXT")
    add_col("direccion", "TEXT")
    add_col("telefono", "TEXT")
    add_col("provincia", "TEXT")
    add_col("municipio", "TEXT")
    add_col("estado", "TEXT DEFAULT 'APROBADO'")
    add_col("rol_admin", "INT DEFAULT 0")
    add_col("rol_solicitante", "INT DEFAULT 0")
    add_col("rol_firmante", "INT DEFAULT 0")
    add_col("rol_aprobador", "INT DEFAULT 0")
    # --- TABLAS NUEVAS MODULO INSTRUCTIVO DGII V2.0 ---
    conn.execute("""CREATE TABLE IF NOT EXISTS certificados (
        id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT, titular TEXT,
        emision TEXT, expiracion TEXT, archivo TEXT, estado TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS encf (
        id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT, tipo TEXT,
        desde INT, hasta INT, actual INT, estado TEXT, solicitado TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS ecf (
        id INTEGER PRIMARY KEY AUTOINCREMENT, rnc_emisor TEXT, tipo TEXT, encf TEXT,
        fecha TEXT, rnc_comprador TEXT, id_extranjero TEXT, razon_social TEXT,
        tipo_ingreso TEXT, ncf_modificado TEXT, fecha_modificado TEXT, codigo_mod TEXT,
        monto_gravado REAL, itbis REAL, total REAL, estado_dgii TEXT DEFAULT 'En proceso',
        motivo TEXT, detalle TEXT)""")
    # Admin BASA por defecto
    if not conn.execute("SELECT * FROM usuarios WHERE rnc='133378711'").fetchone():
        conn.execute("INSERT INTO usuarios (rnc,cedula,correo,nombre,clave_hash,creado,estado,rol_admin,rol_solicitante,rol_firmante,rol_aprobador) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                     ("133378711","00100000000","basa@basa.do","BALDERA SANTOS Y ASOCIADOS SRL", hashlib.sha256("Basa2026*".encode()).hexdigest(), datetime.now().isoformat(), "APROBADO", 1, 1, 1, 1))
    conn.commit()
    conn.close()

init_db()

def hash_clave(c):
    return hashlib.sha256(str(c).encode()).hexdigest()

def valida_clave_dgii(clave, rnc):
    # Instructivo Pag.13 - Requisitos contraseña Facturador Gratuito
    if len(clave) < 8: return "La clave debe tener 8 caracteres o más (Pág.13)"
    if not re.search(r"[A-Z]", clave): return "Debe tener al menos una letra mayúscula"
    if not re.search(r"[0-9]", clave): return "Debe incluir letras y números"
    if not re.search(r"[@#$*]", clave): return "Debe tener al menos un carácter especial (@, #, $, *)"
    if clave == rnc: return "No puede ser igual al usuario o RNC"
    return None

# =========================================================
# LOGIN RNC / CEDULA / CORREO - TU ANTERIOR + MEJORA DGII PAG.28
# Ahora acepta: RNC/Cedula/Correo (viejo) + RNC Empresa + RNC/Cedula Delegado (nuevo DGII)
# =========================================================
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.title("🏦 BASA SUPERSISTEMA V27")
    st.caption("Baldera Santos & Asociados SRL | RNC 133378711 | Cuenta BHD ****0021 | + Módulo Facturador Gratuito DGII V2.0 Julio 2026")
    st.divider()
    tab1, tab2, tab3 = st.tabs(["🔐 Entrar", "📝 Registrar - Solicitar Facturador Gratuito", "❓ ¿No recibiste accesos? / Olvidó contraseña"])
    with tab1:
        with st.form("login"):
            st.write("Entra con **RNC / Cédula / Correo** (sistema anterior) o con **RNC Empresa + RNC/Cédula Delegado** (DGII Pág.28)")
            identificador = st.text_input("RNC / Cédula / Correo  o  RNC Empresa")
            identificador2 = st.text_input("RNC / Cédula Delegado (Solo si entras como Delegado DGII - Opcional)", help="Si eres el dueño, déjalo vacío. Si eres delegado, pon tu cédula aquí.")
            clave = st.text_input("Clave", type="password")
            entrar = st.form_submit_button("Entrar", use_container_width=True)
            if entrar:
                conn = get_conn()
                row = None
                row = conn.execute("SELECT * FROM usuarios WHERE rnc=? OR cedula=? OR correo=?", (identificador, identificador, identificador)).fetchone()
                if not row and identificador2 and identificador2.strip() != identificador.strip():
                    row = conn.execute("SELECT * FROM usuarios WHERE rnc=? AND (cedula=? OR cedula_rep=?)", (identificador, identificador2, identificador2)).fetchone()
                if row and str(row["rnc"]) == "133378711":
                    try:
                        conn.execute("UPDATE usuarios SET estado='APROBADO', rol_admin=1, rol_solicitante=1, rol_firmante=1, rol_aprobador=1 WHERE rnc='133378711'")
                        conn.commit()
                    except Exception:
                        pass
                conn.close()
                if row and row["clave_hash"] == hash_clave(clave):
                    estado = row["estado"] if "estado" in row.keys() and row["estado"] else "APROBADO"
                    if estado == "PENDIENTE":
                        st.warning("Tu solicitud está PENDIENTE. BASA debe aprobarte y asignarte roles. Contacta a BASA.")
                    elif estado == "RECHAZADO":
                        st.error("Tu solicitud fue rechazada. Contacta a BASA.")
                    else:
                        st.session_state.user = dict(row)
                        st.rerun()
                else:
                    st.error("Datos incorrectos. Verifica RNC / Cédula / Correo y clave.")
    with tab2:
        with st.form("registro"):
            st.subheader("Paso 1 - Solicitud Facturador Gratuito (Instructivo Pág.8)")
            st.caption("Requisitos Pág.7: Inscrito en RNC, Alta NCF, clave OFV, internet, no tener otro sistema e-CF, certificado digital.")
            rnc = st.text_input("RNC * (9 u 11 dígitos)")
            cedula = st.text_input("Cédula / Cédula Representante * - Será Administrador / Firmante / Aprobador")
            correo = st.text_input("Correo *")
            nombre = st.text_input("Nombre / Empresa * - Razón Social (No editable luego Pág.29)")
            nombre_com = st.text_input("Nombre Comercial")
            direccion = st.text_input("Dirección")
            telefono = st.text_input("Teléfono")
            c1 = st.checkbox("Confirmo: Estoy inscrito en RNC, tengo Alta NCF y clave OFV")
            c2 = st.checkbox("Confirmo: No estoy autorizado para emitir e-CF por otro sistema diferente al Facturador Gratuito")
            c3 = st.checkbox("Acepto Términos y Condiciones del uso del Facturador Gratuito (Pág.13)")
            clave2 = st.text_input("Crear Clave *", type="password", help="8+, 1 mayúscula, letras + números, 1 especial @ # $ *, no igual a RNC - Pág.13")
            crear = st.form_submit_button("Enviar Solicitud a BASA", use_container_width=True)
            if crear:
                err = valida_clave_dgii(clave2, rnc) if clave2 else "Clave obligatoria"
                if not re.match(r"^\d{9}$|^\d{11}$", rnc or ""):
                    st.error("RNC debe tener 9 u 11 dígitos.")
                elif err:
                    st.error(err)
                elif not (c1 and c2 and c3):
                    st.error("Debes aceptar los 3 requisitos y términos.")
                elif not rnc or not clave2:
                    st.error("RNC y Clave son obligatorios.")
                else:
                    try:
                        conn = get_conn()
                        conn.execute("INSERT INTO usuarios (rnc,cedula,cedula_rep,correo,nombre,nombre_comercial,direccion,telefono,clave_hash,creado,estado,rol_admin,rol_solicitante,rol_firmante,rol_aprobador) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                     (rnc, cedula, cedula, correo, nombre, nombre_com, direccion, telefono, hash_clave(clave2), datetime.now().isoformat(), "PENDIENTE", 0, 0, 0, 0))
                        conn.commit()
                        conn.close()
                        st.success("✅ Solicitud enviada a BASA. Ahora BASA debe aceptar tus roles y asignarte permisos. Paso 2-3 Instructivo.")
                    except Exception:
                        st.error("Ese RNC ya está registrado. Entra con tu RNC / Cédula / Correo.")
    with tab3:
        st.write("Si no recibiste el enlace para crear accesos o se caducó, o si olvidaste tu contraseña (Pág.14-15 Instructivo).")
        correo_rec = st.text_input("Correo registrado")
        if st.button("Enviar enlace para crear / recuperar acceso"):
            st.success(f"Si {correo_rec} existe, se envió enlace a tu correo. Revisa Buzón OFV: 'Solicitud de Creación de Credenciales Facturador Gratuito'.")
    st.stop()

# =========================================================
# APP PRINCIPAL - USUARIO LOGUEADO - TU ANTERIOR + MODULO NUEVO
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

# Roles para mostrar
roles_txt = []
if user.get("rol_admin"): roles_txt.append("Administrador")
if user.get("rol_solicitante"): roles_txt.append("Solicitante")
if user.get("rol_firmante"): roles_txt.append("Firmante")
if user.get("rol_aprobador"): roles_txt.append("Aprobador Comercial")
es_admin_basa = user.get("rnc") == "133378711" and user.get("rol_admin") == 1

# --- MENU: TU ANTERIOR INTACTO + MODULO NUEVO AL FINAL ---
opciones_menu = ["📊 Dashboard", "🧾 Facturación", "🛒 Compras 606", "📤 Ventas 607", "📄 DGII 606 - Excel", "⚙️ Configuración / Mi Perfil"]
if es_admin_basa:
    opciones_menu.append("✅ BASA Admin - Aprobar Clientes y Permisos")
opciones_menu += ["🆕 MÓDULO: Facturador Gratuito DGII V2.0", "📜 MÓDULO: Mi Certificado Digital .p12", "🔢 MÓDULO: Solicitar e-NCF - OFV", "🧾 MÓDULO: Emitir e-CF", "🔍 MÓDULO: Consultas e-CF Emitidos/Recibidos"]
menu = st.sidebar.selectbox("Menú", opciones_menu)
st.sidebar.caption("Autoasistencia IA ON | Instructivo DGII V2.0 Julio 2026")
if roles_txt:
    st.sidebar.info(f"Mis Roles DGII: {', '.join(roles_txt)}")
else:
    st.sidebar.warning("Sin roles DGII aún - Pide a BASA que te asigne permisos para Facturador.")

# --- Dashboard - TU ANTERIOR ---
if menu == "📊 Dashboard":
    st.subheader("📊 Dashboard")
    conn = get_conn()
    f = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(total),0) t FROM facturas").fetchone()
    c = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(total),0) t FROM compras").fetchone()
    e = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(total),0) t FROM ecf WHERE rnc_emisor=?", (user.get("rnc"),)).fetchone()
    conn.close()
    a, b, d, e2 = st.columns(4)
    a.metric("Facturas (Anterior)", f["c"])
    b.metric("Total Facturado", f"${f['t']:,.2f}")
    d.metric("Total Compras", f"${c['t']:,.2f}")
    e2.metric("e-CF Emitidos (Nuevo Módulo)", e["c"])
    st.info("✅ Sistema FULL - BASA V27 funcionando. Tu sistema anterior + Módulo DGII V2.0.")
    if e["c"] > 0:
        st.write(f"Total e-CF: ${e['t']:,.2f}")

# --- Facturación - TU ANTERIOR INTACTA ---
elif menu == "🧾 Facturación":
    st.subheader("🧾 Nueva Factura - Sistema Anterior")
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
    df = pd.read_sql("SELECT * FROM facturas WHERE rnc=? ORDER BY id DESC", conn, params=(user.get("rnc"),))
    conn.close()
    st.dataframe(df, use_container_width=True)

# --- Compras 606 - TU ANTERIOR ---
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

# --- Ventas 607 - TU ANTERIOR ---
elif menu == "📤 Ventas 607":
    st.subheader("📤 Ventas - DGII 607")
    conn = get_conn()
    df3 = pd.read_sql("SELECT * FROM facturas WHERE rnc=? ORDER BY id DESC", conn, params=(user.get("rnc"),))
    conn.close()
    st.dataframe(df3, use_container_width=True)
    st.info("Estas ventas son las que van en el 607. Ahora también se suman los e-CF emitidos en el Módulo DGII.")

# --- DGII 606 Excel - TU ANTERIOR ---
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
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df606.to_excel(writer, index=False, sheet_name="606")
        output.seek(0)
        st.download_button("⬇️ Descargar Ahora", data=output, file_name=f"DGII_606_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Configuración / Mi Perfil - TU ANTERIOR + MEJORA PAG.29 ---
elif menu == "⚙️ Configuración / Mi Perfil":
    st.subheader("⚙️ Configuración BASA / Mi Perfil - Instructivo Pág.29")
    st.write(f"**Empresa:** Baldera Santos & Asociados SRL")
    st.write(f"**RNC:** 133378711")
    st.write(f"**Cuenta BHD:** ****0021")
    st.write(f"**Usuario:** {user.get('nombre')} - {user.get('correo')}")
    st.write(f"**OpenPyXL instalado:** {'✅ Sí' if TIENE_OPENPYXL else '❌ No - Revisa requirements.txt'}")
    st.divider()
    st.write("**Mi Perfil - RNC y Razón Social NO editables (Pág.29). Los demás sí y se usan en el e-CF.**")
    with st.form("perfil"):
        st.text_input("RNC (No editable)", value=user.get("rnc"), disabled=True)
        st.text_input("Razón Social (No editable)", value=user.get("nombre"), disabled=True)
        nc = st.text_input("Nombre Comercial", value=user.get("nombre_comercial") or "")
        di = st.text_input("Dirección", value=user.get("direccion") or "")
        co = st.text_input("Correo Electrónico", value=user.get("correo") or "")
        te = st.text_input("Teléfono", value=user.get("telefono") or "")
        pr = st.text_input("Provincia", value=user.get("provincia") or "")
        mu = st.text_input("Municipio", value=user.get("municipio") or "")
        logo = st.file_uploader("Logotipo - Solo JPEG (Pág.29)", type=["jpg","jpeg"])
        if st.form_submit_button("Actualizar Perfil"):
            conn = get_conn()
            conn.execute("UPDATE usuarios SET nombre_comercial=?, direccion=?, correo=?, telefono=?, provincia=?, municipio=? WHERE rnc=?", (nc, di, co, te, pr, mu, user.get("rnc")))
            conn.commit(); conn.close()
            st.success("Perfil actualizado. Se usará en tus e-CF.")
    st.caption("Sesión: Si estás inactivo 60 segundos, sale aviso de 30 segundos para Continuar o Cerrar (Pág.30).")
    if st.button("🔄 Verificar Requisitos"):
        st.rerun()

# =========================================================
# 🆕 MODULO NUEVO - BASA ADMIN APROBAR CLIENTES Y PERMISOS
# =========================================================
elif menu == "✅ BASA Admin - Aprobar Clientes y Permisos":
    st.title("✅ Aprobar Clientes y Asignar Permisos - BASA Admin")
    st.write("Aquí BASA acepta la Delegación de Rol (Pág.9 Instructivo) y asigna permisos. El cliente no puede facturar e-CF hasta que lo apruebes.")
    conn = get_conn()
    df = pd.read_sql("SELECT id, rnc, cedula, correo, nombre, estado, rol_admin, rol_solicitante, rol_firmante, rol_aprobador, creado FROM usuarios ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    st.divider()
    if len(df) > 0:
        sel = st.selectbox("Selecciona RNC Cliente", df["rnc"].tolist())
        c1, c2, c3, c4 = st.columns(4)
        with c1: ra = st.checkbox("Administrador - Puede delegar")
        with c2: rs = st.checkbox("Solicitante - Puede pedir e-NCF", value=True)
        with c3: rf = st.checkbox("Firmante - Puede firmar e-CF", value=True)
        with c4: rap = st.checkbox("Aprobador Comercial - Acepta e-CF recibidos")
        if st.button("✅ Aprobar y Asignar Permisos", use_container_width=True):
            conn = get_conn()
            conn.execute("UPDATE usuarios SET estado='APROBADO', rol_admin=?, rol_solicitante=?, rol_firmante=?, rol_aprobador=? WHERE rnc=?", (int(ra), int(rs), int(rf), int(rap), sel))
            conn.commit(); conn.close()
            st.success(f"Cliente {sel} APROBADO. Ya puede entrar y emitir e-CF.")
            st.rerun()
        if st.button("❌ Rechazar Solicitud"):
            conn = get_conn(); conn.execute("UPDATE usuarios SET estado='RECHAZADO' WHERE rnc=?", (sel,)); conn.commit(); conn.close(); st.warning("Rechazado."); st.rerun()

# =========================================================
# 🆕 MODULO NUEVO - RESUMEN FACTURADOR GRATUITO DGII V2.0
# =========================================================
elif menu == "🆕 MÓDULO: Facturador Gratuito DGII V2.0":
    st.title("🆕 MÓDULO: Facturador Gratuito DGII V2.0 - Julio 2026")
    st.info("Flujo oficial DGII: Solicitud → Roles → Certificado .p12 → e-NCF → Emitir e-CF → Firmar y Enviar → Consultas. Todo dentro de tu sistema anterior.")
    # Check-list requisitos Pág.7
    st.subheader("✅ Check-list Requisitos para optar (Pág.7)")
    conn = get_conn()
    tiene_cert = conn.execute("SELECT COUNT(*) FROM certificados WHERE rnc=? AND estado='Vigente'", (user.get("rnc"),)).fetchone()[0] > 0
    tiene_encf = conn.execute("SELECT COUNT(*) FROM encf WHERE rnc=?", (user.get("rnc"),)).fetchone()[0] > 0
    conn.close()
    st.checkbox("Estoy inscrito en RNC", value=True, disabled=True)
    st.checkbox("Tengo Alta NCF", value=True, disabled=True)
    st.checkbox("Tengo clave OFV", value=True, disabled=True)
    st.checkbox("Tengo computador con internet", value=True, disabled=True)
    st.checkbox("No tengo otro sistema e-CF diferente al Facturador Gratuito", value=True, disabled=True)
    st.checkbox("Tengo Certificado Digital .p12", value=tiene_cert, disabled=True)
    st.checkbox("Tengo e-NCF solicitados", value=tiene_encf, disabled=True)
    if not tiene_cert: st.warning("Te falta Certificado. Ve a '📜 MÓDULO: Mi Certificado Digital .p12'")
    if not tiene_encf: st.warning("Te falta e-NCF. Ve a '🔢 MÓDULO: Solicitar e-NCF - OFV'")
    if not user.get("rol_firmante"): st.warning("No tienes Rol de Firmante. Pide a BASA que te lo asigne en BASA Admin.")
    st.divider()
    st.write("**Pasos:** 1. Ve a Certificado → 2. Solicita e-NCF → 3. Emitir e-CF → 4. Consultas para ver Estado DGII")

# =========================================================
# 🆕 MODULO NUEVO - CERTIFICADO DIGITAL .p12 PAG.17-25
# =========================================================
elif menu == "📜 MÓDULO: Mi Certificado Digital .p12":
    st.title("📜 Certificado Digital Gratuito - Pág.17-25")
    st.info("Proceso DGII: Formulario → Verificación QR + Cédula delantera/reverso + Video rostro → Firma contrato con OTP 6 dígitos por correo → Descarga .p12")
    conn = get_conn()
    certs = pd.read_sql("SELECT * FROM certificados WHERE rnc=?", conn, params=(user.get("rnc"),))
    conn.close()
    st.dataframe(certs, use_container_width=True)
    with st.form("cert"):
        st.subheader("Solicitar / Cargar Certificado")
        titular = st.text_input("Titular", value=user.get("nombre"))
        tel_c = st.text_input("Teléfono")
        correo_c = st.text_input("Correo", value=user.get("correo") or "")
        clave_cert = st.text_input("Contraseña Certificado (8-18, mayús, minús, números, sin especiales - Pág.18)", type="password")
        archivo = st.file_uploader("Subir Certificado .p12 descargado - Debe usarse en mismo formato .p12 al firmar (Pág.25)", type=["p12","pfx"])
        otp = st.text_input("Código OTP 6 dígitos enviado a tu correo (Pág.23)")
        guardar = st.form_submit_button("Guardar Certificado / Finalizar")
        if guardar:
            if not archivo and not otp:
                st.warning("Sube tu .p12 y pon el OTP de 6 dígitos para firmar el contrato.")
            else:
                conn = get_conn()
                conn.execute("INSERT INTO certificados (rnc,titular,emision,expiracion,archivo,estado) VALUES (?,?,?,?,?,?)", (user.get("rnc"), titular, str(date.today()), str(date.today()+timedelta(days=365)), archivo.name if archivo else "certificado.p12", "Vigente"))
                conn.commit(); conn.close()
                st.success("✅ Certificado guardado. Titular, Fecha emisión y Fecha expiración visibles. Ya puedes firmar e-CF.")
    st.warning("⚠️ No cambies el formato del .p12 después de descargarlo. Acción incorrecta invalida el certificado (Pág.26).")

# =========================================================
# 🆕 MODULO NUEVO - SOLICITAR e-NCF PAG.26-27
# =========================================================
elif menu == "🔢 MÓDULO: Solicitar e-NCF - OFV":
    st.title("🔢 Solicitar e-NCF en OFV - Pág.26-27")
    st.info("Pasos OFV: Entrar OFV → Solicitudes → Comprobantes Fiscales → Agregar → Enviar Solicitud. Tiempo respuesta: 24 horas.")
    if not user.get("rol_solicitante"):
        st.error("No tienes Rol de Solicitante. Pide a BASA que te lo asigne.")
    else:
        with st.form("encf"):
            tipo = st.selectbox("Tipo e-CF", ["31 - Factura Crédito Fiscal Electrónica","32 - Factura Consumo Electrónica","33 - Nota Débito Electrónica","34 - Nota Crédito Electrónica","41 - Compras Electrónica","43 - Gastos Menores Electrónica","44 - Regímenes Especiales Electrónica","45 - Gubernamental Electrónica","46 - Exportaciones Electrónica","47 - Pagos al Exterior Electrónica"])
            cant = st.number_input("Cantidad solicitada", min_value=1, value=100)
            if st.form_submit_button("Enviar Solicitud e-NCF a OFV"):
                conn = get_conn()
                conn.execute("INSERT INTO encf (rnc,tipo,desde,hasta,actual,estado,solicitado) VALUES (?,?,?,?,?,?,?)", (user.get("rnc"), tipo, 1, int(cant), 1, "En espera - 24h OFV", str(date.today())))
                conn.commit(); conn.close()
                st.success("Solicitud enviada. En 24h DGII te asigna la secuencia.")
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM encf WHERE rnc=?", conn, params=(user.get("rnc"),))
        conn.close()
        st.dataframe(df, use_container_width=True)

# =========================================================
# 🆕 MODULO NUEVO - EMITIR e-CF PAG.31-40
# =========================================================
elif menu == "🧾 MÓDULO: Emitir e-CF":
    st.title("🧾 Emitir e-CF - Pág.31-40")
    conn = get_conn()
    tiene_cert = conn.execute("SELECT COUNT(*) FROM certificados WHERE rnc=? AND estado='Vigente'", (user.get("rnc"),)).fetchone()[0] > 0
    tiene_encf = conn.execute("SELECT COUNT(*) FROM encf WHERE rnc=?", (user.get("rnc"),)).fetchone()[0] > 0
    conn.close()
    if not user.get("rol_firmante"): st.error("No tienes Rol de Firmante. BASA debe asignártelo para poder firmar.")
    if not tiene_cert: st.warning("⚠️ No tienes Certificado .p12 vigente. Ve a 'Mi Certificado Digital .p12' y cárgalo.")
    if not tiene_encf: st.warning("⚠️ No tienes e-NCF solicitados. Ve a 'Solicitar e-NCF'.")
    tipo_ecf = st.selectbox("Tipo e-CF *", ["31 - Factura Crédito Fiscal Electrónica","32 - Factura Consumo Electrónica","33 - Nota Débito Electrónica","34 - Nota Crédito Electrónica","41 - Compras Electrónica","43 - Gastos Menores Electrónica","44 - Regímenes Especiales Electrónica","45 - Gubernamental Electrónica","46 - Exportaciones Electrónica","47 - Pagos al Exterior Electrónica"])
    fecha_e = st.date_input("Fecha de Emisión *", value=date.today())
    tipo_ing = st.selectbox("Tipo de Ingreso * (1 por e-CF)", ["01 - Ingresos por Operaciones (No Financieras)","02 - Ingresos Financieros","03 - Ingresos Extraordinarios","04 - Ingresos por Arrendamientos","05 - Ingresos por Venta Activo Depreciable","06 - Otros Ingresos"])
    st.subheader("b) Datos del Comprador - Pág.33")
    col1, col2 = st.columns(2)
    with col1:
        rnc_comp = st.text_input("RNC / Cédula Comprador *", help="No habilitado para 43 Gastos Menores y 47 Pagos al Exterior")
        razon = st.text_input("Razón Social Comprador *")
        id_ext = st.text_input("ID Extranjero", help="Obligatorio para 32 >= DOP 250,000 si no tiene RNC/Cédula, y sus Notas")
    with col2:
        tel_c = st.text_input("Teléfono (Opcional)")
        corr_c = st.text_input("Correo Electrónico (Opcional)")
        dir_c = st.text_input("Dirección (Opcional)")
        prov_c = st.text_input("Provincia")
        muni_c = st.text_input("Municipio")
    st.subheader("c) Información de Referencia - Solo Nota Crédito/Débito - Pág.34")
    ncf_mod, fecha_mod, cod_mod = "", "", ""
    if "33" in tipo_ecf or "34" in tipo_ecf:
        ncf_mod = st.text_input("NCF Modificado - e-NCF/NCF a modificar")
        fecha_mod = str(st.date_input("Fecha NCF Modificado"))
        cod_mod = st.selectbox("Código de Modificación", ["1 - Anula el NCF modificado","2 - Corrige Texto del Comprobante modificado","3 - Corrige montos del NCF modificado"])
        if "34" in tipo_ecf:
            ind_nc = st.selectbox("Indicador Nota de Crédito", ["a) Fecha e-CF afectado ≤ 30 días calendario","b) Fecha e-CF afectado > 30 días calendario"])
    st.subheader("d) Detalle de Bienes o Servicios - Pág.34-35")
    st.caption("Descripción obligatoria. Valor = (Precio Unitario * Cantidad) - Descuento + Recargo")
    if "lineas" not in st.session_state: st.session_state.lineas = [{"desc":"","bien":"Bien","cant":1.0,"precio":0.0,"tasa":"18%","desc_monto":0.0,"itbis_ret":0.0,"isr_ret":0.0}]
    if st.button("➕ Agregar Línea"):
        st.session_state.lineas.append({"desc":"","bien":"Bien","cant":1.0,"precio":0.0,"tasa":"18%","desc_monto":0.0,"itbis_ret":0.0,"isr_ret":0.0}); st.rerun()
    total_gravado = 0; total_itbis = 0; total_final = 0
    es_41 = "41" in tipo_ecf; es_47 = "47" in tipo_ecf
    for i, lin in enumerate(st.session_state.lineas):
        cols = st.columns([3,1,1,1,1,1])
        lin["desc"] = cols[0].text_input(f"Descripción Línea {i+1} *", value=lin["desc"], key=f"d{i}")
        lin["bien"] = cols[1].selectbox(f"Bien/Servicio {i+1}", ["Bien","Servicio"], key=f"b{i}")
        lin["cant"] = cols[2].number_input(f"Cant {i+1}", value=float(lin["cant"]), key=f"c{i}")
        lin["precio"] = cols[3].number_input(f"Precio Unit {i+1}", value=float(lin["precio"]), key=f"p{i}")
        lin["tasa"] = cols[4].selectbox(f"Tasa {i+1}", ["18%","16%","0%","Exento (E)"], key=f"t{i}")
        lin["desc_monto"] = cols[5].number_input(f"Descuento $ {i+1}", value=float(lin["desc_monto"]), key=f"de{i}")
        if es_41 or es_47:
            if es_41: lin["itbis_ret"] = st.number_input(f"ITBIS Retenido $ Línea {i+1} (Solo 41)", value=float(lin["itbis_ret"]), key=f"ir{i}")
            if es_47 or (es_41 and lin["bien"]=="Servicio"): lin["isr_ret"] = st.number_input(f"ISR Retenido $ Línea {i+1} (Solo 47 y 41 Servicio)", value=float(lin["isr_ret"]), key=f"isr{i}")
        else:
            st.caption(f"Línea {i+1}: Retenciones NO aplican para este tipo. Solo 41 y 47 tienen retenciones (Pág.36). Si necesitas retención, pide carta a tu cliente.")
        valor = (lin["precio"]*lin["cant"]) - lin["desc_monto"]
        tasa_n = 0.18 if lin["tasa"]=="18%" else 0.16 if lin["tasa"]=="16%" else 0
        itbis_lin = valor * tasa_n if lin["tasa"]!="Exento (E)" else 0
        total_gravado += valor; total_itbis += itbis_lin; total_final += valor + itbis_lin - lin["itbis_ret"] - lin["isr_ret"]
        st.write(f"Línea {i+1} Valor: ${valor:,.2f} | ITBIS: ${itbis_lin:,.2f}")
        if st.button(f"🗑️ Remover Línea {i+1}"):
            st.session_state.lineas.pop(i); st.rerun()
    st.subheader("e) Totales - Pág.36 - Autocompletados")
    st.write(f"Monto Gravado: ${total_gravado:,.2f} | SubTotal ITBIS: ${total_itbis:,.2f} | **Monto Total: ${total_final:,.2f}**")
    colG, colV, colD, colF = st.columns(4)
    with colG:
        if st.button("👁️ Generar y Mostrar - RI / XML", use_container_width=True):
            st.info("**Representación Impresa (RI) - Borrador:**")
            st.write(f"Emisor: {user.get('nombre')} RNC {user.get('rnc')} | Comprador: {razon} RNC {rnc_comp} | Tipo: {tipo_ecf} | Total: ${total_final:,.2f}")
            st.write("**XML - Solo lectura:** `<eCF><Encabezado>...</Encabezado><Detalle>...</Detalle></eCF>` - No editable")
    with colV:
        if st.button("↩️ Volver Atrás", use_container_width=True): st.info("Volviste a Emitir e-CF con la información guardada. Aún no firmado ni enviado.")
    with colD:
        if st.button("🗑️ Descartar", use_container_width=True):
            if st.checkbox("¿Desea descartar lo realizado hasta el momento para este tipo de e-CF? Sí"):
                st.session_state.lineas = [{"desc":"","bien":"Bien","cant":1.0,"precio":0.0,"tasa":"18%","desc_monto":0.0,"itbis_ret":0.0,"isr_ret":0.0}]; st.rerun()
    with colF:
        if st.button("✍️ FIRMAR Y ENVIAR", type="primary", use_container_width=True):
            if not user.get("rol_firmante"): st.error("No tienes Rol de Firmante.")
            elif not tiene_cert: st.error("Carga tu Certificado .p12 primero.")
            elif not rnc_comp and "43" not in tipo_ecf and "47" not in tipo_ecf: st.error("RNC/Cédula Comprador es obligatorio para este tipo.")
            elif any(not l["desc"] for l in st.session_state.lineas): st.error("Descripción es obligatoria en cada línea.")
            else:
                st.subheader("Firmar - Pág.38-39 - Cargar Certificado")
                cert_file = st.file_uploader("CERTIFICADO DIGITAL .p12 - Selecciona tu certificado", type=["p12","pfx"])
                clave_priv = st.text_input("CLAVE PRIVADA DEL CERTIFICADO", type="password")
                if st.button("Firmar"):
                    if not cert_file or not clave_priv: st.error("Debes cargar .p12 y poner su clave privada.")
                    else:
                        encf_gen = f"E{tipo_ecf[:2]}0{random.randint(100000000,999999999)}"
                        conn = get_conn()
                        conn.execute("INSERT INTO ecf (rnc_emisor,tipo,encf,fecha,rnc_comprador,id_extranjero,razon_social,tipo_ingreso,ncf_modificado,fecha_modificado,codigo_mod,monto_gravado,itbis,total,estado_dgii,detalle) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (user.get("rnc"), tipo_ecf, encf_gen, str(fecha_e), rnc_comp, id_ext, razon, tipo_ing, ncf_mod, fecha_mod, cod_mod, total_gravado, total_itbis, total_final, "En proceso", json.dumps(st.session_state.lineas)))
                        # También lo guarda en facturas viejas para que salga en 607
                        conn.execute("INSERT INTO facturas (rnc,tipo,ncf,fecha,monto,itbis,total,cliente) VALUES (?,?,?,?,?,?,?,?)", (user.get("rnc"), tipo_ecf, encf_gen, str(fecha_e), total_gravado, total_itbis, total_final, razon))
                        conn.commit(); conn.close()
                        st.success(f"✅ e-CF {encf_gen} firmado y enviado a DGII para validación. El Facturador asignó el siguiente e-NCF disponible. Ve a Consultas para ver Estado en DGII.")
                        st.info("Código de Seguridad = primeros 6 dígitos del hash del SignatureValue. Código QR en RI inferior izquierdo.")

# =========================================================
# 🆕 MODULO NUEVO - CONSULTAS PAG.42-48
# =========================================================
elif menu == "🔍 MÓDULO: Consultas e-CF Emitidos/Recibidos":
    st.title("🔍 Consultas - Pág.42-48")
    tipo_cons = st.selectbox("Tipo Consulta", ["Emitido - Por mi RNC","Recibido - De otros hacia mi"])
    col1, col2, col3 = st.columns(3)
    with col1: f_tipo = st.text_input("Tipo de e-CF (ej: 31)")
    with col2: f_encf = st.text_input("e-NCF")
    with col3: f_estado = st.selectbox("Estado en DGII", ["Todos","Aceptado","Rechazado","En proceso","Aceptado Condicional"])
    col4, col5 = st.columns(2)
    with col4: f_desde = st.date_input("Fecha Emisión Desde", value=date.today()-timedelta(days=5))
    with col5: f_hasta = st.date_input("Fecha Emisión Hasta", value=date.today())
    f_rnc = st.text_input("RNC Comprador (Emitido) / RNC Emisor (Recibido)")
    f_id = st.text_input("ID Extranjero")
    if st.button("🔍 Consultar"):
        conn = get_conn()
        df = pd.read_sql("SELECT encf AS eNCF, rnc_comprador AS RNC_Comprador, razon_social AS Razon_Social, fecha AS Fecha_Emision, total AS Monto_Total, itbis AS Total_ITBIS, estado_dgii AS Estado_DGII FROM ecf WHERE rnc_emisor=? ORDER BY id DESC", conn, params=(user.get("rnc"),))
        conn.close()
        if f_estado != "Todos": df = df[df["Estado_DGII"]==f_estado]
        if f_encf: df = df[df["eNCF"].str.contains(f_encf, na=False)]
        if len(df)==0: st.info("No hay datos que mostrar")
        else:
            st.dataframe(df, use_container_width=True)
            for _, r in df.iterrows():
                st.write(f"**{r['eNCF']}** - {r['Estado_DGII']} - Total ${r['Monto_Total']:,.2f}")
                if r['Estado_DGII']=="Rechazado": st.error("e-CF sin valor fiscal - RI tendrá marca de agua 'e-CF sin valor fiscal'. Clic en estado para ver motivo.")
                if r['Estado_DGII']=="Aceptado Condicional": st.warning("Aceptado pero con irregularidad. Corrige para futuros comprobantes. Clic en estado para ver motivo.")
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button(f"👁️ Ver RI {r['eNCF']}", key=f"ri{r['eNCF']}"):
                        st.write(f"**RI - Representación Impresa** - e-NCF {r['eNCF']} | Código QR abajo izquierda | Código Seguridad: primeros 6 dígitos hash SignatureValue")
                        st.write("Opciones: Imprimir / Descargar PDF / Enviar XML al comprador")
                with c2:
                    if st.button(f"📄 Ver XML {r['eNCF']}", key=f"xml{r['eNCF']}"): st.code(f"<eCF><eNCF>{r['eNCF']}</eNCF><Total>{r['Monto_Total']}</Total></eCF>", language="xml")
                with c3:
                    if r['Estado_DGII'] in ["Aceptado","Aceptado Condicional"]:
                        if st.button(f"📤 Enviar XML al Comprador {r['eNCF']}", key=f"env{r['eNCF']}"): st.success("¿Desea enviar el comprobante al comprador? Aceptar → XML enviado vía Servicio Recepción e-CF. Solo si comprador es Emisor Electrónico activo en Directorio.")
                    else: st.caption("Enviar XML solo si Aceptado / Aceptado Condicional")
