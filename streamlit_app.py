# ==============================================================================
# 🏦 BASA SUPERSISTEMA V27 - VERIFICADO FULL - ANTERIOR + DGII V2.0 + DUAL BASA/DGII 100/100
# Baldera Santos & Asociados SRL | RNC 133378711 | Cuenta BHD ****0021
# 1 SOLO MENU, 1 SOLO ROLES, 1 SOLA TABLA ECF CON MIGRACION, SIN DUPLICADOS
# ==============================================================================

import streamlit as st
import importlib.util
import sqlite3
import pandas as pd
import re
import json
import hashlib
import random
import string
from datetime import date, datetime, timedelta
from pathlib import Path
from io import BytesIO

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    TIENE_OPENPYXL = True
except Exception:
    openpyxl = None
    TIENE_OPENPYXL = False

try:
    import qrcode
    TIENE_QR = True
except Exception:
    qrcode = None
    TIENE_QR = False

st.set_page_config(page_title="BASA SUPERSISTEMA V27", layout="wide", page_icon="🏦")

def _verificar_basa():
    req = ["streamlit", "pandas", "openpyxl", "xlsxwriter", "numpy", "sqlalchemy", "fastapi", "requests", "cryptography", "lxml", "signxml", "PIL", "dateutil", "qrcode"]
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

BASE = Path("BASA_V27_SUPERSISTEMA")
BASE.mkdir(exist_ok=True)
DB = BASE / "basa.db"

def get_conn():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT, cedula TEXT, correo TEXT, nombre TEXT, clave_hash TEXT, creado TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS facturas (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT, tipo TEXT, ncf TEXT, fecha TEXT, monto REAL, itbis REAL, total REAL, cliente TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS compras (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc_proveedor TEXT, ncf TEXT, fecha TEXT, monto REAL, itbis REAL, total REAL, proveedor TEXT)""")
    cols = [r[1] for r in conn.execute("PRAGMA table_info(usuarios)").fetchall()]
    def add_col_usuario(nombre, tipo):
        if nombre not in cols:
            try:
                conn.execute(f"ALTER TABLE usuarios ADD COLUMN {nombre} {tipo}")
            except Exception:
                pass
    add_col_usuario("cedula_rep", "TEXT")
    add_col_usuario("nombre_comercial", "TEXT")
    add_col_usuario("direccion", "TEXT")
    add_col_usuario("telefono", "TEXT")
    add_col_usuario("provincia", "TEXT")
    add_col_usuario("municipio", "TEXT")
    add_col_usuario("pais", "TEXT DEFAULT 'DO - Republica Dominicana'")
    add_col_usuario("moneda", "TEXT DEFAULT 'DOP'")
    add_col_usuario("codigo_digital", "TEXT")
    add_col_usuario("proveedor_firma", "TEXT")
    add_col_usuario("estado", "TEXT DEFAULT 'APROBADO'")
    add_col_usuario("rol_admin", "INT DEFAULT 0")
    add_col_usuario("rol_solicitante", "INT DEFAULT 0")
    add_col_usuario("rol_firmante", "INT DEFAULT 0")
    add_col_usuario("rol_aprobador", "INT DEFAULT 0")
    add_col_usuario("afiliacion_pagada", "INT DEFAULT 0")
    add_col_usuario("plan", "TEXT DEFAULT 'Gratuito'")
    conn.execute("""CREATE TABLE IF NOT EXISTS certificados (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT, titular TEXT, emision TEXT, expiracion TEXT, archivo TEXT, estado TEXT, proveedor TEXT, codigo_digital TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS encf (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT, tipo TEXT, desde INT, hasta INT, actual INT, estado TEXT, solicitado TEXT)""")
    # ECF UNIFICADO: columnas viejas + nuevas DUAL
    conn.execute("""CREATE TABLE IF NOT EXISTS ecf (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc_emisor TEXT, tipo TEXT, encf TEXT, fecha TEXT, rnc_comprador TEXT, id_extranjero TEXT, razon_social TEXT, tipo_ingreso TEXT, ncf_modificado TEXT, fecha_modificado TEXT, codigo_mod TEXT, monto_gravado REAL, itbis REAL, total REAL, estado_dgii TEXT DEFAULT 'En proceso', motivo TEXT, detalle TEXT)""")
    ecf_cols = [r[1] for r in conn.execute("PRAGMA table_info(ecf)").fetchall()]
    def add_col_ecf(nombre, tipo):
        if nombre not in ecf_cols:
            try:
                conn.execute(f"ALTER TABLE ecf ADD COLUMN {nombre} {tipo}")
            except Exception:
                pass
    add_col_ecf("fecha_emision", "TEXT")
    add_col_ecf("fecha_vencimiento", "TEXT")
    add_col_ecf("fecha_firma", "TEXT")
    add_col_ecf("tipo_pago", "TEXT")
    add_col_ecf("forma_pago", "TEXT")
    add_col_ecf("moneda", "TEXT DEFAULT 'DOP'")
    add_col_ecf("tasa_cambio", "REAL DEFAULT 1.0")
    add_col_ecf("telefono_comprador", "TEXT")
    add_col_ecf("correo_comprador", "TEXT")
    add_col_ecf("direccion_comprador", "TEXT")
    add_col_ecf("provincia_comprador", "TEXT")
    add_col_ecf("municipio_comprador", "TEXT")
    add_col_ecf("indicador_nc", "TEXT")
    add_col_ecf("subtotal_gravado", "REAL")
    add_col_ecf("subtotal_exento", "REAL")
    add_col_ecf("total_itbis", "REAL")
    add_col_ecf("total_otros_impuestos", "REAL")
    add_col_ecf("total_isce", "REAL")
    add_col_ecf("total_iscav", "REAL")
    add_col_ecf("total_cdt", "REAL")
    add_col_ecf("total_propina", "REAL")
    add_col_ecf("total_itbis_retenido", "REAL")
    add_col_ecf("total_isr_retenido", "REAL")
    add_col_ecf("monto_total", "REAL")
    add_col_ecf("codigo_seguridad", "TEXT")
    add_col_ecf("comentario", "TEXT")
    add_col_ecf("xml_text", "TEXT")
    add_col_ecf("pais", "TEXT")
    add_col_ecf("codigo_digital", "TEXT")
    conn.execute("""CREATE TABLE IF NOT EXISTS servicios (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT, nombre TEXT, precio REAL, moneda TEXT, descripcion TEXT, activo INT DEFAULT 1, actualizado TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS pagos (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT, concepto TEXT, monto REAL, moneda TEXT, metodo TEXT, referencia TEXT, fecha TEXT, estado TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS historial (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT, usuario TEXT, accion TEXT, detalle TEXT, fecha TEXT, modulo TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS dev_keys (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT, nombre_app TEXT, api_key TEXT, webhook TEXT, activo INT DEFAULT 1, creado TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS auditoria (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT, evento TEXT, resultado TEXT, detalle TEXT, fecha TEXT, usuario TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS dual_sync (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT, encf TEXT UNIQUE, via_origen TEXT, via_destino TEXT, estado_basa TEXT, estado_dgii TEXT, fecha_basa TEXT, fecha_dgii TEXT, xml_hash TEXT, sincronizado INT DEFAULT 0, nota TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS validacion_dual (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT, encf TEXT, via TEXT, puntaje INT, checks TEXT, fecha TEXT, resultado TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS conexiones (id INTEGER PRIMARY KEY AUTOINCREMENT, rnc TEXT, nombre TEXT, tipo TEXT, endpoint TEXT, clave_oculta TEXT, activo INT DEFAULT 1)""")
    if not conn.execute("SELECT * FROM usuarios WHERE rnc='133378711'").fetchone():
        conn.execute("INSERT INTO usuarios (rnc,cedula,correo,nombre,clave_hash,creado,estado,rol_admin,rol_solicitante,rol_firmante,rol_aprobador,pais,moneda) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("133378711","00100000000","basa@basa.do","BALDERA SANTOS Y ASOCIADOS SRL", hashlib.sha256("Basa2026*".encode()).hexdigest(), datetime.now().isoformat(), "APROBADO", 1, 1, 1, 1, "DO - Republica Dominicana", "DOP"))
    if conn.execute("SELECT COUNT(*) FROM servicios WHERE rnc='133378711'").fetchone()[0] == 0:
        for nom, prec, desc in [("Afiliacion Facturador Gratuito DGII", 2500, "Registro + roles + certificado + e-NCF"), ("Emision e-CF Mensual", 1500, "Hasta 50 e-CF / mes + RI + XML + QR"), ("Declaracion DGII 606/607", 3000, "Preparacion 606/607"), ("Firma Digital Gestionada", 2000, "Gestion Viafirma / DGII / Industria y Comercio")]:
            conn.execute("INSERT INTO servicios (rnc,nombre,precio,moneda,descripcion,actualizado) VALUES (?,?,?,?,?,?)", ("133378711", nom, prec, "DOP", desc, datetime.now().isoformat()))
    conn.commit()
    conn.close()

init_db()

def hash_clave(c):
    return hashlib.sha256(str(c).encode()).hexdigest()

def gen_codigo():
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(6))

def gen_key():
    return "basa_live_" + "".join(random.choice(string.ascii_letters + string.digits) for _ in range(24))

def gen_qr(texto):
    if not TIENE_QR:
        return None
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def log_hist(rnc, usuario, accion, detalle, modulo):
    try:
        c = get_conn()
        c.execute("INSERT INTO historial (rnc,usuario,accion,detalle,fecha,modulo) VALUES (?,?,?,?,?,?)", (rnc, usuario, accion, detalle, datetime.now().isoformat(), modulo))
        c.commit()
        c.close()
    except Exception:
        pass

def log_audit(rnc, evento, resultado, detalle, usuario):
    try:
        c = get_conn()
        c.execute("INSERT INTO auditoria (rnc,evento,resultado,detalle,fecha,usuario) VALUES (?,?,?,?,?,?)", (rnc, evento, resultado, detalle, datetime.now().isoformat(), usuario))
        c.commit()
        c.close()
    except Exception:
        pass

def _score_dual(row_ecf, via):
    checks = []
    def _ok(cond, nombre):
        checks.append({"check": nombre, "ok": bool(cond), "puntos": 10 if cond else 0})
    _ok(row_ecf.get("encf"), "1. e-NCF presente")
    _ok(row_ecf.get("fecha_emision") or row_ecf.get("fecha"), "2. Fecha Emision presente")
    _ok(row_ecf.get("fecha_vencimiento"), "3. Fecha Vencimiento presente")
    _ok(row_ecf.get("rnc_comprador"), "4. RNC Comprador presente")
    _ok(row_ecf.get("razon_social"), "5. Razon Social presente")
    try:
        _det = json.loads(row_ecf.get("detalle") or "[]")
        _ok(len(_det) > 0 and all(d.get("desc") for d in _det), "6. Detalle con Descripcion")
    except Exception:
        _ok(False, "6. Detalle con Descripcion")
    _monto = row_ecf.get("monto_total") if row_ecf.get("monto_total") is not None else row_ecf.get("total")
    _ok(_monto is not None and float(_monto or 0) > 0, "7. Monto Total > 0")
    _ok(row_ecf.get("codigo_seguridad") and len(str(row_ecf.get("codigo_seguridad"))) == 6, "8. Codigo Seguridad 6 caracteres")
    _ok(row_ecf.get("fecha_firma"), "9. Fecha Firma Digital presente")
    _ok(row_ecf.get("xml_text") and "<eCF>" in str(row_ecf.get("xml_text")), "10. XML valido con <eCF>")
    total = sum(c["puntos"] for c in checks)
    return total, checks

def valida_clave_dgii(clave, rnc):
    if len(clave) < 8:
        return "La clave debe tener 8 caracteres o mas (Pag.13)"
    if not re.search(r"[A-Z]", clave):
        return "Debe tener al menos una letra mayuscula"
    if not re.search(r"[0-9]", clave):
        return "Debe incluir letras y numeros"
    if not re.search(r"[@#$*]", clave):
        return "Debe tener al menos un caracter especial (@, #, $, *)"
    if clave == rnc:
        return "No puede ser igual al usuario o RNC"
    return None

if "user" not in st.session_state:
    st.session_state.user = None
if "lineas" not in st.session_state:
    st.session_state.lineas = [{"desc": "Servicio Impuestos sept 2026", "bien": "Servicio", "cant": 1.0, "precio": 6000.0, "tasa": "18%", "desc_monto": 0.0, "itbis_ret": 0.0, "isr_ret": 0.0}]

if st.session_state.user is None:
    st.title("🏦 BASA SUPERSISTEMA V27")
    st.caption("Baldera Santos & Asociados SRL | RNC 133378711 | Cuenta BHD ****0021 | + Facturador Gratuito DGII V2.0 + DUAL BASA/DGII")
    st.divider()
    tab1, tab2, tab3 = st.tabs(["🔐 Entrar", "📝 Registrar - Solicitar Facturador Gratuito", "❓ Olvido contrasena"])
    with tab1:
        with st.form("login"):
            identificador = st.text_input("RNC / Cedula / Correo o RNC Empresa")
            identificador2 = st.text_input("RNC / Cedula Delegado (Solo Delegado - Si eres dueno, dejalo vacio)")
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
                        st.warning("Tu solicitud esta PENDIENTE. BASA debe aprobarte.")
                    elif estado == "RECHAZADO":
                        st.error("Tu solicitud fue rechazada. Contacta a BASA.")
                    else:
                        st.session_state.user = dict(row)
                        st.rerun()
                else:
                    st.error("Datos incorrectos. Si eres dueno, deja el segundo campo VACIO.")
    with tab2:
        with st.form("registro"):
            st.subheader("Paso 1 - Solicitud Facturador Gratuito (Pag.8)")
            rnc = st.text_input("RNC * (9 u 11 digitos)")
            cedula = st.text_input("Cedula Representante *")
            correo = st.text_input("Correo *")
            nombre = st.text_input("Nombre / Empresa *")
            nombre_com = st.text_input("Nombre Comercial")
            direccion = st.text_input("Direccion")
            telefono = st.text_input("Telefono")
            c1 = st.checkbox("Confirmo: Inscrito RNC, Alta NCF, clave OFV")
            c2 = st.checkbox("Confirmo: No tengo otro sistema e-CF diferente al Facturador Gratuito")
            c3 = st.checkbox("Acepto Terminos Facturador Gratuito (Pag.13)")
            clave2 = st.text_input("Crear Clave *", type="password")
            crear = st.form_submit_button("Enviar Solicitud a BASA", use_container_width=True)
            if crear:
                err = valida_clave_dgii(clave2, rnc) if clave2 else "Clave obligatoria"
                if not re.match(r"^\d{9}$|^\d{11}$", rnc or ""):
                    st.error("RNC debe tener 9 u 11 digitos.")
                elif err:
                    st.error(err)
                elif not (c1 and c2 and c3):
                    st.error("Debes aceptar los 3 requisitos.")
                else:
                    try:
                        conn = get_conn()
                        conn.execute("INSERT INTO usuarios (rnc,cedula,cedula_rep,correo,nombre,nombre_comercial,direccion,telefono,clave_hash,creado,estado,rol_admin,rol_solicitante,rol_firmante,rol_aprobador) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (rnc, cedula, cedula, correo, nombre, nombre_com, direccion, telefono, hash_clave(clave2), datetime.now().isoformat(), "PENDIENTE", 0, 0, 0, 0))
                        conn.commit()
                        conn.close()
                        st.success("Solicitud enviada a BASA.")
                    except Exception:
                        st.error("Ese RNC ya esta registrado. Entra con tu RNC.")
    with tab3:
        st.write("Si olvidaste tu contrasena (Pag.14-15).")
        correo_rec = st.text_input("Correo registrado")
        if st.button("Enviar enlace para crear / recuperar acceso"):
            st.success(f"Si {correo_rec} existe, se envio enlace a tu correo.")
    st.stop()

user = st.session_state.user
col1, col2, col3 = st.columns([3, 2, 1])
with col1:
    st.title("🏦 BASA SUPERSISTEMA V27")
    st.caption(f"Bienvenido: {user.get('nombre') or user.get('rnc')} | RNC: {user.get('rnc')} | Pais: {user.get('pais') or 'DO - Republica Dominicana'} | Moneda: {user.get('moneda') or 'DOP'}")
with col3:
    if st.button("Cerrar Sesion"):
        st.session_state.user = None
        st.rerun()

# UN SOLO BLOQUE ROLES + MENU - NO DUPLICAR ABAJO
roles_txt = []
if user.get("rol_admin"):
    roles_txt.append("Administrador")
if user.get("rol_solicitante"):
    roles_txt.append("Solicitante")
if user.get("rol_firmante"):
    roles_txt.append("Firmante")
if user.get("rol_aprobador"):
    roles_txt.append("Aprobador Comercial")
es_admin_basa = user.get("rnc") == "133378711" and user.get("rol_admin") == 1

opciones_menu = ["📊 Dashboard", "🧾 Facturación", "🛒 Compras 606", "📤 Ventas 607", "📄 DGII 606 - Excel", "⚙️ Configuración / Mi Perfil"]
if es_admin_basa:
    opciones_menu.append("✅ BASA Admin - Aprobar Clientes y Permisos")
opciones_menu += ["🆕 MÓDULO: Facturador Gratuito DGII V2.0", "📜 MÓDULO: Mi Certificado Digital .p12", "🔢 MÓDULO: Solicitar e-NCF - OFV", "🧾 MÓDULO: Emitir e-CF", "🔍 MÓDULO: Consultas e-CF Emitidos/Recibidos"]
opciones_menu += ["📜 Firma Digital - Subir o Gestionar", "💳 Pagar Afiliacion - Cliente Paga Aqui", "🛍️ Cartera de Servicios - Editable AUTOSAVE", "📜 Historial Completo", "🧑‍💻 Modulo Desarrolladores - API / Validar / Auditar", "🔌 Conexiones Ocultas - Solo BASA"]
opciones_menu += ["🔀 MODULO 2DA OPCION: Facturacion DUAL BASA / DGII - 100/100", "🔄 Sincronizar BASA <-> DGII", "✅ Validador 100/100 DUAL", "🧾 RI - Representacion Impresa Modelo NCF-28"]
menu = st.sidebar.selectbox("Menú", opciones_menu)
st.sidebar.caption("Autoasistencia IA ON | DGII V2.0 Julio 2026 | DUAL BASA/DGII | AUTOSAVE ON")
if roles_txt:
    st.sidebar.info(f"Mis Roles DGII: {', '.join(roles_txt)}")
else:
    st.sidebar.warning("Sin roles DGII aun - Pide a BASA que te asigne permisos.")

if menu == "📊 Dashboard":
    st.subheader("📊 Dashboard")
    conn = get_conn()
    f = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(total),0) t FROM facturas").fetchone()
    c = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(total),0) t FROM compras").fetchone()
    e = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(COALESCE(monto_total,total)),0) t FROM ecf WHERE rnc_emisor=?", (user.get("rnc"),)).fetchone()
    conn.close()
    a, b, d, e2 = st.columns(4)
    a.metric("Facturas (Anterior)", f["c"])
    b.metric("Total Facturado", f"${f['t']:,.2f}")
    d.metric("Total Compras", f"${c['t']:,.2f}")
    e2.metric("e-CF Emitidos", e["c"])
    st.info("✅ Sistema FULL - BASA V27 + DGII V2.0 + DUAL 100/100.")

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
        if st.form_submit_button("Guardar Factura"):
            conn = get_conn()
            conn.execute("INSERT INTO facturas (rnc,tipo,ncf,fecha,monto,itbis,total,cliente) VALUES (?,?,?,?,?,?,?,?)", (user.get("rnc"), "Venta", ncf, str(fecha), monto, itbis, total, cliente))
            conn.commit()
            conn.close()
            st.success(f"Factura {ncf} guardada.")
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM facturas WHERE rnc=? ORDER BY id DESC", conn, params=(user.get("rnc"),))
    conn.close()
    st.dataframe(df, use_container_width=True)

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
        if st.form_submit_button("Guardar Compra"):
            conn = get_conn()
            conn.execute("INSERT INTO compras (rnc_proveedor,ncf,fecha,monto,itbis,total,proveedor) VALUES (?,?,?,?,?,?,?)", (rnc_p, ncf_c, str(fecha_c), monto_c, itbis_c, total_c, prov))
            conn.commit()
            conn.close()
            st.success("Compra guardada para 606.")
    conn = get_conn()
    df2 = pd.read_sql("SELECT * FROM compras ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df2, use_container_width=True)

elif menu == "📤 Ventas 607":
    st.subheader("📤 Ventas - DGII 607")
    conn = get_conn()
    df3 = pd.read_sql("SELECT * FROM facturas WHERE rnc=? ORDER BY id DESC", conn, params=(user.get("rnc"),))
    conn.close()
    st.dataframe(df3, use_container_width=True)

elif menu == "📄 DGII 606 - Excel":
    st.subheader("📄 DGII 606 - Excel Formato Azul Oficial")
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

elif menu == "⚙️ Configuración / Mi Perfil":
    st.subheader("⚙️ Configuración / Mi Perfil - Pag.29 - AUTOSAVE")
    st.write(f"Empresa: Baldera Santos & Asociados SRL | RNC: 133378711 | Cuenta BHD: ****0021")
    with st.form("perfil"):
        st.text_input("RNC (No editable)", value=user.get("rnc"), disabled=True)
        st.text_input("Razon Social (No editable)", value=user.get("nombre"), disabled=True)
        nc = st.text_input("Nombre Comercial", value=user.get("nombre_comercial") or "")
        di = st.text_input("Direccion", value=user.get("direccion") or "")
        co = st.text_input("Correo", value=user.get("correo") or "")
        te = st.text_input("Telefono", value=user.get("telefono") or "")
        pr = st.text_input("Provincia", value=user.get("provincia") or "")
        mu = st.text_input("Municipio", value=user.get("municipio") or "")
        if st.form_submit_button("Actualizar Perfil"):
            conn = get_conn()
            conn.execute("UPDATE usuarios SET nombre_comercial=?, direccion=?, correo=?, telefono=?, provincia=?, municipio=? WHERE rnc=?", (nc, di, co, te, pr, mu, user.get("rnc")))
            conn.commit()
            conn.close()
            log_hist(user.get("rnc"), user.get("nombre"), "Perfil actualizado", f"{nc} {co}", "Perfil")
            st.success("Perfil actualizado.")
    st.write(f"Codigo Digital: {user.get('codigo_digital') or 'Sin codigo - Ve a Firma Digital'} | Proveedor: {user.get('proveedor_firma') or 'Sin proveedor'}")

elif menu == "✅ BASA Admin - Aprobar Clientes y Permisos":
    st.title("✅ Aprobar Clientes y Permisos - BASA Admin")
    conn = get_conn()
    df = pd.read_sql("SELECT id, rnc, cedula, correo, nombre, estado, rol_admin, rol_solicitante, rol_firmante, rol_aprobador, creado FROM usuarios ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    if len(df) > 0:
        sel = st.selectbox("Selecciona RNC Cliente", df["rnc"].tolist())
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            ra = st.checkbox("Administrador")
        with c2:
            rs = st.checkbox("Solicitante", value=True)
        with c3:
            rf = st.checkbox("Firmante", value=True)
        with c4:
            rap = st.checkbox("Aprobador Comercial")
        if st.button("✅ Aprobar y Asignar Permisos", use_container_width=True):
            conn = get_conn()
            conn.execute("UPDATE usuarios SET estado='APROBADO', rol_admin=?, rol_solicitante=?, rol_firmante=?, rol_aprobador=? WHERE rnc=?", (int(ra), int(rs), int(rf), int(rap), sel))
            conn.commit()
            conn.close()
            st.success(f"Cliente {sel} APROBADO.")
            st.rerun()

elif menu == "🆕 MÓDULO: Facturador Gratuito DGII V2.0":
    st.title("🆕 Facturador Gratuito DGII V2.0")
    conn = get_conn()
    tiene_cert = conn.execute("SELECT COUNT(*) FROM certificados WHERE rnc=? AND estado='Vigente'", (user.get("rnc"),)).fetchone()[0] > 0
    tiene_encf = conn.execute("SELECT COUNT(*) FROM encf WHERE rnc=?", (user.get("rnc"),)).fetchone()[0] > 0
    conn.close()
    st.checkbox("Inscrito RNC", value=True, disabled=True)
    st.checkbox("Alta NCF", value=True, disabled=True)
    st.checkbox("Clave OFV", value=True, disabled=True)
    st.checkbox("Certificado .p12", value=tiene_cert, disabled=True)
    st.checkbox("e-NCF solicitados", value=tiene_encf, disabled=True)
    if not tiene_cert:
        st.warning("Te falta Certificado. Ve a Certificado Digital.")
    if not tiene_encf:
        st.warning("Te falta e-NCF. Ve a Solicitar e-NCF.")

elif menu == "📜 MÓDULO: Mi Certificado Digital .p12":
    st.title("📜 Certificado Digital .p12 - Pag.17-25")
    conn = get_conn()
    certs = pd.read_sql("SELECT * FROM certificados WHERE rnc=?", conn, params=(user.get("rnc"),))
    conn.close()
    st.dataframe(certs, use_container_width=True)
    with st.form("cert"):
        titular = st.text_input("Titular", value=user.get("nombre"))
        clave_cert = st.text_input("Contrasena Certificado (8-18, mayus, minus, numeros)", type="password")
        archivo = st.file_uploader("Subir .p12", type=["p12", "pfx"])
        otp = st.text_input("OTP 6 digitos")
        if st.form_submit_button("Guardar Certificado"):
            if not archivo and not otp:
                st.warning("Sube tu .p12 y pon OTP.")
            else:
                conn = get_conn()
                conn.execute("INSERT INTO certificados (rnc,titular,emision,expiracion,archivo,estado) VALUES (?,?,?,?,?,?)", (user.get("rnc"), titular, str(date.today()), str(date.today() + timedelta(days=365)), archivo.name if archivo else "certificado.p12", "Vigente"))
                conn.commit()
                conn.close()
                st.success("Certificado guardado.")

elif menu == "🔢 MÓDULO: Solicitar e-NCF - OFV":
    st.title("🔢 Solicitar e-NCF - OFV - Pag.26-27")
    if not user.get("rol_solicitante"):
        st.error("No tienes Rol Solicitante. Pide a BASA.")
    else:
        with st.form("encf"):
            tipo = st.selectbox("Tipo e-CF", ["31 - Factura Credito Fiscal Electronica", "32 - Factura Consumo Electronica", "33 - Nota Debito Electronica", "34 - Nota Credito Electronica", "41 - Compras Electronica", "43 - Gastos Menores Electronica", "44 - Regimenes Especiales Electronica", "45 - Gubernamental Electronica", "46 - Exportaciones Electronica", "47 - Pagos al Exterior Electronica"])
            cant = st.number_input("Cantidad", min_value=1, value=100)
            if st.form_submit_button("Enviar Solicitud e-NCF"):
                conn = get_conn()
                conn.execute("INSERT INTO encf (rnc,tipo,desde,hasta,actual,estado,solicitado) VALUES (?,?,?,?,?,?,?)", (user.get("rnc"), tipo, 1, int(cant), 1, "En espera - 24h OFV", str(date.today())))
                conn.commit()
                conn.close()
                st.success("Solicitud enviada. En 24h DGII asigna secuencia.")
        conn = get_conn()
        df = pd.read_sql("SELECT * FROM encf WHERE rnc=?", conn, params=(user.get("rnc"),))
        conn.close()
        st.dataframe(df, use_container_width=True)

elif menu == "🧾 MÓDULO: Emitir e-CF":
    st.title("🧾 Emitir e-CF - Pag.31-40 - FULL + Fecha Vencimiento + Recargo + ISC + CDT + Propina + Comentario")
    conn = get_conn()
    tiene_cert = conn.execute("SELECT COUNT(*) FROM certificados WHERE rnc=? AND estado='Vigente'", (user.get("rnc"),)).fetchone()[0] > 0
    tiene_encf = conn.execute("SELECT COUNT(*) FROM encf WHERE rnc=?", (user.get("rnc"),)).fetchone()[0] > 0
    conn.close()
    if not user.get("rol_firmante"):
        st.error("No tienes Rol Firmante.")
    if not tiene_cert:
        st.warning("No tienes Certificado .p12 vigente.")
    if not tiene_encf:
        st.warning("No tienes e-NCF.")
    tipo_ecf = st.selectbox("Tipo e-CF *", ["31 - Factura Credito Fiscal Electronica", "32 - Factura Consumo Electronica", "33 - Nota Debito Electronica", "34 - Nota Credito Electronica", "41 - Compras Electronica", "43 - Gastos Menores Electronica", "44 - Regimenes Especiales Electronica", "45 - Gubernamental Electronica", "46 - Exportaciones Electronica", "47 - Pagos al Exterior Electronica"])
    colA1, colA2, colA3 = st.columns(3)
    with colA1:
        fecha_e = st.date_input("Fecha Emision *", value=date.today())
        tipo_ing = st.selectbox("Tipo Ingreso *", ["01 - Ingresos por Operaciones", "02 - Ingresos Financieros", "03 - Ingresos Extraordinarios", "04 - Arrendamientos", "05 - Venta Activo Depreciable", "06 - Otros Ingresos"])
    with colA2:
        fecha_v = st.date_input("Fecha Vencimiento *", value=date.today() + timedelta(days=30))
        tipo_pago = st.selectbox("Tipo Pago *", ["1 - Contado", "2 - Credito"])
    with colA3:
        forma_pago = st.selectbox("Forma Pago *", ["1 - Efectivo", "2 - Cheque/Transferencia", "3 - Tarjeta", "4 - Compensacion", "5 - Permuta", "6 - Nota Credito", "7 - Mixto"])
        moneda = st.selectbox("Moneda", ["DOP", "USD", "EUR"])
    st.subheader("b) Comprador")
    col1, col2 = st.columns(2)
    with col1:
        rnc_comp = st.text_input("RNC / Cedula Comprador *", value="133412918")
        razon = st.text_input("Razon Social Comprador *", value="MANUEL KING VEHICULOS SRL")
        id_ext = st.text_input("ID Extranjero")
    with col2:
        tel_c = st.text_input("Telefono")
        corr_c = st.text_input("Correo")
        dir_c = st.text_input("Direccion")
        prov_c = st.text_input("Provincia")
        muni_c = st.text_input("Municipio")
    st.subheader("c) Referencia - Solo 33/34")
    ncf_mod, fecha_mod, cod_mod, ind_nc = "", "", "", ""
    if "33" in tipo_ecf or "34" in tipo_ecf:
        ncf_mod = st.text_input("NCF Modificado")
        fecha_mod = str(st.date_input("Fecha NCF Modificado"))
        cod_mod = st.selectbox("Codigo Modificacion", ["1 - Anula", "2 - Corrige Texto", "3 - Corrige montos"])
        if "34" in tipo_ecf:
            ind_nc = st.selectbox("Indicador NC", ["a) <=30 dias", "b) >30 dias"])
    st.subheader("d) Detalle")
    if st.button("➕ Agregar Linea"):
        st.session_state.lineas.append({"desc": "", "bien": "Servicio", "cant": 1.0, "precio": 0.0, "tasa": "18%", "desc_monto": 0.0, "itbis_ret": 0.0, "isr_ret": 0.0})
        st.rerun()
    total_gravado = 0
    total_exento = 0
    total_itbis = 0
    total_ret_itbis = 0
    total_ret_isr = 0
    total_recargo = 0
    es_41 = "41" in tipo_ecf
    es_47 = "47" in tipo_ecf
    for i, lin in enumerate(st.session_state.lineas):
        cols = st.columns([3, 1, 1, 1, 1, 1])
        lin["desc"] = cols[0].text_input(f"Descripcion {i+1} *", value=lin["desc"], key=f"d{i}")
        lin["bien"] = cols[1].selectbox(f"Bien/Servicio {i+1}", ["Bien", "Servicio"], key=f"b{i}")
        lin["cant"] = cols[2].number_input(f"Cant {i+1}", value=float(lin["cant"]), key=f"c{i}")
        lin["precio"] = cols[3].number_input(f"Precio {i+1}", value=float(lin["precio"]), key=f"p{i}")
        lin["tasa"] = cols[4].selectbox(f"Tasa {i+1}", ["18%", "16%", "0%", "Exento (E)"], key=f"t{i}")
        lin["desc_monto"] = cols[5].number_input(f"Descuento {i+1}", value=float(lin["desc_monto"]), key=f"de{i}")
        lin["recargo"] = st.number_input(f"Recargo Linea {i+1}", value=float(lin.get("recargo", 0.0)), key=f"rec{i}")
        if es_41 or es_47:
            if es_41:
                lin["itbis_ret"] = st.number_input(f"ITBIS Ret {i+1} Solo 41", value=float(lin["itbis_ret"]), key=f"ir{i}")
            if es_47 or (es_41 and lin["bien"] == "Servicio"):
                lin["isr_ret"] = st.number_input(f"ISR Ret {i+1} Solo 47/41 Serv", value=float(lin["isr_ret"]), key=f"isr{i}")
        valor = (lin["precio"] * lin["cant"]) - lin["desc_monto"] + float(lin.get("recargo", 0.0))
        tasa_n = 0.18 if lin["tasa"] == "18%" else 0.16 if lin["tasa"] == "16%" else 0
        itbis_lin = valor * tasa_n if lin["tasa"] not in ["Exento (E)", "0%"] else 0
        if lin["tasa"] == "Exento (E)":
            total_exento += valor
        else:
            total_gravado += valor
        total_itbis += itbis_lin
        total_ret_itbis += lin["itbis_ret"]
        total_ret_isr += lin["isr_ret"]
        total_recargo += float(lin.get("recargo", 0.0))
        st.write(f"Linea {i+1} Valor: ${valor:,.2f} | ITBIS: ${itbis_lin:,.2f}")
        if st.button(f"🗑️ Remover {i+1}"):
            st.session_state.lineas.pop(i)
            st.rerun()
    st.subheader("e) Totales - Modelo NCF-28")
    total_otros = st.number_input("Otros Impuestos Adicionales", value=0.0)
    total_isce = st.number_input("Total ISCe", value=0.0)
    total_iscav = st.number_input("Total ISCav", value=0.0)
    total_cdt = st.number_input("CDT", value=0.0)
    total_propina = st.number_input("Propina Legal", value=0.0)
    monto_total = total_gravado + total_exento + total_itbis + total_otros + total_isce + total_iscav + total_cdt + total_propina - total_ret_itbis - total_ret_isr
    st.write(f"Subtotal Gravado: {total_gravado:,.2f} | Exento: {total_exento:,.2f} | ITBIS: {total_itbis:,.2f} | **Monto Total: {monto_total:,.2f}**")
    comentario = st.text_area("Comentario", value="Servicio Impuestos sept 2026")
    colG, colV, colD, colF = st.columns(4)
    with colG:
        if st.button("👁️ Generar y Mostrar RI / XML", use_container_width=True):
            st.write(f"Emisor: {user.get('nombre')} | Comprador: {razon} | Total: {monto_total:,.2f}")
            st.code(f"<eCF><Tipo>{tipo_ecf[:2]}</Tipo><Fecha>{fecha_e}</Fecha><Total>{monto_total:.2f}</Total></eCF>", language="xml")
    with colV:
        if st.button("↩️ Volver Atras", use_container_width=True):
            st.info("Volviste con info guardada. Aun no firmado.")
    with colD:
        if st.button("🗑️ Descartar", use_container_width=True):
            st.session_state.lineas = [{"desc": "", "bien": "Servicio", "cant": 1.0, "precio": 0.0, "tasa": "18%", "desc_monto": 0.0, "itbis_ret": 0.0, "isr_ret": 0.0}]
            st.rerun()
    with colF:
        if st.button("✍️ FIRMAR Y ENVIAR", type="primary", use_container_width=True):
            if not user.get("rol_firmante"):
                st.error("No tienes Rol Firmante.")
            elif not tiene_cert:
                st.error("Carga tu .p12 primero.")
            elif not rnc_comp and "43" not in tipo_ecf and "47" not in tipo_ecf:
                st.error("RNC Comprador obligatorio.")
            elif any(not l["desc"] for l in st.session_state.lineas):
                st.error("Descripcion obligatoria.")
            else:
                st.subheader("Firmar - Cargar Certificado")
                cert_file = st.file_uploader("CERTIFICADO .p12", type=["p12", "pfx"])
                clave_priv = st.text_input("CLAVE PRIVADA", type="password")
                if st.button("Firmar"):
                    if not cert_file or not clave_priv:
                        st.error("Carga .p12 y clave.")
                    else:
                        encf_gen = f"E{tipo_ecf[:2]}0{random.randint(100000000, 999999999)}"
                        codigo_seg = gen_codigo()
                        fecha_firma = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                        xml_text = f"<eCF><Tipo>{tipo_ecf[:2]}</Tipo><eNCF>{encf_gen}</eNCF><FechaEmision>{fecha_e}</FechaEmision><FechaVencimiento>{fecha_v}</FechaVencimiento><MontoTotal>{monto_total:.2f}</MontoTotal><CodigoSeguridad>{codigo_seg}</CodigoSeguridad></eCF>"
                        conn = get_conn()
                        conn.execute("INSERT INTO ecf (rnc_emisor,tipo,encf,fecha,fecha_emision,fecha_vencimiento,fecha_firma,rnc_comprador,id_extranjero,razon_social,tipo_ingreso,ncf_modificado,fecha_modificado,codigo_mod,monto_gravado,itbis,total,subtotal_gravado,subtotal_exento,total_itbis,total_otros_impuestos,total_isce,total_iscav,total_cdt,total_propina,total_itbis_retenido,total_isr_retenido,monto_total,codigo_seguridad,estado_dgii,comentario,detalle,xml_text,moneda,tipo_pago,forma_pago) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (user.get("rnc"), tipo_ecf, encf_gen, str(fecha_e), str(fecha_e), str(fecha_v), fecha_firma, rnc_comp, id_ext, razon, tipo_ing, ncf_mod, fecha_mod, cod_mod, total_gravado, total_itbis, monto_total, total_gravado, total_exento, total_itbis, total_otros, total_isce, total_iscav, total_cdt, total_propina, total_ret_itbis, total_ret_isr, monto_total, codigo_seg, "En proceso", comentario, json.dumps(st.session_state.lineas), xml_text, moneda, tipo_pago, forma_pago))
                        conn.execute("INSERT INTO facturas (rnc,tipo,ncf,fecha,monto,itbis,total,cliente) VALUES (?,?,?,?,?,?,?,?)", (user.get("rnc"), tipo_ecf, encf_gen, str(fecha_e), total_gravado, total_itbis, monto_total, razon))
                        conn.commit()
                        conn.close()
                        log_hist(user.get("rnc"), user.get("nombre"), "e-CF firmado", f"{encf_gen} {monto_total}", "Emitir e-CF")
                        st.success(f"✅ e-CF {encf_gen} firmado. Codigo Seguridad: {codigo_seg} | Fecha Firma: {fecha_firma}")
                        qr_buf = gen_qr(f"https://dgii.gov.do/eCF/{encf_gen}/{codigo_seg}")
                        if qr_buf:
                            st.image(qr_buf, width=150, caption="QR - Valida tu e-CF")

elif menu == "🔍 MÓDULO: Consultas e-CF Emitidos/Recibidos":
    st.title("🔍 Consultas - Pag.42-48")
    f_encf = st.text_input("e-NCF")
    f_estado = st.selectbox("Estado DGII", ["Todos", "Aceptado", "Rechazado", "En proceso", "Aceptado Condicional"])
    if st.button("🔍 Consultar"):
        conn = get_conn()
        df = pd.read_sql("SELECT encf AS eNCF, rnc_comprador AS RNC_Comprador, razon_social AS Razon_Social, COALESCE(fecha_emision,fecha) AS Fecha_Emision, COALESCE(monto_total,total) AS Monto_Total, COALESCE(total_itbis,itbis) AS Total_ITBIS, estado_dgii AS Estado_DGII, codigo_seguridad AS Codigo_Seguridad FROM ecf WHERE rnc_emisor=? ORDER BY id DESC", conn, params=(user.get("rnc"),))
        conn.close()
        if f_estado != "Todos":
            df = df[df["Estado_DGII"] == f_estado]
        if f_encf:
            df = df[df["eNCF"].str.contains(f_encf, na=False)]
        if len(df) == 0:
            st.info("No hay datos que mostrar")
        else:
            st.dataframe(df, use_container_width=True)
            for _, r in df.iterrows():
                st.write(f"**{r['eNCF']}** - {r['Estado_DGII']} - Total ${float(r['Monto_Total'] or 0):,.2f} - Codigo: {r['Codigo_Seguridad']}")
                if r["Estado_DGII"] == "Rechazado":
                    st.error("e-CF sin valor fiscal - RI con marca de agua.")
                if r["Estado_DGII"] == "Aceptado Condicional":
                    st.warning("Aceptado con irregularidad.")

elif menu == "📜 Firma Digital - Subir o Gestionar":
    st.title("📜 Firma Digital - Subir o Gestionar")
    conn = get_conn()
    certs = pd.read_sql("SELECT * FROM certificados WHERE rnc=?", conn, params=(user.get("rnc"),))
    conn.close()
    st.dataframe(certs, use_container_width=True)
    with st.form("firma_subir"):
        prov = st.selectbox("Proveedor", ["DGII", "Viafirma", "Industria y Comercio", "Otro"])
        codigo = st.text_input("Codigo Digital DGII / Viafirma / Industria y Comercio *")
        archivo = st.file_uploader("Subir .p12 / .pfx / .pem / .cer", type=["p12", "pfx", "pem", "cer", "crt"])
        clave_cert = st.text_input("Clave privada", type="password")
        if st.form_submit_button("💾 Guardar Firma y Codigo Digital"):
            if not codigo:
                st.error("Codigo Digital obligatorio.")
            else:
                conn = get_conn()
                conn.execute("INSERT INTO certificados (rnc,titular,emision,expiracion,archivo,estado,proveedor,codigo_digital) VALUES (?,?,?,?,?,?,?,?)", (user.get("rnc"), user.get("nombre"), str(date.today()), str(date.today() + timedelta(days=365)), archivo.name if archivo else "firma.p12", "Vigente", prov, codigo))
                conn.execute("UPDATE usuarios SET codigo_digital=?, proveedor_firma=? WHERE rnc=?", (codigo, prov, user.get("rnc")))
                conn.commit()
                conn.close()
                log_hist(user.get("rnc"), user.get("nombre"), "Firma subida", prov, "Firma")
                st.success(f"Firma guardada. Proveedor {prov} + Codigo guardado.")

elif menu == "💳 Pagar Afiliacion - Cliente Paga Aqui":
    st.title("💳 Pagar Afiliacion - Cliente paga aqui")
    conn = get_conn()
    serv = pd.read_sql("SELECT * FROM servicios WHERE rnc='133378711' AND activo=1", conn)
    conn.close()
    st.dataframe(serv, use_container_width=True)
    concepto = st.selectbox("Que quieres pagar", serv["nombre"].tolist() if len(serv) > 0 else ["Afiliacion"])
    monto_p = float(serv[serv["nombre"] == concepto]["precio"].iloc[0]) if len(serv) > 0 else 2500
    st.write(f"Monto: **{monto_p:,.2f} {user.get('moneda') or 'DOP'}**")
    metodo = st.selectbox("Metodo", ["Tarjeta Credito/Debito", "Transferencia BHD ****0021", "PayPal", "Link de Pago"])
    ref = st.text_input("Referencia / Ultimos 4 / Comprobante")
    if st.button("💳 Pagar Ahora y Activar", type="primary", use_container_width=True):
        if not ref:
            st.error("Pon referencia.")
        else:
            conn = get_conn()
            conn.execute("INSERT INTO pagos (rnc,concepto,monto,moneda,metodo,referencia,fecha,estado) VALUES (?,?,?,?,?,?,?,?)", (user.get("rnc"), concepto, monto_p, user.get("moneda") or "DOP", metodo, ref, str(date.today()), "Pagado"))
            conn.execute("UPDATE usuarios SET afiliacion_pagada=1, plan=? WHERE rnc=?", (concepto, user.get("rnc")))
            conn.commit()
            conn.close()
            log_hist(user.get("rnc"), user.get("nombre"), "Pago Afiliacion", f"{concepto} {monto_p}", "Pagos")
            st.success("✅ Pago registrado. Afiliacion ACTIVADA.")

elif menu == "🛍️ Cartera de Servicios - Editable AUTOSAVE":
    st.title("🛍️ Cartera de Servicios - Editable AUTOSAVE")
    conn = get_conn()
    serv = pd.read_sql("SELECT * FROM servicios WHERE rnc='133378711' ORDER BY id", conn)
    conn.close()
    for _, s in serv.iterrows():
        col1, col2, col3 = st.columns([3, 1, 3])
        with col1:
            nom_nuevo = st.text_input(f"Nombre {s['id']}", value=s["nombre"], key=f"serv_nom_{s['id']}")
        with col2:
            precio_nuevo = st.number_input(f"Precio {s['id']}", value=float(s["precio"]), key=f"serv_prec_{s['id']}")
        with col3:
            desc_nuevo = st.text_area(f"Descripcion {s['id']}", value=s["descripcion"] or "", key=f"serv_desc_{s['id']}")
        if (nom_nuevo != s["nombre"] or precio_nuevo != float(s["precio"]) or desc_nuevo != (s["descripcion"] or "")) and es_admin_basa:
            conn = get_conn()
            conn.execute("UPDATE servicios SET nombre=?, precio=?, descripcion=?, actualizado=? WHERE id=?", (nom_nuevo, precio_nuevo, desc_nuevo, datetime.now().isoformat(), int(s["id"])))
            conn.commit()
            conn.close()
            st.success(f"💾 AUTOSAVE: {nom_nuevo} guardado.")
    if es_admin_basa:
        with st.form("nuevo_serv"):
            nn = st.text_input("Nombre Nuevo Servicio")
            pp = st.number_input("Precio", min_value=0.0)
            dd = st.text_area("Descripcion")
            if st.form_submit_button("➕ Agregar Servicio"):
                conn = get_conn()
                conn.execute("INSERT INTO servicios (rnc,nombre,precio,moneda,descripcion,actualizado) VALUES (?,?,?,?,?,?)", ("133378711", nn, pp, "DOP", dd, datetime.now().isoformat()))
                conn.commit()
                conn.close()
                st.success("Servicio agregado.")

elif menu == "📜 Historial Completo":
    st.title("📜 Historial Completo")
    conn = get_conn()
    hist = pd.read_sql("SELECT * FROM historial WHERE rnc=? ORDER BY id DESC LIMIT 100", conn, params=(user.get("rnc"),))
    conn.close()
    st.dataframe(hist, use_container_width=True)

elif menu == "🧑‍💻 Modulo Desarrolladores - API / Validar / Auditar":
    st.title("🧑‍💻 Modulo Desarrolladores")
    conn = get_conn()
    keys = pd.read_sql("SELECT * FROM dev_keys WHERE rnc=?", conn, params=(user.get("rnc"),))
    conn.close()
    st.dataframe(keys, use_container_width=True)
    with st.form("new_key"):
        app_nom = st.text_input("Nombre App")
        webhook = st.text_input("Webhook URL")
        if st.form_submit_button("🔑 Generar API Key"):
            nk = gen_key()
            conn = get_conn()
            conn.execute("INSERT INTO dev_keys (rnc,nombre_app,api_key,webhook,creado) VALUES (?,?,?,?,?)", (user.get("rnc"), app_nom, nk, webhook, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            st.success(f"Tu API Key: {nk}")
    xml_a_validar = st.text_area("Pega XML para validar")
    if st.button("✅ Validar XML"):
        if "<eCF>" in xml_a_validar and "<eNCF>" in xml_a_validar:
            st.success("✅ XML VALIDO")
        else:
            st.error("❌ XML INVALIDO")
    conn = get_conn()
    aud = pd.read_sql("SELECT * FROM auditoria WHERE rnc=? ORDER BY id DESC LIMIT 50", conn, params=(user.get("rnc"),))
    conn.close()
    st.dataframe(aud, use_container_width=True)

elif menu == "🔌 Conexiones Ocultas - Solo BASA":
    if not es_admin_basa:
        st.error("Solo BASA Admin.")
    else:
        st.title("🔌 Conexiones Ocultas - Solo BASA")
        conn = get_conn()
        conns = pd.read_sql("SELECT * FROM conexiones WHERE rnc='133378711'", conn)
        conn.close()
        st.dataframe(conns, use_container_width=True)
        with st.form("nueva_conex"):
            nom_c = st.text_input("Nombre Conexion")
            tipo_c = st.selectbox("Tipo", ["DGII", "Viafirma", "Industria y Comercio", "Banco", "PayPal", "Otro"])
            endpoint = st.text_input("Endpoint")
            clave_o = st.text_input("Clave / Token", type="password")
            if st.form_submit_button("Guardar Conexion Oculta"):
                conn = get_conn()
                conn.execute("INSERT INTO conexiones (rnc,nombre,tipo,endpoint,clave_oculta) VALUES (?,?,?,?,?)", ("133378711", nom_c, tipo_c, endpoint, "****" + clave_o[-4:] if len(clave_o) >= 4 else "****"))
                conn.commit()
                conn.close()
                st.success("Conexion guardada oculta.")

elif menu == "🔀 MODULO 2DA OPCION: Facturacion DUAL BASA / DGII - 100/100":
    st.title("🔀 DUAL BASA / DGII - Ambos 100/100")
    via = st.radio("¿Por cual via facturas?", ["🟦 VIA 1 - Facturacion BASA", "🟩 VIA 2 - Via DGII Facturador Gratuito"], horizontal=False)
    st.session_state["via_dual"] = "BASA" if "VIA 1" in via else "DGII"
    if "VIA 1" in via:
        st.success("VIA 1 BASA: Facturas en BASA, firma con tu .p12 BASA / Viafirma / Industria y Comercio.")
    else:
        st.success("VIA 2 DGII: Facturas como Portal FG, con tu .p12 DGII, sincroniza a BASA.")
    colD1, colD2 = st.columns(2)
    with colD1:
        dual_tipo = st.selectbox("Tipo e-CF DUAL", ["31 - Factura Credito Fiscal Electronica", "32 - Factura Consumo Electronica", "33 - Nota Debito Electronica", "34 - Nota Credito Electronica", "41 - Compras Electronica", "43 - Gastos Menores Electronica", "44 - Regimenes Especiales Electronica", "45 - Gubernamental Electronica", "46 - Exportaciones Electronica", "47 - Pagos al Exterior Electronica"], key="dual_tipo")
        dual_fecha = st.date_input("Fecha Emision DUAL", value=date.today(), key="dual_fecha")
        dual_venc = st.date_input("Fecha Vencimiento DUAL", value=date.today() + timedelta(days=30), key="dual_venc")
    with colD2:
        dual_rnc_comp = st.text_input("RNC Comprador DUAL", value="133412918", key="dual_rnc")
        dual_razon = st.text_input("Razon Social DUAL", value="MANUEL KING VEHICULOS SRL", key="dual_razon")
        dual_monto = st.number_input("Monto sin ITBIS DUAL", value=6000.0, key="dual_monto")
        dual_desc = st.text_input("Descripcion DUAL", value="Servicio Impuestos sept 2026", key="dual_desc")
    dual_coment = st.text_area("Comentario DUAL", value="Servicio Impuestos sept 2026", key="dual_coment")
    dual_encf_manual = st.text_input("e-NCF DUAL - Si ya lo tienes de DGII, ponlo para no duplicar. Vacio = BASA genera.", placeholder="Ej: E310000000028", key="dual_encf")
    dual_codigo = st.text_input("Codigo Digital DUAL", value=user.get("codigo_digital") or "", key="dual_codigo")
    if st.button("💾 AUTOSAVE Borrador DUAL", key="dual_autosave"):
        log_hist(user.get("rnc"), user.get("nombre"), "Borrador DUAL", f"{dual_razon} {dual_monto}", "DUAL")
        st.success("Borrador DUAL guardado.")
    if st.button("✍️ FIRMAR Y ENVIAR DUAL", type="primary", key="dual_enviar"):
        if not dual_rnc_comp or not dual_razon or not dual_desc:
            st.error("Falta RNC, Razon o Descripcion.")
        elif not dual_codigo:
            st.error("Te falta Codigo Digital. Ponlo en Firma Digital.")
        else:
            conn = get_conn()
            existe = None
            if dual_encf_manual:
                existe = conn.execute("SELECT * FROM ecf WHERE encf=? AND rnc_emisor=?", (dual_encf_manual, user.get("rnc"))).fetchone()
            conn.close()
            if existe:
                st.warning(f"Ya existe {dual_encf_manual}. No se duplica. Ve a Sincronizar.")
            else:
                if st.button("✅ SI, CONFIRMO ENVIO DUAL", key="dual_confirm"):
                    encf_gen = dual_encf_manual if dual_encf_manual else f"E{dual_tipo[:2]}0{random.randint(100000000, 999999999)}"
                    codigo_seg = gen_codigo()
                    fecha_firma = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    itbis_dual = round(dual_monto * 0.18, 2)
                    total_dual = dual_monto + itbis_dual
                    detalle_dual = [{"desc": dual_desc, "bien": "Servicio", "cant": 1.0, "precio": dual_monto, "tasa": "18%", "desc_monto": 0.0, "recargo": 0.0}]
                    xml_dual = f"<eCF><Tipo>{dual_tipo[:2]}</Tipo><eNCF>{encf_gen}</eNCF><FechaEmision>{dual_fecha}</FechaEmision><FechaVencimiento>{dual_venc}</FechaVencimiento><MontoTotal>{total_dual:.2f}</MontoTotal><CodigoSeguridad>{codigo_seg}</CodigoSeguridad></eCF>"
                    conn = get_conn()
                    conn.execute("INSERT INTO ecf (rnc_emisor,tipo,encf,fecha,fecha_emision,fecha_vencimiento,fecha_firma,rnc_comprador,razon_social,subtotal_gravado,total_itbis,monto_total,codigo_seguridad,estado_dgii,comentario,detalle,xml_text,pais,codigo_digital,total,itbis,monto_gravado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (user.get("rnc"), dual_tipo, encf_gen, str(dual_fecha), str(dual_fecha), str(dual_venc), fecha_firma, dual_rnc_comp, dual_razon, dual_monto, itbis_dual, total_dual, codigo_seg, "En proceso", dual_coment, json.dumps(detalle_dual), xml_dual, user.get("pais") or "DO - Republica Dominicana", dual_codigo, total_dual, itbis_dual, dual_monto))
                    conn.execute("INSERT INTO facturas (rnc,tipo,ncf,fecha,monto,itbis,total,cliente) VALUES (?,?,?,?,?,?,?,?)", (user.get("rnc"), dual_tipo, encf_gen, str(dual_fecha), dual_monto, itbis_dual, total_dual, dual_razon))
                    via_origen = st.session_state.get("via_dual")
                    via_destino = "DGII" if via_origen == "BASA" else "BASA"
                    conn.execute("INSERT OR IGNORE INTO dual_sync (rnc,encf,via_origen,via_destino,estado_basa,estado_dgii,fecha_basa,fecha_dgii,xml_hash,sincronizado,nota) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (user.get("rnc"), encf_gen, via_origen, via_destino, "En proceso", "Pendiente", str(dual_fecha), str(dual_fecha), hashlib.sha256(xml_dual.encode()).hexdigest()[:12], 1, f"Creado via {via_origen}"))
                    conn.commit()
                    conn.close()
                    log_hist(user.get("rnc"), user.get("nombre"), f"ENVIO DUAL {via_origen}", f"{encf_gen} {total_dual}", "DUAL")
                    st.success(f"✅ DUAL {via_origen}: {encf_gen} | Total {total_dual:,.2f} | Codigo {codigo_seg} | Firma {fecha_firma}")
                    qr_buf = gen_qr(f"https://dgii.gov.do/eCF/{encf_gen}/{codigo_seg}")
                    if qr_buf:
                        st.image(qr_buf, width=150, caption="QR DUAL")

elif menu == "🔄 Sincronizar BASA <-> DGII":
    st.title("🔄 Sincronizar BASA <-> DGII")
    conn = get_conn()
    df_sync = pd.read_sql("SELECT * FROM dual_sync WHERE rnc=? ORDER BY id DESC", conn, params=(user.get("rnc"),))
    conn.close()
    st.dataframe(df_sync, use_container_width=True)
    st.subheader("Importar e-CF ya hecho en DGII")
    with st.form("import_dgii"):
        imp_encf = st.text_input("e-NCF DGII * Ej: E310000000028")
        imp_fecha = st.date_input("Fecha Emision DGII", value=date.today())
        imp_rnc_comp = st.text_input("RNC Comprador DGII")
        imp_razon = st.text_input("Razon Social DGII")
        imp_total = st.number_input("Monto Total DGII", value=7080.0)
        imp_codigo = st.text_input("Codigo Seguridad DGII Ej: OhfPUY")
        if st.form_submit_button("🔄 Importar DGII -> BASA"):
            if not imp_encf or not imp_codigo:
                st.error("e-NCF y Codigo obligatorios.")
            else:
                conn = get_conn()
                existe = conn.execute("SELECT * FROM ecf WHERE encf=? AND rnc_emisor=?", (imp_encf, user.get("rnc"))).fetchone()
                if existe:
                    st.warning(f"Ya existe {imp_encf}. No se duplica.")
                    conn.execute("UPDATE dual_sync SET sincronizado=1, estado_dgii='Aceptado' WHERE encf=?", (imp_encf,))
                else:
                    xml_imp = f"<eCF><eNCF>{imp_encf}</eNCF><CodigoSeguridad>{imp_codigo}</CodigoSeguridad></eCF>"
                    conn.execute("INSERT INTO ecf (rnc_emisor,tipo,encf,fecha,fecha_emision,fecha_vencimiento,fecha_firma,rnc_comprador,razon_social,subtotal_gravado,total_itbis,monto_total,codigo_seguridad,estado_dgii,comentario,detalle,xml_text,pais,total,itbis,monto_gravado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (user.get("rnc"), "31 - Factura Credito Fiscal Electronica", imp_encf, str(imp_fecha), str(imp_fecha), str(imp_fecha + timedelta(days=30)), datetime.now().strftime("%d-%m-%Y %H:%M:%S"), imp_rnc_comp, imp_razon, imp_total / 1.18, imp_total - imp_total / 1.18, imp_total, imp_codigo, "Aceptado", "Importado DGII", json.dumps([{"desc": "Importado DGII", "bien": "Servicio", "cant": 1.0, "precio": imp_total / 1.18, "tasa": "18%"}]), xml_imp, user.get("pais") or "DO - Republica Dominicana", imp_total, imp_total - imp_total / 1.18, imp_total / 1.18))
                    conn.execute("INSERT INTO dual_sync (rnc,encf,via_origen,via_destino,estado_basa,estado_dgii,fecha_basa,fecha_dgii,xml_hash,sincronizado,nota) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (user.get("rnc"), imp_encf, "DGII", "BASA", "Aceptado", "Aceptado", str(imp_fecha), str(imp_fecha), hashlib.sha256(xml_imp.encode()).hexdigest()[:12], 1, "Importado DGII -> BASA"))
                    conn.execute("INSERT INTO facturas (rnc,tipo,ncf,fecha,monto,itbis,total,cliente) VALUES (?,?,?,?,?,?,?,?)", (user.get("rnc"), "31 - Importado DGII", imp_encf, str(imp_fecha), imp_total / 1.18, imp_total - imp_total / 1.18, imp_total, imp_razon))
                conn.commit()
                conn.close()
                log_hist(user.get("rnc"), user.get("nombre"), "Sync DGII -> BASA", imp_encf, "SYNC")
                st.success(f"✅ {imp_encf} sincronizado DGII -> BASA sin duplicar.")
    st.subheader("Marcar e-CF BASA como Enviado en DGII")
    conn = get_conn()
    df_ecf = pd.read_sql("SELECT encf, estado_dgii FROM ecf WHERE rnc_emisor=? ORDER BY id DESC LIMIT 20", conn, params=(user.get("rnc"),))
    conn.close()
    if len(df_ecf) > 0:
        sel_sync = st.selectbox("Elige e-NCF BASA", df_ecf["encf"].tolist())
        nuevo_estado = st.selectbox("Nuevo Estado DGII", ["Aceptado", "Aceptado Condicional", "En proceso", "Rechazado"])
        if st.button("🔄 Sincronizar BASA -> DGII"):
            conn = get_conn()
            conn.execute("UPDATE ecf SET estado_dgii=? WHERE encf=? AND rnc_emisor=?", (nuevo_estado, sel_sync, user.get("rnc")))
            conn.execute("UPDATE dual_sync SET estado_dgii=?, sincronizado=1 WHERE encf=?", (nuevo_estado, sel_sync))
            conn.commit()
            conn.close()
            st.success(f"✅ {sel_sync} ahora {nuevo_estado} en ambas vias.")

elif menu == "✅ Validador 100/100 DUAL":
    st.title("✅ Validador 100/100 DUAL")
    conn = get_conn()
    dfv = pd.read_sql("SELECT * FROM ecf WHERE rnc_emisor=? ORDER BY id DESC LIMIT 20", conn, params=(user.get("rnc"),))
    conn.close()
    if len(dfv) == 0:
        st.info("Aun no tienes e-CF para validar.")
    else:
        sel_v = st.selectbox("Elige e-NCF", dfv["encf"].tolist())
        row_v = dfv[dfv["encf"] == sel_v].iloc[0]
        for via_v in ["BASA", "DGII"]:
            total_v, checks_v = _score_dual(dict(row_v), via_v)
            st.subheader(f"Via {via_v} - {total_v}/100")
            for c in checks_v:
                if c["ok"]:
                    st.success(f"✅ {c['check']} - 10/10")
                else:
                    st.error(f"❌ {c['check']} - 0/10")
            if total_v == 100:
                st.success(f"🎉 Via {via_v}: 100/100")
            else:
                st.warning(f"Via {via_v}: {total_v}/100 - Te falta {100-total_v}")
            if st.button(f"💾 Guardar Validacion {via_v}", key=f"guardar_val_{via_v}"):
                conn = get_conn()
                conn.execute("INSERT INTO validacion_dual (rnc,encf,via,puntaje,checks,fecha,resultado) VALUES (?,?,?,?,?,?,?)", (user.get("rnc"), sel_v, via_v, total_v, json.dumps(checks_v), datetime.now().isoformat(), "100/100 APROBADO" if total_v == 100 else f"{total_v}/100"))
                conn.commit()
                conn.close()
                st.success(f"Validacion {via_v} {total_v}/100 guardada.")
        conn = get_conn()
        df_val = pd.read_sql("SELECT * FROM validacion_dual WHERE rnc=? ORDER BY id DESC LIMIT 20", conn, params=(user.get("rnc"),))
        conn.close()
        st.dataframe(df_val, use_container_width=True)

elif menu == "🧾 RI - Representacion Impresa Modelo NCF-28":
    st.title("🧾 RI - Modelo NCF-28 - MANUEL KING 7,080.00")
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM ecf WHERE rnc_emisor=? ORDER BY id DESC LIMIT 10", conn, params=(user.get("rnc"),))
    conn.close()
    if len(df) == 0:
        st.info("Aun no tienes e-CF. Ejemplo: E310000000028 - MANUEL KING - 7,080.00 - Codigo OhfPUY - Fecha Firma 09-10-2026 08:54:56")
    else:
        sel = st.selectbox("Elige e-NCF", df["encf"].tolist())
        row = df[df["encf"] == sel].iloc[0]
        colL, colR = st.columns([2, 1])
        with colL:
            st.write(f"**{user.get('nombre')}**")
            st.write(f"**RNC:** {user.get('rnc')}")
            st.write(f"**Direccion:** {user.get('direccion') or 'Calle Orlando Martinez No.49, Brisas del Este'}")
            st.write(f"**Telefono:** {user.get('telefono') or '829-771-7390'}")
            st.write(f"**Fecha Emision:** {row['fecha_emision'] or row['fecha']}")
        with colR:
            st.write("**Factura de Credito Fiscal Electronica**")
            st.write(f"**e-NCF:** {row['encf']}")
            st.write(f"**Fecha Vencimiento:** {row['fecha_vencimiento']}")
            if row["estado_dgii"] == "Rechazado":
                st.error("MARCA DE AGUA: e-CF sin valor fiscal")
        st.write(f"**Razon Social Cliente:** {row['razon_social']}")
        st.write(f"**RNC Cliente:** {row['rnc_comprador']}")
        try:
            detalle = json.loads(row["detalle"] or "[]")
        except Exception:
            detalle = []
        if detalle:
            df_det = pd.DataFrame([{"Cant": d.get("cant"), "Descripcion": d.get("desc"), "Precio": d.get("precio"), "Valor": (d.get("precio", 0) * d.get("cant", 0) - d.get("desc_monto", 0) + d.get("recargo", 0))} for d in detalle])
            st.dataframe(df_det, use_container_width=True)
        colQR, colTot = st.columns([1, 2])
        with colQR:
            qr_buf = gen_qr(f"https://dgii.gov.do/eCF/{row['encf']}/{row['codigo_seguridad']}")
            if qr_buf:
                st.image(qr_buf, width=150)
            st.write(f"**Codigo Seguridad:** {row['codigo_seguridad']}")
            st.write(f"**Fecha Firma:** {row['fecha_firma']}")
        with colTot:
            st.write(f"Subtotal Gravado: {float(row['subtotal_gravado'] or row['monto_gravado'] or 0):,.2f}")
            st.write(f"Subtotal Exento: {float(row['subtotal_exento'] or 0):,.2f}")
            st.write(f"Total ITBIS: {float(row['total_itbis'] or row['itbis'] or 0):,.2f}")
            st.write(f"**Monto Total: {float(row['monto_total'] or row['total'] or 0):,.2f}**")
        st.write("**Comentario:**")
        st.write(row["comentario"] or "")
