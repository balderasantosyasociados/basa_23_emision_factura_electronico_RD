# BASA AUDIT INTELLIGENCE USA V23 - VERSION LIMPIA FULL
# Corregido: PDF/PNG, ID ruta, migracion, info.json, duplicados, cuenta enmascarada, DGII real vs local
import streamlit as st
import sqlite3, pandas as pd, os, re, json, hashlib, shutil
from datetime import date, datetime
from pathlib import Path
import urllib.parse

st.set_page_config(page_title="BASA V23 LIMPIA - eCF + Cartera", layout="wide")

# =========================================================
# 0. CONFIGURACION SEGURA - BASA
# =========================================================
BASE_DIR = Path("data_basa")
BASE_DIR.mkdir(exist_ok=True)
DB_PATH = BASE_DIR / "basa_v23.db"
CLIENTES_DIR = BASE_DIR / "clientes"
CLIENTES_DIR.mkdir(exist_ok=True)

# CUENTA BHD - NUNCA MOSTRAR COMPLETA EN PANTALLA
CUENTA_BHD_COMPLETA = "08694150021"  # Solo para uso interno / pago, no para mostrar
def enmascarar_cuenta(cuenta: str) -> str:
    # FIX 6: Exposicion cuenta completa
    if not cuenta or len(cuenta) < 4:
        return "****"
    return f"****{cuenta[-4:]}"  # Muestra ****5021

CUENTA_MOSTRAR = enmascarar_cuenta(CUENTA_BHD_COMPLETA)  # ****5021
BANCO = "BHD"
TITULAR = "Pedro Anibal Baldera"

# =========================================================
# 1. FIX: VALIDAR ID CLIENTE COMO RUTA - NO PERMITIR ../
# =========================================================
def validar_id_cliente(id_cliente: str) -> bool:
    # Solo letras, numeros, guion y guion bajo. Nada de / \ .. 
    if not id_cliente or len(id_cliente) > 50:
        return False
    if ".." in id_cliente or "/" in id_cliente or "\\" in id_cliente:
        return False
    return bool(re.match(r"^[A-Za-z0-9_-]+$", id_cliente))

def ruta_cliente_segura(id_cliente: str) -> Path | None:
    # FIX 2: Validacion insuficiente de IDs usados como rutas
    if not validar_id_cliente(id_cliente):
        return None
    ruta = (CLIENTES_DIR / id_cliente).resolve()
    # Asegura que la ruta quede DENTRO de clientes, no fuera
    if not str(ruta).startswith(str(CLIENTES_DIR.resolve())):
        return None
    return ruta

# =========================================================
# 2. FIX: VALIDAR ARCHIVO PDF vs PNG POR CONTENIDO
# =========================================================
def guardar_comprobante_seguro(archivo_subido, cliente_id: str):
    # FIX 1: No guardar PDF con extension .png
    if archivo_subido is None:
        return None, "Sin archivo"
    ruta_cliente = ruta_cliente_segura(cliente_id)
    if ruta_cliente is None:
        return None, "ID cliente invalido"
    ruta_cliente.mkdir(parents=True, exist_ok=True)

    contenido = archivo_subido.getvalue()
    nombre_original = archivo_subido.name or "archivo"
    # Detectar por MAGIC BYTES, no por nombre
    if contenido.startswith(b"%PDF"):
        ext_correcta = ".pdf"
        tipo_real = "PDF"
    elif contenido.startswith(b"\x89PNG"):
        ext_correcta = ".png"
        tipo_real = "PNG"
    elif contenido.startswith(b"\xff\xd8\xff"):
        ext_correcta = ".jpg"
        tipo_real = "JPG"
    else:
        return None, "Tipo de archivo no permitido. Solo PDF, PNG, JPG"

    # Si el usuario subio un PDF pero lo llamo .png, lo corregimos
    nombre_base = Path(nombre_original).stem
    nombre_base = re.sub(r"[^A-Za-z0-9_-]", "_", nombre_base)[:50]
    nombre_final = f"{nombre_base}{ext_correcta}"
    ruta_final = ruta_cliente / nombre_final
    # Evitar sobreescribir
    if ruta_final.exists():
        ruta_final = ruta_cliente / f"{nombre_base}_{int(datetime.now().timestamp())}{ext_correcta}"
    with open(ruta_final, "wb") as f:
        f.write(contenido)
    return str(ruta_final), f"Guardado como {tipo_real} - {nombre_final}"

# =========================================================
# 3. FIX: MIGRACION CARPETAS ANTIGUAS INEXISTENTES
# =========================================================
def migrar_carpetas_antiguas():
    # FIX 3: No fallar si carpeta vieja no existe
    carpetas_viejas = ["clientes_old", "data_old", "uploads_old", "basa_old"]
    for vieja in carpetas_viejas:
        p_vieja = Path(vieja)
        if not p_vieja.exists():
            continue  # Si no existe, saltar, no dar error
        if not p_vieja.is_dir():
            continue
        destino = BASE_DIR / f"migrado_{vieja}"
        try:
            if destino.exists():
                # Si ya existe destino, no sobreescribir
                continue
            shutil.move(str(p_vieja), str(destino))
        except Exception as e:
            st.warning(f"No se pudo migrar {vieja}: {e}")

migrar_carpetas_antiguas()

# =========================================================
# 4. FIX: RECUPERACION CONTRASENA CON info.json DANADO
# =========================================================
def leer_info_json_seguro(ruta: Path):
    # FIX 4: info.json danado no rompe el sistema
    if not ruta.exists():
        return {}
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
    except json.JSONDecodeError:
        # Hacer backup del archivo danado y crear uno nuevo vacio
        try:
            backup = ruta.with_suffix(".json.corrupto.bak")
            shutil.copy(str(ruta), str(backup))
            st.warning(f"info.json estaba dañado. Se hizo backup en {backup.name} y se creo uno nuevo.")
        except Exception:
            pass
        return {}
    except Exception:
        return {}

def guardar_info_json_seguro(ruta: Path, data: dict):
    # Guardar atomico: escribe temporal y luego renombra
    tmp = ruta.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(ruta)

# =========================================================
# 5. BASE DE DATOS
# =========================================================
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.execute("""CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, email TEXT UNIQUE, rnc TEXT UNIQUE, nombre TEXT, password_hash TEXT, fecha_registro DATE)""")
conn.execute("""CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY, rnc TEXT UNIQUE, nombre TEXT, telefono TEXT, email TEXT UNIQUE)""")
conn.execute("""CREATE TABLE IF NOT EXISTS facturas (id INTEGER PRIMARY KEY, numero_ecf TEXT UNIQUE, cliente_nombre TEXT, cliente_id TEXT, fecha_emision DATE, fecha_vencimiento DATE, monto REAL, estado TEXT, estado_dgii TEXT, link_azul TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS pagos (id INTEGER PRIMARY KEY, factura_id INTEGER, fecha_pago DATE, monto REAL, metodo TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS inventario (id INTEGER PRIMARY KEY, codigo TEXT UNIQUE, producto TEXT, stock INTEGER, precio REAL, minimo INTEGER)""")
conn.commit()

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

# =========================================================
# 6. FIX: VALIDAR DUPLICADOS EN REGISTRO
# =========================================================
def validar_email(email: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email or ""))

def registrar_usuario(email, rnc, nombre, password):
    # FIX 5: Falta validacion correos/IDs duplicados
    email = (email or "").strip().lower()
    rnc = (rnc or "").strip()
    if not validar_email(email):
        return False, "Correo invalido. Ejemplo: pedro@basa.com"
    if not rnc:
        return False, "RNC / Cedula obligatorio"
    if len(password or "") < 6:
        return False, "Contrasena debe tener minimo 6 caracteres"
    # Revisar duplicados ANTES de insertar
    existe = conn.execute("SELECT 1 FROM usuarios WHERE email=? OR rnc=?", (email, rnc)).fetchone()
    if existe:
        return False, "Ya existe un usuario con ese correo o RNC. Usa otro correo o recupera tu contrasena."
    # Revisar tambien en clientes
    existe_cli = conn.execute("SELECT 1 FROM clientes WHERE email=? OR rnc=?", (email, rnc)).fetchone()
    if existe_cli:
        return False, "Ese correo o RNC ya esta registrado como cliente."
    try:
        conn.execute("INSERT INTO usuarios (email,rnc,nombre,password_hash,fecha_registro) VALUES (?,?,?,?,?)", (email, rnc, nombre, hash_password(password), str(date.today())))
        conn.commit()
        return True, "Usuario registrado correctamente"
    except sqlite3.IntegrityError:
        return False, "Duplicado detectado por base de datos. No se guardo."

# =========================================================
# 7. FIX: DGII - SEPARAR LOCAL vs ENVIO REAL
# =========================================================
# FIX 7: El sistema NO debe reportar como enviado algo que solo fue registrado local
def enviar_a_dgii_real(factura: dict):
    """
    ENVIO REAL A DGII - TODAVIA NO IMPLEMENTADO
    Esta funcion es el UNICO lugar donde se debe hacer la transmision oficial.
    Por ahora NO hace envio. Retorna False para evitar falso 'Enviado'.
    Cuando tengas tu certificado .p12 y tu URL de DGII, aqui se conecta.
    """
    # TODO: Conectar con https://ecf.dgii.gov.do / servicio oficial DGII
    # Requiere: certificado .p12, RNC emisor, token DGII
    return False, "NO ENVIADO A DGII - Solo registrado local. Falta conectar servicio oficial DGII."

def registrar_factura_local(numero_ecf, cliente_nombre, cliente_id, fecha_em, fecha_ven, monto):
    # Esto SOLO guarda local, NO es envio a DGII
    try:
        conn.execute("INSERT INTO facturas (numero_ecf, cliente_nombre, cliente_id, fecha_emision, fecha_vencimiento, monto, estado, estado_dgii) VALUES (?,?,?,?,?,?,?,?)",
                     (numero_ecf, cliente_nombre, cliente_id, str(fecha_em), str(fecha_ven), monto, "PENDIENTE", "REGISTRADO LOCAL - NO ENVIADO A DGII"))
        conn.commit()
        return True, "Factura guardada LOCAL. NO enviada a DGII."
    except sqlite3.IntegrityError:
        return False, "Ese numero e-CF ya existe."

def clasificar_cartera(fecha_venc):
    try:
        fv = pd.to_datetime(fecha_venc).date()
        dias = (date.today() - fv).days
        if dias <= 30: return "VIGENTE 0-30", "🟢", dias
        elif dias <= 60: return "B 31-60", "🟡", dias
        elif dias <= 90: return "C 61-90", "🟠", dias
        else: return "VENCIDA +90", "🔴", dias
    except: return "VIGENTE 0-30", "🟢", 0

def link_whatsapp(telefono, mensaje):
    tel = "".join(filter(str.isdigit, str(telefono or "")))
    if len(tel)==10: tel = "1"+tel
    return f"https://wa.me/{tel}?text={urllib.parse.quote(mensaje)}"

# =========================================================
# INTERFAZ - BASA V23 LIMPIA
# =========================================================
st.sidebar.title("🏦 BASA V23 LIMPIA")
st.sidebar.write("AUDIT INTELLIGENCE USA")
st.sidebar.write(f"Cuenta BHD: {CUENTA_MOSTRAR} - {BANCO}")  # Muestra ****5021, no completa
st.sidebar.write(f"Titular: {TITULAR}")
st.sidebar.caption("⚠️ Estado DGII: Local ≠ Enviado Oficial")

menu = st.sidebar.selectbox("MENU", ["01 Dashboard", "02 Registro Usuario - Sin Duplicados", "03 Clientes + Historico", "04 Facturas e-CF - DGII Local vs Real", "05 Cartera + WhatsApp", "06 Inventario", "07 Subir Comprobante PDF/PNG Seguro", "08 Recuperar Contrasena Segura"])

if menu == "01 Dashboard":
    st.title("BASA V23 LIMPIA - Dashboard")
    df = pd.read_sql("SELECT numero_ecf, cliente_nombre, fecha_vencimiento, monto, estado, estado_dgii FROM facturas", conn)
    if len(df)>0:
        c1,c2,c3 = st.columns(3)
        c1.metric("Facturas", len(df))
        c2.metric("Total", f"RD$ {df['monto'].sum():,.0f}")
        c3.metric("Pendientes", len(df[df['estado']=='PENDIENTE']))
        st.dataframe(df)
        st.warning("⚠️ Columna 'estado_dgii' = REGISTRADO LOCAL - NO ENVIADO A DGII. No es envio oficial.")
    else:
        st.info("Sin facturas todavia.")

if menu == "02 Registro Usuario - Sin Duplicados":
    st.title("Registro - Sin Duplicados")
    with st.form("reg"):
        email = st.text_input("Correo")
        rnc = st.text_input("RNC / Cedula")
        nombre = st.text_input("Nombre")
        pw = st.text_input("Contrasena", type="password")
        if st.form_submit_button("Registrar"):
            ok, msg = registrar_usuario(email, rnc, nombre, pw)
            if ok: st.success(msg)
            else: st.error(msg)

if menu == "03 Clientes + Historico":
    st.title("Clientes + Historico")
    with st.form("cli"):
        rnc = st.text_input("RNC")
        nombre = st.text_input("Nombre")
        tel = st.text_input("Telefono WhatsApp 809...")
        email = st.text_input("Correo Cliente")
        if st.form_submit_button("Guardar Cliente"):
            email_n = email.strip().lower()
            if email_n and not validar_email(email_n):
                st.error("Correo invalido")
            else:
                existe = conn.execute("SELECT 1 FROM clientes WHERE rnc=? OR email=?", (rnc, email_n)).fetchone()
                if existe:
                    st.error("Ya existe cliente con ese RNC o correo. No se guardo duplicado.")
                else:
                    conn.execute("INSERT INTO clientes (rnc,nombre,telefono,email) VALUES (?,?,?,?)", (rnc,nombre,tel,email_n))
                    conn.commit(); st.success("Cliente guardado")
    st.dataframe(pd.read_sql("SELECT * FROM clientes", conn))

if menu == "04 Facturas e-CF - DGII Local vs Real":
    st.title("Facturas e-CF - DGII")
    st.info("IMPORTANTE: Aqui SOLO se registra local. Para envio oficial DGII necesitas certificado .p12 y conexion oficial.")
    clientes = pd.read_sql("SELECT * FROM clientes", conn)
    with st.form("fac"):
        num = st.text_input("Numero e-CF", "E310000000001")
        cli = st.selectbox("Cliente", clientes['nombre'].tolist() if len(clientes)>0 else ["Sin clientes"])
        cid = st.text_input("ID Cliente para Carpeta - Solo letras/numeros/guion", "CLI-001")
        fe = st.date_input("Fecha Emision", date.today())
        fv = st.date_input("Fecha Vencimiento", date.today())
        monto = st.number_input("Monto RD$", 0.0)
        if st.form_submit_button("Guardar Factura LOCAL"):
            if not validar_id_cliente(cid):
                st.error("ID cliente invalido. No uses / \\ .. ni espacios. Ejemplo: CLI-001")
            else:
                ok, msg = registrar_factura_local(num, cli, cid, fe, fv, monto)
                if ok: st.success(msg)
                else: st.error(msg)
    df = pd.read_sql("SELECT * FROM facturas", conn)
    st.dataframe(df)
    if len(df)>0:
        st.subheader("Intentar Envio Real a DGII - Separado")
        sel = st.selectbox("Factura para enviar a DGII", df['numero_ecf'].tolist())
        if st.button("Intentar Enviar a DGII Oficial"):
            # Esto NO va a decir 'Enviado' si no es real
            ok, msg = enviar_a_dgii_real({"numero_ecf": sel})
            st.error(f"DGII: {msg} - No se cambio el estado a Enviado.")
            st.caption("Cuando conectes el servicio oficial DGII, aqui se pondra: ENVIADO A DGII + fecha + codigo DGII.")

if menu == "05 Cartera + WhatsApp":
    st.title("Cartera por Edades + WhatsApp")
    st.write("VIGENTE 0-30 🟢 | B 31-60 🟡 | C 61-90 🟠 | VENCIDA +90 🔴")
    df = pd.read_sql("SELECT * FROM facturas WHERE estado='PENDIENTE'", conn)
    if len(df)>0:
        rows=[]
        for _, r in df.iterrows():
            bucket, color, dias = clasificar_cartera(r['fecha_vencimiento'])
            rows.append({"Cliente": r['cliente_nombre'], "e-CF": r['numero_ecf'], "Vencimiento": r['fecha_vencimiento'], "Dias": dias, "Monto": r['monto'], "Bucket": bucket})
        cdf = pd.DataFrame(rows)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("🟢 VIGENTE", f"RD$ {cdf[cdf['Bucket']=='VIGENTE 0-30']['Monto'].sum():,.0f}")
        c2.metric("🟡 B", f"RD$ {cdf[cdf['Bucket']=='B 31-60']['Monto'].sum():,.0f}")
        c3.metric("🟠 C", f"RD$ {cdf[cdf['Bucket']=='C 61-90']['Monto'].sum():,.0f}")
        c4.metric("🔴 VENCIDA", f"RD$ {cdf[cdf['Bucket']=='VENCIDA +90']['Monto'].sum():,.0f}")
        st.dataframe(cdf)
        for _, r in cdf.iterrows():
            if r['Bucket'] != "VIGENTE 0-30":
                msg = f"Hola {r['Cliente']}, su factura {r['e-CF']} por RD$ {r['Monto']:,.0f} tiene {r['Dias']} dias. Bucket {r['Bucket']}. Pague en BHD {CUENTA_MOSTRAR} - BASA."
                st.link_button(f"📲 WhatsApp {r['Cliente']} - {r['Bucket']}", link_whatsapp("8090000000", msg))
    else:
        st.info("Sin facturas pendientes.")

if menu == "06 Inventario":
    st.title("Inventario")
    with st.form("inv"):
        cod = st.text_input("Codigo", "PROD-001")
        prod = st.text_input("Producto")
        stock = st.number_input("Stock", 0)
        precio = st.number_input("Precio", 0.0)
        minimo = st.number_input("Minimo", 5)
        if st.form_submit_button("Agregar"):
            try:
                conn.execute("INSERT INTO inventario (codigo,producto,stock,precio,minimo) VALUES (?,?,?,?,?)", (cod,prod,stock,precio,minimo))
                conn.commit(); st.success("Agregado")
            except sqlite3.IntegrityError:
                st.error("Codigo duplicado. Usa otro codigo.")
    st.dataframe(pd.read_sql("SELECT * FROM inventario", conn))

if menu == "07 Subir Comprobante PDF/PNG Seguro":
    st.title("Subir Comprobante - Seguro PDF/PNG")
    st.info("Si subes un PDF con nombre .png, el sistema lo corrige a .pdf automaticamente por contenido.")
    cid = st.text_input("ID Cliente - Ej: CLI-001", "CLI-001")
    archivo = st.file_uploader("Sube PDF, PNG o JPG", type=["pdf","png","jpg","jpeg"])
    if st.button("Guardar Comprobante"):
        ruta, msg = guardar_comprobante_seguro(archivo, cid)
        if ruta: st.success(msg); st.write(ruta)
        else: st.error(msg)

if menu == "08 Recuperar Contrasena Segura":
    st.title("Recuperar Contrasena - Seguro")
    st.write("Si tu info.json esta dañado, el sistema hace backup y no se rompe.")
    ruta_info = BASE_DIR / "info.json"
    info = leer_info_json_seguro(ruta_info)
    st.write(f"Info cargada: {len(info)} registros")
    email = st.text_input("Tu correo para recuperar")
    if st.button("Recuperar"):
        email_n = email.strip().lower()
        user = conn.execute("SELECT * FROM usuarios WHERE email=?", (email_n,)).fetchone()
        if user:
            st.success("Usuario encontrado. Se enviara link de recuperacion a tu correo (simulado en esta version).")
            # Guardar intento de forma segura
            info[email_n] = {"ultimo_intento": str(datetime.now()), "estado": "solicitud_recuperacion"}
            guardar_info_json_seguro(ruta_info, info)
        else:
            st.error("Correo no encontrado. Verifica que este bien escrito.")

st.caption(f"BASA AUDIT INTELLIGENCE USA V23 LIMPIA - Cuenta BHD {CUENTA_MOSTRAR} - Pedro Anibal Baldera - Estado DGII Local ≠ Enviado Oficial")
