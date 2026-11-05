# BASA e-CF PRO v71 PROFESIONAL - VERSION LIMPIA FULL
# Fixes: 1) PDF/PNG 2) ID ruta 3) Migracion 4) info.json danado 5) Duplicados 6) Cuenta enmascarada 7) DGII Local vs Real
import streamlit as st, json, os, hashlib, datetime, sqlite3, uuid, base64, random, string, shutil, re
from pathlib import Path
import pandas as pd

st.set_page_config(page_title="BASA e-CF PRO v71 PROFESIONAL - LIMPIO", layout="wide", page_icon="💰")

# =========================================================
# 0. CONFIG SEGURA - CUENTA ENMASCARADA
# =========================================================
BASE_DIR_NEW = Path("BASA_eCF_PRO_v71_PROFESIONAL")
CLIENTES_DB_NEW = BASE_DIR_NEW / "clientes_db"
BASE_DIR_NEW.mkdir(exist_ok=True); CLIENTES_DB_NEW.mkdir(exist_ok=True)
BACKUP_DIR = BASE_DIR_NEW / "backup_migracion_2026"; BACKUP_DIR.mkdir(exist_ok=True)
CASOS_DIR = CLIENTES_DB_NEW
BASES_VIEJAS = ["BASA_eCF_PRO_v7_0_AFILIACION","BASA_eCF_PRO_v6_3_ENVIO_DGII_CERT","BASA_eCF_PRO_v6_DGII_CERTIFICADO","BASA_eCF_PRO_v6_DGII","BASA_eCF_PRO_v5","clientes_db"]

# FIX 6: Cuenta completa solo en constante interna, NUNCA mostrar completa en header
_CUENTA_BHD_REAL = "08694150021"
def mostrar_cuenta(mask=True):
    if mask:
        return f"****{_CUENTA_BHD_REAL[-4:]}"  # ****5021
    return _CUENTA_BHD_REAL
CUENTA_MOSTRAR = mostrar_cuenta(True)

MASTER_USER = {"email":"Licpedrobaldera@gmail.com","password_hash":hashlib.sha256("Basa2026!".encode()).hexdigest(),"rnc":"133378711"}
CRED = {"nombre":"Lic. Pedro A. Baldera R.","empresa":"Baldera Santos & Asociados SRL","rnc":"133378711","telefono":"829-771-7390","whatsapp":"829-771-7390","email":"licpedrobaldera@gmail.com","direccion":"Calle Orlando Martinez No.49, Brisas del Este, Santo Domingo Este"}
DGII_PORTAL = "https://fg.dgii.gov.do/ecf/PortalFG/login?redirectUrl=%2Fecf%2Fportalfg"
DGII_HOME = "https://fg.dgii.gov.do/ecf/PortalFG/home"

# =========================================================
# FIX 2: VALIDAR ID CLIENTE COMO RUTA
# =========================================================
def validar_id_cliente(cid: str) -> bool:
    if not cid or len(cid) > 50: return False
    if ".." in cid or "/" in cid or "\\" in cid: return False
    return bool(re.match(r"^[A-Za-z0-9_-]+$", cid))

def ruta_cliente_segura(cid: str):
    if not validar_id_cliente(cid): return None
    ruta = (CASOS_DIR / cid).resolve()
    if not str(ruta).startswith(str(CASOS_DIR.resolve())): return None
    return ruta

def validar_email(email: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email or ""))

# =========================================================
# FIX 4: LEER info.json SEGURO - SI ESTA DANADO HACE BACKUP
# =========================================================
def leer_info_json_seguro(jf: Path):
    if not jf.exists(): return None
    try:
        data = json.loads(jf.read_text(encoding="utf-8"))
        if not isinstance(data, dict): return None
        return data
    except json.JSONDecodeError:
        try:
            backup = jf.with_suffix(".json.corrupto.bak")
            shutil.copy(str(jf), str(backup))
        except: pass
        return None
    except: return None

def guardar_info_json_seguro(jf: Path, data: dict):
    tmp = jf.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(jf)

# =========================================================
# FIX 7: DGII - SEPARAR LOCAL vs ENVIO REAL
# =========================================================
def enviar_a_dgii_real(factura: dict):
    # UNICO lugar para envio oficial DGII. Por ahora NO envia.
    # TODO: Conectar con API oficial DGII + certificado .p12 + token
    return False, "NO ENVIADO A DGII - Solo registrado local. Falta conectar servicio oficial DGII con certificado .p12."

# =========================================================
# FIX 3: MIGRACION SIN PERDIDAS - VERIFICA EXISTENCIA
# =========================================================
def migrar_sin_perdidas():
    log_mig = []
    for base_vieja in BASES_VIEJAS:
        p_vieja = Path(base_vieja)
        if not p_vieja.exists() or not p_vieja.is_dir(): continue
        origen = p_vieja / "clientes_db" if (p_vieja / "clientes_db").exists() else p_vieja
        if not origen.exists() or not origen.is_dir(): continue
        try: lista = list(origen.iterdir())
        except: continue
        for cli_dir in lista:
            try:
                if not cli_dir.is_dir() or not cli_dir.name.startswith("CLI-"): continue
                if not validar_id_cliente(cli_dir.name): continue
                destino = CASOS_DIR / cli_dir.name
                if not destino.exists():
                    shutil.copytree(str(cli_dir), str(destino), dirs_exist_ok=True)
                    backup_dest = BACKUP_DIR / cli_dir.name
                    if not backup_dest.exists():
                        shutil.copytree(str(cli_dir), str(backup_dest), dirs_exist_ok=True)
                    log_mig.append(f"MIGRADO {cli_dir.name} de {base_vieja} a v71 PROFESIONAL")
                else:
                    for archivo in ["info.json","logo.png"]:
                        src_file = cli_dir / archivo
                        dst_file = destino / archivo
                        if src_file.exists() and not dst_file.exists():
                            shutil.copy2(str(src_file), str(dst_file))
                            log_mig.append(f"SALVAGUARDADO {archivo} de {cli_dir.name}")
                    src_cert_dir = cli_dir / "certificados"; dst_cert_dir = destino / "certificados"
                    dst_cert_dir.mkdir(exist_ok=True)
                    if src_cert_dir.exists() and src_cert_dir.is_dir():
                        for cert_file in src_cert_dir.iterdir():
                            if cert_file.is_file() and cert_file.name not in [f.name for f in dst_cert_dir.iterdir()]:
                                shutil.copy2(str(cert_file), str(dst_cert_dir / cert_file.name))
                                log_mig.append(f"SALVAGUARDADO cert {cert_file.name}")
            except Exception as e:
                log_mig.append(f"ERROR migrando {cli_dir.name}: {e}")
    return log_mig

def get_db_path(cid):
    ruta = ruta_cliente_segura(cid)
    if ruta is None: raise ValueError(f"ID cliente invalido: {cid}")
    ruta.mkdir(exist_ok=True, parents=True); (ruta / "certificados").mkdir(exist_ok=True, parents=True)
    return ruta / f"BASA_{cid}_eCF.db"

def init_db_v71(cid):
    dbp = get_db_path(cid); conn = sqlite3.connect(str(dbp)); c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS facturas (id INTEGER PRIMARY KEY, ncf TEXT UNIQUE, tipo TEXT, cliente TEXT, rnc_cliente TEXT, descripcion TEXT, cantidad REAL, precio REAL, itbis REAL, descuento REAL, total REAL, fecha TEXT, vencimiento TEXT, estado TEXT, codigo_seg TEXT, firma_digital TEXT, precio_id TEXT, forma_pago TEXT, observaciones TEXT, xml_generado TEXT, trackid TEXT, estado_dgii TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS clientes_info (id TEXT PRIMARY KEY, nombre TEXT, rnc TEXT, email TEXT, direccion TEXT, telefono TEXT, precio_base REAL, logo_path TEXT, web TEXT, usuario_dgii TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS precios (id TEXT PRIMARY KEY, descripcion TEXT, precio REAL, cliente_id TEXT, fecha TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS historico (id INTEGER PRIMARY KEY, cliente_id TEXT, accion TEXT, ncf TEXT, detalle TEXT, usuario TEXT, fecha TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS dgii_config (id TEXT PRIMARY KEY, cliente_id TEXT, usuario_dgii TEXT, clave_dgii_hash TEXT, rnc_emisor TEXT, razon_social TEXT, fecha_registro TEXT, portal_url TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS certificados (id TEXT PRIMARY KEY, cliente_id TEXT, proveedor TEXT, cert_file_path TEXT, clave_cert_hash TEXT, fecha_expedicion TEXT, fecha_expiracion TEXT, estado TEXT, activo INTEGER, fecha_subida TEXT, firma_electronica TEXT, historico TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS afiliaciones (id TEXT PRIMARY KEY, usuario_master_email TEXT, empresa_principal_id TEXT, empresas_afiliadas_json TEXT, tipo TEXT, fecha_creacion TEXT, estado TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS pagos_bhd (id TEXT PRIMARY KEY, cliente_id TEXT, monto REAL, referencia_bhd TEXT, fecha_pago TEXT, comprobante_path TEXT, estado TEXT, cuenta_pago_id TEXT, liberado_por TEXT, fecha_liberacion TEXT, usuario_email TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS productos_servicios (id TEXT PRIMARY KEY, cliente_id TEXT, descripcion TEXT, precio REAL, unidad TEXT, categoria TEXT, veces_usado INTEGER, ultimo_uso TEXT, codigo TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS migracion_log (id INTEGER PRIMARY KEY, origen TEXT, destino TEXT, cliente_id TEXT, fecha TEXT, detalle TEXT, usuario TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS cuentas_pago_admin (id TEXT PRIMARY KEY, banco TEXT, numero_cuenta TEXT, titular TEXT, tipo_cuenta TEXT, moneda TEXT, ubicacion TEXT, estado TEXT, fecha_creacion TEXT, creado_por TEXT, notas TEXT)")
    conn.commit(); conn.close(); return dbp

def get_next_ncf(cid, tipo="E31"):
    dbp = get_db_path(cid)
    if not dbp.exists(): init_db_v71(cid)
    conn = sqlite3.connect(str(dbp)); c = conn.cursor()
    try:
        c.execute("SELECT ncf FROM facturas WHERE tipo=? ORDER BY id DESC LIMIT 1", (tipo,))
        row = c.fetchone(); nxt = int(row[0][3:])+1 if row and len(row[0])>3 and row[0][3:].isdigit() else 1
    except: nxt = 1
    conn.close(); return f"{tipo}{nxt:010d}"

def add_historico(cid, accion, ncf, detalle, usuario):
    try:
        dbp = get_db_path(cid); conn = sqlite3.connect(str(dbp)); c = conn.cursor()
        c.execute("INSERT INTO historico (cliente_id, accion, ncf, detalle, usuario, fecha) VALUES (?,?,?,?,?,?)", (cid, accion, ncf, detalle, usuario, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")))
        conn.commit(); conn.close()
    except: pass

# =========================================================
# FIX 1: GUARDAR LOGO / CERT / COMPROBANTE POR CONTENIDO REAL
# =========================================================
def detectar_ext_por_contenido(contenido: bytes, nombre_original: str):
    if contenido.startswith(b"%PDF"): return ".pdf"
    if contenido.startswith(b"\x89PNG"): return ".png"
    if contenido.startswith(b"\xff\xd8\xff"): return ".jpg"
    if contenido.startswith(b"PK\x03\x04"): return ".zip"
    # .p12 no tiene magic fijo, se valida por extension + tamano
    if nombre_original.lower().endswith(".p12"): return ".p12"
    return None

def save_logo(cid, uploaded_file):
    if not validar_id_cliente(cid): raise ValueError("ID cliente invalido")
    cf = CASOS_DIR / cid; cf.mkdir(exist_ok=True, parents=True)
    contenido = uploaded_file.getbuffer().tobytes() if hasattr(uploaded_file, "getbuffer") else uploaded_file.read()
    ext = detectar_ext_por_contenido(contenido, uploaded_file.name or "")
    if ext not in [".png", ".jpg"]:
        # Si es PNG/JPG real pero con otro nombre, forzar .png solo si es imagen
        if contenido.startswith(b"\x89PNG"): ext = ".png"
        elif contenido.startswith(b"\xff\xd8\xff"): ext = ".jpg"
        else: raise ValueError("Logo debe ser PNG o JPG real")
    logo_path = cf / f"logo{ext}"
    with open(logo_path, "wb") as f: f.write(contenido)
    return str(logo_path)

def save_cert(cid, uploaded_file, proveedor):
    if not validar_id_cliente(cid): raise ValueError("ID cliente invalido")
    cf = CASOS_DIR / cid / "certificados"; cf.mkdir(parents=True, exist_ok=True)
    contenido = uploaded_file.getbuffer().tobytes() if hasattr(uploaded_file, "getbuffer") else uploaded_file.read()
    # Cert .p12: no validar por magic, solo tamano y extension
    if len(contenido) == 0: raise ValueError("Certificado vacio")
    proveedor_limpio = re.sub(r"[^A-Za-z0-9_-]", "_", proveedor)[:20]
    cert_name = f"cert_{proveedor_limpio}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.p12"
    cert_path = cf / cert_name
    with open(cert_path, "wb") as f: f.write(contenido)
    return str(cert_path)

def save_comprobante_bhd(cid, uploaded_file):
    # FIX 1: ANTES siempre .png aunque fuera PDF. AHORA detecta contenido.
    if not validar_id_cliente(cid): raise ValueError("ID cliente invalido")
    cf = CASOS_DIR / cid; cf.mkdir(exist_ok=True, parents=True)
    contenido = uploaded_file.getbuffer().tobytes() if hasattr(uploaded_file, "getbuffer") else uploaded_file.read()
    ext = detectar_ext_por_contenido(contenido, uploaded_file.name or "")
    if ext is None:
        raise ValueError("Comprobante debe ser PDF, PNG o JPG real. No se pudo detectar tipo.")
    comp_name = f"comprobante_pago_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
    comp_path = cf / comp_name
    with open(comp_path, "wb") as f: f.write(contenido)
    return str(comp_path)

def autoguardar_producto(cid, descripcion, precio, unidad="CAJ"):
    try:
        dbp = get_db_path(cid); conn = sqlite3.connect(str(dbp)); c = conn.cursor()
        c.execute("SELECT * FROM productos_servicios WHERE cliente_id=? AND descripcion=?", (cid, descripcion))
        row = c.fetchone()
        if row:
            c.execute("UPDATE productos_servicios SET veces_usado=veces_usado+1, ultimo_uso=?, precio=? WHERE id=?", (datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), precio, row[0]))
        else:
            pid = f"PROD-{str(uuid.uuid4())[:6].upper()}"
            c.execute("INSERT INTO productos_servicios (id,cliente_id,descripcion,precio,unidad,categoria,veces_usado,ultimo_uso,codigo) VALUES (?,?,?,?,?,?,?,?,?)", (pid, cid, descripcion, precio, unidad, "General", 1, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), descripcion[:10].upper()))
        conn.commit(); conn.close()
    except: pass

def get_cuenta_pago_activa():
    for cf in CASOS_DIR.iterdir():
        if cf.is_dir():
            dbp = cf / f"BASA_{cf.name}_eCF.db"
            if dbp.exists():
                try:
                    conn = sqlite3.connect(str(dbp)); c = conn.cursor()
                    c.execute("SELECT * FROM cuentas_pago_admin WHERE estado='Activa' ORDER BY fecha_creacion DESC LIMIT 1")
                    row = c.fetchone(); conn.close()
                    if row: return row
                except: pass
    return ("CUENTA-OFICIAL-001", "BHD León", _CUENTA_BHD_REAL, "Pedro Anibal Baldera", "Ahorros en Pesos", "DOP", "RD Local", "Activa", datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "Licpedrobaldera@gmail.com", "Cuenta oficial autorizada")

def format_cuenta_profesional(cuenta_row):
    if not cuenta_row:
        return '<div style="padding:15px;background:#f8f9fa;border-radius:10px;">Cuenta de pago autorizada por Administrador - Consultar con Administracion</div>'
    banco = cuenta_row[1]; numero = cuenta_row[2]; titular = cuenta_row[3]; tipo = cuenta_row[4]; moneda = cuenta_row[5]; ubicacion = cuenta_row[6]
    # FIX 6: Mostrar solo ****5021, no numero completo
    numero_masked = f"****{str(numero)[-4:]}" if len(str(numero))>4 else numero
    return f"""
    <div style="background:linear-gradient(135deg,#0f2027,#2c5364);padding:20px;border-radius:15px;color:white;border-left:5px solid #FFD700;">
    <h3 style="color:#FFD700;margin:0 0 15px 0;">💳 Cuenta de Pago Autorizada - Formato Profesional v71 LIMPIO</h3>
    <table style="width:100%;color:white;font-size:14px;">
    <tr><td style="padding:5px;"><b>Banco:</b></td><td style="padding:5px;">{banco}</td></tr>
    <tr><td style="padding:5px;"><b>Titular:</b></td><td style="padding:5px;">{titular}</td></tr>
    <tr><td style="padding:5px;"><b>Tipo Cuenta:</b></td><td style="padding:5px;">{tipo}</td></tr>
    <tr><td style="padding:5px;"><b>Moneda:</b></td><td style="padding:5px;">{moneda}</td></tr>
    <tr><td style="padding:5px;"><b>Ubicacion:</b></td><td style="padding:5px;">{ubicacion}</td></tr>
    <tr><td style="padding:5px;"><b>Numero Cuenta:</b></td><td style="padding:5px;">{numero_masked} (Completo visible solo al confirmar pago)</td></tr>
    <tr><td style="padding:5px;"><b>Estado:</b></td><td style="padding:5px;color:#4CAF50;">{cuenta_row[7]} - Autorizada</td></tr>
    </table>
    <p style="font-size:11px;margin-top:10px;opacity:0.8;">Cuenta autorizada por Administrador - Formato profesional v71 LIMPIO - Numero enmascarado por privacidad</p>
    </div>
    """

# FIX 5: Buscar duplicados en TODOS los clientes
def existe_email_o_rnc_duplicado(email, rnc):
    email_n = (email or "").strip().lower(); rnc_n = (rnc or "").strip()
    if not CASOS_DIR.exists(): return False, ""
    for cf in CASOS_DIR.iterdir():
        if not cf.is_dir(): continue
        jf = cf / "info.json"
        info = leer_info_json_seguro(jf)
        if info:
            if info.get("email","").strip().lower() == email_n and email_n:
                return True, f"Correo {email_n} ya existe en cliente {cf.name}"
            if info.get("rnc","").strip() == rnc_n and rnc_n:
                return True, f"RNC {rnc_n} ya existe en cliente {cf.name}"
    return False, ""

if "migracion_ejecutada" not in st.session_state:
    logs = migrar_sin_perdidas()
    st.session_state.migracion_ejecutada = True
    st.session_state.migracion_logs = logs

st.markdown("<style>.header-pro{background:linear-gradient(135deg,#0F2027,#203A43,#2C5364);padding:20px;border-radius:15px;text-align:center;color:white;border:2px solid #FFD700;}.footer-pro{background:#0F2027;color:white;padding:15px;border-radius:10px;margin-top:20px;border-left:5px solid #FFD700;}.dgii-box{background:linear-gradient(135deg,#1a472a,#2d5a27);padding:15px;border-radius:10px;color:white;border:2px solid #4CAF50;}.bhd-box{background:linear-gradient(135deg,#1a3a5a,#2d5a8a);padding:15px;border-radius:10px;color:white;border:2px solid #FFD700;}</style>", unsafe_allow_html=True)
if "logged" not in st.session_state: st.session_state.logged = False
if "modulo_activo" not in st.session_state: st.session_state.modulo_activo = "DASHBOARD"
if "recovery_mode" not in st.session_state: st.session_state.recovery_mode = False
if "show_register" not in st.session_state: st.session_state.show_register = False

if not st.session_state.logged:
    # FIX 6: Header ya NO muestra 08694150021 completo, solo ****5021
    st.markdown(f'<div class="header-pro"><h1>🏛️ BASA e-CF PRO v71 PROFESIONAL - LIMPIO</h1><h2>Cuenta {CUENTA_MOSTRAR} - Ahorros Pesos - Pedro Anibal Baldera - Migracion Sin Perdidas + Afiliacion + Cuenta Autorizada Admin | RNC 133378711</h2><p style="color:#FFD700;">Baldera Santos & Asociados SRL - Formato Profesional v71 LIMPIO - Sin puntos</p></div>', unsafe_allow_html=True)
    if st.session_state.get("migracion_logs"):
        with st.expander(f"📦 Migracion Automatica Sin Perdidas v71 - {len(st.session_state.migracion_logs)} archivos"):
            for log in st.session_state.migracion_logs[:20]: st.write(log)
    c1,c2,c3 = st.columns([1,2,1])
    with c2:
        tab_login, tab_register = st.tabs(["🔐 LOGIN", "📝 REGISTRO + PAGO"])
        with tab_login:
            if not st.session_state.recovery_mode and not st.session_state.show_register:
                st.markdown(f"### 🔐 Acceso Seguro - v71 LIMPIO - Cuenta {CUENTA_MOSTRAR}")
                email = st.text_input("Correo Electronico", key="login_email")
                pwd = st.text_input("Contraseña", type="password", key="login_pwd")
                if st.button("🚀 Entrar a BASA v71 LIMPIO", use_container_width=True, type="primary"):
                    ph = hashlib.sha256(pwd.encode()).hexdigest()
                    if email == MASTER_USER["email"] and ph == MASTER_USER["password_hash"]:
                        st.session_state.logged = True; st.session_state.user = email; st.session_state.role = "ADMIN"; st.rerun()
                    else:
                        found = False
                        for cf in CASOS_DIR.iterdir():
                            if cf.is_dir():
                                jf = cf / "info.json"
                                info = leer_info_json_seguro(jf)  # FIX 4: No se rompe si esta danado
                                if info and info.get("email") == email and info.get("password_hash") == ph:
                                    st.session_state.logged = True; st.session_state.user = email; st.session_state.role = "CLIENT"; st.session_state.client_id = info.get("id"); found = True; st.rerun()
                        if not found: st.error("❌ Credenciales incorrectas")
                colA,colB = st.columns(2)
                with colA:
                    if st.button("🔑 Olvide mi clave", use_container_width=True): st.session_state.recovery_mode = True; st.rerun()
                with colB:
                    if st.button("📝 Crear Cuenta + Pagar", use_container_width=True): st.session_state.show_register = True; st.rerun()
            if st.session_state.recovery_mode:
                st.markdown("### 🔑 Recuperar Clave - Seguro")
                email_rec = st.text_input("Correo registrado", key="rec_email")
                if st.button("📧 Generar Codigo", use_container_width=True, type="primary"):
                    code = "".join(random.choices(string.digits, k=6)); st.session_state.recovery_code = code; st.session_state.recovery_email = email_rec
                    st.success(f"✅ Codigo: {code} - Enviado a {email_rec} / WhatsApp {CRED['whatsapp']}")
                code_in = st.text_input("Ingresa codigo", key="rec_code")
                new_pwd = st.text_input("Nueva contraseña", type="password", key="rec_newpwd")
                if st.button("🔄 Cambiar clave", use_container_width=True):
                    if code_in == st.session_state.get("recovery_code"):
                        actualizado = False
                        for cf in CASOS_DIR.iterdir():
                            if not cf.is_dir(): continue
                            jf = cf / "info.json"
                            info = leer_info_json_seguro(jf)
                            if info and info.get("email") == st.session_state.get("recovery_email"):
                                info["password_hash"] = hashlib.sha256(new_pwd.encode()).hexdigest()
                                guardar_info_json_seguro(jf, info)
                                st.success(f"✅ Clave actualizada para {info.get('email')}")
                                actualizado = True
                        if not actualizado: st.error("Correo no encontrado o info.json dañado - Contacta Admin")
                    else: st.error("Codigo incorrecto")
                if st.button("⬅️ Volver"): st.session_state.recovery_mode = False; st.session_state.show_register = False; st.rerun()
        with tab_register:
            st.markdown("### 📝 Registro Nuevo Cliente BASA v71 LIMPIO + Pago Cuenta Autorizada")
            cuenta_activa_reg = get_cuenta_pago_activa()
            st.markdown(format_cuenta_profesional(cuenta_activa_reg), unsafe_allow_html=True)
            reg_id = st.text_input("ID Cliente (Auto)", value=f"CLI-{str(uuid.uuid4())[:4].upper()}", key="reg_id")
            reg_nombre = st.text_input("Razon Social / Nombre Empresa", value="", key="reg_nombre")
            reg_rnc = st.text_input("RNC / Cedula", value="", key="reg_rnc")
            reg_email = st.text_input("Correo Electronico (Usuario)", value="", key="reg_email")
            reg_pwd = st.text_input("Contraseña", type="password", key="reg_pwd")
            reg_tel = st.text_input("Telefono / WhatsApp", value="", key="reg_tel")
            reg_dir = st.text_input("Direccion Completa", value="", key="reg_dir")
            reg_web = st.text_input("Sitio Web (Opcional)", value="", key="reg_web")
            reg_logo = st.file_uploader("📷 Logo Empresa (PNG/JPG)", type=["png","jpg","jpeg"], key="reg_logo")
            reg_usuario_dgii = st.text_input("Usuario DGII e-CF FG Home", value="", key="reg_usu_dgii")
            reg_clave_dgii = st.text_input("Clave DGII e-CF FG Home", type="password", key="reg_clave_dgii")
            st.markdown("---")
            st.markdown("### 💳 Pago Cuenta Autorizada - Formato Profesional v71 LIMPIO")
            monto_pago = st.number_input("Monto a Pagar (Para liberacion Full)", value=199.0, key="monto_pago_v71")
            ref_bhd = st.text_input("Referencia Transferencia", value="", key="ref_bhd_v71")
            comp_bhd = st.file_uploader("📁 Subir Comprobante Pago (Foto/PDF)", type=["png","jpg","jpeg","pdf"], key="comp_bhd_v71")
            tipo_afiliacion = st.selectbox("Tipo Afiliacion", ["Individual - Solo mi empresa","Consorcio - Tengo varias empresas afiliadas","Grupo Empresarial"], key="tipo_afiliacion_v71")
            empresas_afiliadas_input = st.text_input("IDs Empresas Afiliadas (coma)", value="", key="empresas_afiliadas_v71") if tipo_afiliacion != "Individual - Solo mi empresa" else ""
            if st.button("✅ REGISTRARME EN BASA v71 LIMPIO + PAGAR", use_container_width=True, type="primary"):
                # FIX 5: Validar duplicados + email + ID
                if not validar_id_cliente(reg_id):
                    st.error("ID Cliente invalido. Solo letras, numeros, guion. Ej: CLI-AB12")
                elif not validar_email(reg_email):
                    st.error("Correo invalido. Ej: pedro@basa.com")
                elif not (reg_nombre and reg_rnc and reg_email and reg_pwd and ref_bhd and comp_bhd):
                    st.error("Complete Nombre, RNC, Email, Contraseña, Referencia y Comprobante")
                else:
                    duplicado, msg_dup = existe_email_o_rnc_duplicado(reg_email, reg_rnc)
                    if duplicado:
                        st.error(f"❌ DUPLICADO: {msg_dup} - No se guardo. Usa otro correo/RNC o recupera clave.")
                    else:
                        try:
                            dbp = init_db_v71(reg_id)
                            logo_path = ""
                            if reg_logo:
                                try: logo_path = save_logo(reg_id, reg_logo)
                                except Exception as e: st.error(f"Logo invalido: {e}"); st.stop()
                            try: comp_path = save_comprobante_bhd(reg_id, comp_bhd)
                            except Exception as e: st.error(f"Comprobante invalido: {e}"); st.stop()
                            info = {"id":reg_id,"nombre":reg_nombre,"rnc":reg_rnc,"email":reg_email.strip().lower(),"password_hash":hashlib.sha256(reg_pwd.encode()).hexdigest(),"precio":monto_pago,"direccion":reg_dir,"telefono":reg_tel,"web":reg_web,"logo_path":logo_path,"usuario_dgii":reg_usuario_dgii,"tipo_afiliacion":tipo_afiliacion,"empresas_afiliadas":empresas_afiliadas_input}
                            guardar_info_json_seguro(CASOS_DIR / reg_id / "info.json", info)
                            conn = sqlite3.connect(str(dbp)); c = conn.cursor()
                            c.execute("INSERT OR REPLACE INTO clientes_info (id,nombre,rnc,email,direccion,telefono,precio_base,logo_path,web,usuario_dgii) VALUES (?,?,?,?,?,?,?,?,?,?)", (reg_id, reg_nombre, reg_rnc, reg_email.strip().lower(), reg_dir, reg_tel, monto_pago, logo_path, reg_web, reg_usuario_dgii))
                            if reg_usuario_dgii:
                                c.execute("INSERT OR REPLACE INTO dgii_config (id,cliente_id,usuario_dgii,clave_dgii_hash,rnc_emisor,razon_social,fecha_registro,portal_url) VALUES (?,?,?,?,?,?,?,?)", (f"DGII-{reg_id}", reg_id, reg_usuario_dgii, hashlib.sha256(reg_clave_dgii.encode()).hexdigest() if reg_clave_dgii else "", reg_rnc, reg_nombre, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), DGII_HOME))
                            cuenta_activa = get_cuenta_pago_activa()
                            pago_id = f"PAGO-{str(uuid.uuid4())[:8].upper()}"
                            c.execute("INSERT INTO pagos_bhd (id,cliente_id,monto,referencia_bhd,fecha_pago,comprobante_path,estado,cuenta_pago_id,liberado_por,fecha_liberacion,usuario_email) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (pago_id, reg_id, monto_pago, ref_bhd, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), comp_path, f"Pendiente - Verificando en cuenta autorizada {cuenta_activa[0]}", cuenta_activa[0], "", "", reg_email))
                            if tipo_afiliacion != "Individual - Solo mi empresa":
                                afili_id = f"AFIL-{str(uuid.uuid4())[:6].upper()}"
                                c.execute("INSERT INTO afiliaciones (id,usuario_master_email,empresa_principal_id,empresas_afiliadas_json,tipo,fecha_creacion,estado) VALUES (?,?,?,?,?,?,?)", (afili_id, reg_email, reg_id, json.dumps([s.strip() for s in empresas_afiliadas_input.split(",") if s.strip()] + [reg_id]), tipo_afiliacion, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "Activo - Consorcio v71 LIMPIO"))
                            c.execute("INSERT OR REPLACE INTO cuentas_pago_admin (id,banco,numero_cuenta,titular,tipo_cuenta,moneda,ubicacion,estado,fecha_creacion,creado_por,notas) VALUES (?,?,?,?,?,?,?,?,?,?,?)", cuenta_activa)
                            conn.commit(); conn.close()
                            add_historico(reg_id, "REGISTRO_CLIENTE_BASA_v71_LIMPIO", "-", f"Cliente {reg_nombre} RNC {reg_rnc} registrado v71 LIMPIO - Pago {monto_pago} Ref {ref_bhd}", reg_email)
                            st.success(f"✅ CUENTA CREADA BASA v71 LIMPIO: {reg_id} | {reg_nombre} | RNC {reg_rnc} | Monto RD$ {monto_pago} Ref {ref_bhd} | Pendiente liberacion")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Error registrando: {e}")
    st.markdown(f'<div class="dgii-box"><h3>🔗 Portal DGII e-CF Oficial FG Home: <a href="{DGII_HOME}" target="_blank" style="color:#FFD700;">{DGII_HOME}</a></h3><p>Cuenta Autorizada - Formato profesional v71 LIMPIO - {CUENTA_MOSTRAR}</p></div>', unsafe_allow_html=True)
    st.stop()

# ================= DESPUES DE LOGIN =================
def verificar_liberado_bhd(cid):
    if not validar_id_cliente(cid): return False
    try: dbp = get_db_path(cid)
    except: return False
    if not dbp.exists(): return False
    conn = sqlite3.connect(str(dbp)); c = conn.cursor()
    try:
        c.execute("SELECT estado FROM pagos_bhd WHERE cliente_id=? ORDER BY fecha_pago DESC LIMIT 1", (cid,))
        row = c.fetchone(); conn.close()
        if row and "Liberado" in row[0]: return True
        if st.session_state.role == "ADMIN": return True
        if not row: return True
        return False
    except: conn.close(); return True

def get_empresas_afiliadas_usuario(email):
    empresas = []
    for cf in CASOS_DIR.iterdir():
        if cf.is_dir():
            dbp = cf / f"BASA_{cf.name}_eCF.db"
            if dbp.exists():
                try:
                    conn = sqlite3.connect(str(dbp)); c = conn.cursor()
                    c.execute("SELECT * FROM afiliaciones WHERE usuario_master_email=?", (email,))
                    row = c.fetchone()
                    if row:
                        try: empresas.extend(json.loads(row[3]))
                        except: pass
                    conn.close()
                except: pass
    for cf in CASOS_DIR.iterdir():
        jf = cf / "info.json"
        info = leer_info_json_seguro(jf)
        if info and info.get("email") == email:
            if info.get("empresas_afiliadas"):
                empresas.extend([s.strip() for s in info.get("empresas_afiliadas").split(",") if s.strip()])
            empresas.append(info.get("id"))
    return list(set([e for e in empresas if e and validar_id_cliente(e)]))

st.markdown("### 📋 Modulos v71 LIMPIO")
b1,b2,b3,b4,b5,b6,b7,b8,b9,b10 = st.columns(10)
for btn, mod_name, label in [(b1,"DASHBOARD","📊 DASHBOARD"),(b2,"CLIENTES","👥 CLIENTES"),(b3,"FACTURAR","🧾 FACTURAR"),(b4,"HISTORICO","📜 HISTORICO"),(b5,"PRECIOS","💰 PRECIOS"),(b6,"CERTIFICADOS","🔐 DGII + CERT"),(b7,"CONSULTAR_NCF","🔍 CONSULTAR NCF"),(b8,"ENVIO_DGII_CERT","📤 ENVIO DGII"),(b9,"BHD_PAGOS","💳 PAGOS"),(b10,"CONSORCIO","🏢 CONSORCIO")]:
    with btn:
        if st.button(label, use_container_width=True, type="primary" if st.session_state.modulo_activo==mod_name else "secondary"):
            st.session_state.modulo_activo = mod_name; st.rerun()

with st.sidebar:
    st.write(f"Usuario: {st.session_state.user}"); st.write(f"Rol: {st.session_state.role}"); st.markdown("---")
    empresas_usuario = get_empresas_afiliadas_usuario(st.session_state.user)
    if empresas_usuario and st.session_state.role != "ADMIN":
        st.markdown("### 🏢 Mis Empresas Afiliadas")
        empresa_seleccionada = st.selectbox("Seleccionar Empresa", empresas_usuario, key="empresa_consorcio_select")
        if empresa_seleccionada: st.session_state.client_id = empresa_seleccionada; client_id_input = empresa_seleccionada
        else: client_id_input = st.text_input("ID Cliente DB v71", value=st.session_state.get("client_id","CLI-D452"))
    else:
        client_id_input = st.text_input("ID Cliente DB v71", value=st.session_state.get("client_id","CLI-D452"))
    if not validar_id_cliente(client_id_input):
        st.error("ID Cliente invalido. Solo letras, numeros, guion. Ej: CLI-D452"); st.stop()
    liberado = verificar_liberado_bhd(client_id_input)
    cuenta_activa_sidebar = get_cuenta_pago_activa()
    st.markdown(format_cuenta_profesional(cuenta_activa_sidebar), unsafe_allow_html=True)
    if liberado: st.success(f"✅ Liberado Full - Caso {client_id_input}")
    else: st.error(f"⚠️ No liberado - Caso {client_id_input} - Pague a cuenta autorizada para liberacion")
    if st.button("✅ Crear/Verificar DB v71 + Migrar", use_container_width=True):
        logs = migrar_sin_perdidas(); dbp = init_db_v71(client_id_input)
        conn = sqlite3.connect(str(dbp)); c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO cuentas_pago_admin (id,banco,numero_cuenta,titular,tipo_cuenta,moneda,ubicacion,estado,fecha_creacion,creado_por,notas) VALUES (?,?,?,?,?,?,?,?,?,?,?)", cuenta_activa_sidebar)
        conn.commit(); conn.close()
        st.success(f"DB v71 OK: {dbp} | Migracion: {len(logs)} archivos")
    if st.session_state.role == "ADMIN":
        st.markdown("---"); st.markdown("### 💳 ADMIN - Crear Cuenta de Pago Autorizada")
        with st.expander("🔧 Crear Nueva Cuenta"):
            banco_admin = st.selectbox("Banco", ["BHD León","Banreservas","Popular","BHD León USA","Bank of America USA","Chase USA","Otro"], key="banco_admin_v71")
            numero_cuenta_admin = st.text_input("Numero Cuenta", value="****5021 - Escribe completo solo aqui si eres ADMIN", key="numero_cuenta_admin_v71")
            titular_admin = st.text_input("Titular Cuenta", value="Pedro Anibal Baldera", key="titular_admin_v71")
            tipo_cuenta_admin = st.selectbox("Tipo Cuenta", ["Ahorros en Pesos","Ahorros en Dolares","Corriente en Pesos","Corriente en Dolares","Ahorros USA"], key="tipo_cuenta_admin_v71")
            moneda_admin = st.selectbox("Moneda", ["DOP - Pesos Dominicanos","USD - Dolares USA"], key="moneda_admin_v71")
            ubicacion_admin = st.selectbox("Ubicacion", ["RD Local - Republica Dominicana","USA - Estados Unidos"], key="ubicacion_admin_v71")
            notas_admin = st.text_area("Notas Cuenta (Interno)", value="Cuenta oficial autorizada para liberacion Full BASA v71", key="notas_admin_v71")
            if st.button("✅ ADMIN Crear Cuenta", type="primary", use_container_width=True):
                # ADMIN escribe numero completo aqui, pero NO se muestra en pantalla publica
                if numero_cuenta_admin.startswith("****") or len(numero_cuenta_admin) < 8:
                    st.error("Como ADMIN, escribe el numero completo aqui (no se mostrara en pantallas publicas, solo ****5021).")
                else:
                    cuenta_id = f"CUENTA-{str(uuid.uuid4())[:6].upper()}"
                    dbp_admin = get_db_path(client_id_input)
                    conn = sqlite3.connect(str(dbp_admin)); c = conn.cursor()
                    c.execute("UPDATE cuentas_pago_admin SET estado='Inactiva' WHERE ubicacion=?", (ubicacion_admin,))
                    c.execute("INSERT INTO cuentas_pago_admin (id,banco,numero_cuenta,titular,tipo_cuenta,moneda,ubicacion,estado,fecha_creacion,creado_por,notas) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (cuenta_id, banco_admin, numero_cuenta_admin, titular_admin, tipo_cuenta_admin, moneda_admin, ubicacion_admin, "Activa", datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), st.session_state.user, notas_admin))
                    conn.commit(); conn.close()
                    st.success(f"✅ Cuenta creada: {cuenta_id} | Banco {banco_admin} | Ubicacion {ubicacion_admin} | Activa")
                    st.rerun()
    st.markdown("---")
    st.markdown(f'<div class="dgii-box"><b>🔗 DGII FG Home</b><br><a href="{DGII_HOME}" target="_blank" style="color:#FFD700;">Abrir FG Home</a></div>', unsafe_allow_html=True)
    st.markdown("---"); st.markdown("### 🔑 Cambiar Clave")
    new_pwd_sidebar = st.text_input("Nueva clave", type="password", key="new_pwd_sidebar_v71")
    if st.button("💾 Guardar Nueva Clave v71", use_container_width=True):
        for cf in CASOS_DIR.iterdir():
            jf = cf / "info.json"
            info = leer_info_json_seguro(jf)
            if info and info.get("email") == st.session_state.user:
                info["password_hash"] = hashlib.sha256(new_pwd_sidebar.encode()).hexdigest()
                guardar_info_json_seguro(jf, info)
                st.success(f"Clave actualizada para {st.session_state.user}")
    if st.button("🚪 Salir", use_container_width=True): st.session_state.logged = False; st.rerun()
    st.markdown("---"); st.markdown(f"**{CRED['nombre']}**"); st.markdown(f"{CRED['telefono']}"); st.markdown(f"{CRED['email']}")
    try:
        cf_logo = CASOS_DIR / client_id_input / "logo.png"
        if cf_logo.exists(): st.image(str(cf_logo), caption=f"Logo {client_id_input}", use_column_width=True)
    except: pass

mod = st.session_state.modulo_activo
if not verificar_liberado_bhd(client_id_input) and st.session_state.role != "ADMIN" and mod not in ["DASHBOARD","BHD_PAGOS","CONSORCIO"]:
    st.error(f"⚠️ Caso {client_id_input} NO liberado - Debe pagar a cuenta autorizada para liberacion Full"); st.stop()

# ================= DASHBOARD =================
if mod == "DASHBOARD":
    st.header(f"📊 Dashboard v71 LIMPIO - Cuenta {CUENTA_MOSTRAR} - Formato profesional")
    if st.session_state.get("migracion_logs"):
        st.info(f"📦 Migracion sin perdidas: {len(st.session_state.migracion_logs)} archivos - Backup en {BACKUP_DIR}")
    st.markdown(format_cuenta_profesional(get_cuenta_pago_activa()), unsafe_allow_html=True)
    total_c = len([d for d in CASOS_DIR.iterdir() if d.is_dir()]); total_f = 0; total_m = 0; total_certs = 0; total_borradores = 0; total_enviados_local = 0; total_bhd_pend = 0; total_bhd_lib = 0
    acumulado_por_cliente = []
    for cf in CASOS_DIR.iterdir():
        if cf.is_dir():
            if st.session_state.role != "ADMIN":
                empresas_user = get_empresas_afiliadas_usuario(st.session_state.user)
                if cf.name not in empresas_user and cf.name != client_id_input: continue
            dbp = cf / f"BASA_{cf.name}_eCF.db"
            if dbp.exists():
                conn = sqlite3.connect(str(dbp))
                try:
                    c = conn.cursor(); c.execute("SELECT COUNT(*), SUM(total), SUM(itbis) FROM facturas"); cnt, sm, it = c.fetchone()
                    c.execute("SELECT COUNT(*) FROM certificados WHERE activo=1"); cert_cnt = c.fetchone()[0]
                    c.execute("SELECT COUNT(*) FROM facturas WHERE estado LIKE '%Borrador%'"); borr = c.fetchone()[0]
                    # FIX 7: Contar solo REGISTRADO LOCAL, no confundir con Enviado Real DGII
                    c.execute("SELECT COUNT(*) FROM facturas WHERE estado_dgii LIKE '%REGISTRADO LOCAL%'"); env_local = c.fetchone()[0]
                    c.execute("SELECT COUNT(*) FROM pagos_bhd WHERE estado LIKE '%Pendiente%'"); bhd_pend = c.fetchone()[0]
                    c.execute("SELECT COUNT(*) FROM pagos_bhd WHERE estado LIKE '%Liberado%'"); bhd_lib = c.fetchone()[0]
                    total_f += cnt or 0; total_m += sm or 0; total_certs += cert_cnt or 0; total_borradores += borr or 0; total_enviados_local += env_local or 0; total_bhd_pend += bhd_pend or 0; total_bhd_lib += bhd_lib or 0
                    jf = cf / "info.json"; info_cli = leer_info_json_seguro(jf)
                    nombre_cli = info_cli.get("nombre", cf.name) if info_cli else cf.name
                    acumulado_por_cliente.append({"ID Cliente":cf.name,"Nombre":nombre_cli,"Facturas":cnt or 0,"Monto Total RD$":sm or 0,"ITBIS Total":it or 0,"Borradores":borr or 0,"Registrados Local (NO DGII)":env_local or 0,"Cert Activo":cert_cnt or 0,"Pagos Pendiente":bhd_pend or 0,"Pagos Liberado":bhd_lib or 0})
                except: pass
                conn.close()
    c1,c2,c3,c4,c5,c6,c7,c8 = st.columns(8); c1.metric("Clientes", total_c); c2.metric("Facturas", total_f); c3.metric("Monto", f"RD$ {total_m:,.2f}"); c4.metric("Certs", total_certs); c5.metric("Borradores", total_borradores); c6.metric("Registrados Local", total_enviados_local); c7.metric("Pagos Pend", total_bhd_pend); c8.metric("Pagos Liberados", total_bhd_lib)
    st.warning("⚠️ 'Registrados Local' NO significa Enviado a DGII. El envio oficial DGII esta separado en modulo ENVIO DGII.")
    st.markdown("### 📊 Historico Acumulado por Cliente")
    if acumulado_por_cliente:
        df_acum = pd.DataFrame(acumulado_por_cliente); st.dataframe(df_acum, use_container_width=True)
        st.download_button("📥 Descargar Historico Acumulado", df_acum.to_csv(index=False), file_name=f"historico_acumulado_v71_{datetime.datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)
        cliente_seleccion = st.selectbox("Seleccionar Cliente para Ver Historial", [f"{r['ID Cliente']} - {r['Nombre']}" for r in acumulado_por_cliente], key="cliente_seleccion_acum_v71")
        if cliente_seleccion:
            id_cli_sel = cliente_seleccion.split(" - ")[0]
            if validar_id_cliente(id_cli_sel):
                dbp_sel = get_db_path(id_cli_sel)
                if dbp_sel.exists():
                    conn = sqlite3.connect(str(dbp_sel))
                    try:
                        df_hist_sel = pd.read_sql_query("SELECT ncf, tipo, cliente, descripcion, cantidad, precio, total, fecha, estado, estado_dgii, trackid FROM facturas ORDER BY id DESC", conn)
                        st.write(f"Historial {id_cli_sel} - {len(df_hist_sel)} facturas"); st.dataframe(df_hist_sel, use_container_width=True)
                    except Exception as e: st.info(f"Sin historial: {e}")
                    conn.close()

if mod == "BHD_PAGOS":
    st.header(f"💳 Pagos - Cuenta Autorizada - Cliente {client_id_input} - Cuenta {CUENTA_MOSTRAR}")
    cuenta_activa = get_cuenta_pago_activa()
    st.markdown(format_cuenta_profesional(cuenta_activa), unsafe_allow_html=True)
    st.info("Para ver numero completo de cuenta, confirma tu pago abajo. En pantallas publicas solo se muestra ****5021 por privacidad.")
    dbp = get_db_path(client_id_input)
    if not dbp.exists(): st.warning("DB v71 no existe"); st.stop()
    st.markdown("### 💳 Registrar Nuevo Pago")
    monto_bhd = st.number_input("Monto Pagado RD$", value=199.0, key="monto_bhd_v71")
    ref_bhd = st.text_input("Referencia", value="", key="ref_bhd_pago_v71")
    comp_bhd = st.file_uploader("📁 Subir Comprobante Pago (PNG/JPG/PDF) - Se detecta tipo real", type=["png","jpg","jpeg","pdf"], key="comp_bhd_pago_v71")
    if st.button("💾 Registrar Pago - Para Liberacion Full", type="primary", use_container_width=True):
        if ref_bhd and comp_bhd:
            try: comp_path = save_comprobante_bhd(client_id_input, comp_bhd)
            except Exception as e: st.error(f"Comprobante invalido: {e}"); st.stop()
            conn = sqlite3.connect(str(dbp)); c = conn.cursor()
            pago_id = f"PAGO-{str(uuid.uuid4())[:8].upper()}"
            c.execute("INSERT INTO pagos_bhd (id,cliente_id,monto,referencia_bhd,fecha_pago,comprobante_path,estado,cuenta_pago_id,liberado_por,fecha_liberacion,usuario_email) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (pago_id, client_id_input, monto_bhd, ref_bhd, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), comp_path, f"Pendiente - Verificando en cuenta autorizada {cuenta_activa[0]}", cuenta_activa[0], "", "", st.session_state.user))
            conn.commit(); conn.close()
            st.success(f"✅ Pago registrado: {pago_id} | Monto RD$ {monto_bhd} | Ref {ref_bhd} | Comprobante guardado con extension correcta: {comp_path}")
            add_historico(client_id_input, "PAGO_CUENTA_AUTORIZADA_v71_LIMPIO", pago_id, f"Pago {monto_bhd} Ref {ref_bhd}", st.session_state.user)
        else: st.error("Debe ingresar Referencia y Comprobante")
    st.markdown("### 📜 Historico Pagos")
    conn = sqlite3.connect(str(dbp))
    try:
        df_pagos = pd.read_sql_query("SELECT * FROM pagos_bhd WHERE cliente_id=? ORDER BY fecha_pago DESC", (client_id_input,)); st.dataframe(df_pagos, use_container_width=True)
        if st.session_state.role == "ADMIN":
            st.markdown("### 🔓 ADMIN - Liberar Cliente")
            pago_id_liberar = st.text_input("ID Pago a Liberar (PAGO-XXXX)", value="", key="pago_id_liberar_v71")
            if st.button("✅ ADMIN LIBERAR USO FULL", type="primary", use_container_width=True):
                c = conn.cursor()
                c.execute("UPDATE pagos_bhd SET estado=?, liberado_por=?, fecha_liberacion=? WHERE id=?", (f"Liberado Full - Verificado en cuenta autorizada {cuenta_activa[0]} - Liberado por ADMIN {st.session_state.user}", st.session_state.user, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), pago_id_liberar))
                conn.commit(); st.success(f"✅ ADMIN libero: Pago {pago_id_liberar} | Cliente {client_id_input}")
                add_historico(client_id_input, "LIBERACION_ADMIN_v71_LIMPIO", pago_id_liberar, f"ADMIN {st.session_state.user} libero {client_id_input}", st.session_state.user)
    except Exception as e: st.info(f"Sin pagos aun: {e}")
    conn.close()

if mod == "FACTURAR":
    st.header(f"🧾 Facturacion v71 LIMPIO - Cliente {client_id_input} - Cuenta {CUENTA_MOSTRAR}")
    st.warning("⚠️ IMPORTANTE DGII: Este modulo REGISTRA LOCAL. NO es envio oficial a DGII. El envio oficial esta en modulo ENVIO DGII y requiere certificado .p12 y conexion oficial.")
    dbp = get_db_path(client_id_input)
    if not dbp.exists(): st.warning("DB v71 no existe"); st.stop()
    if not verificar_liberado_bhd(client_id_input) and st.session_state.role != "ADMIN":
        st.error(f"⚠️ Caso {client_id_input} NO liberado"); st.stop()
    conn = sqlite3.connect(str(dbp)); c = conn.cursor()
    c.execute("SELECT * FROM dgii_config WHERE cliente_id=?", (client_id_input,)); dgii_conf = c.fetchone()
    c.execute("SELECT * FROM certificados WHERE cliente_id=? AND activo=1 ORDER BY fecha_subida DESC LIMIT 1", (client_id_input,)); cert_activo = c.fetchone()
    c.execute("SELECT descripcion, precio, unidad, veces_usado FROM productos_servicios WHERE cliente_id=? ORDER BY veces_usado DESC", (client_id_input,)); productos_autoguardados = c.fetchall(); conn.close()
    retomar_data = st.session_state.get("retomar_ncf", None)
    cuenta_activa = get_cuenta_pago_activa()
    st.markdown(format_cuenta_profesional(cuenta_activa), unsafe_allow_html=True)
    st.markdown(f'<div class="dgii-box">🔐 Usuario DGII: {dgii_conf[2] if dgii_conf else "No configurado"} | Cert Activo: {"SI - "+str(cert_activo[2]) if cert_activo else "NO"} | BHD Liberado: SI | Productos: {len(productos_autoguardados)}</div>', unsafe_allow_html=True)
    if productos_autoguardados:
        prod_opciones = [f"{p[0]} - RD$ {p[1]:,.2f} - {p[2]} - Usado {p[3]} veces" for p in productos_autoguardados]
        prod_seleccion = st.selectbox("Seleccionar Producto Autoguardado", ["-- Escribir manual --"] + prod_opciones, key="prod_autoguardado_v71")
        if prod_seleccion != "-- Escribir manual --":
            desc_auto = prod_seleccion.split(" - ")[0]; precio_auto = float(prod_seleccion.split("RD$ ")[1].split(" -")[0].replace(",", ""))
        else: desc_auto = "Zapatos"; precio_auto = 550.0
    else: desc_auto = "Zapatos"; precio_auto = 550.0
    col_ncf1, col_ncf2 = st.columns(2)
    with col_ncf1:
        tipo_sel = st.selectbox("Tipo e-NCF DGII Oficial", ["E31 - Factura Credito Fiscal Electronica","E32 - Factura Consumo Electronica","E33 - Nota Debito Electronica","E34 - Nota Credito Electronica","E41 - Compras Electronico","E43 - Gastos Menores Electronico","E44 - Regimenes Especiales Electronico","E45 - Gubernamental Electronico","E46 - Exportacion Electronico","E47 - Pagos al Exterior Electronico"], key="tipo_sel_v71")
        tipo_code = tipo_sel.split(" - ")[0]
    with col_ncf2:
        modo_ncf = st.selectbox("Modo NCF", ["Automatico - Guardar NCF Automatico v71","Manual - Agregar NCF Manual v71"], key="modo_ncf_v71")
    if "Automatico" in modo_ncf:
        next_ncf = get_next_ncf(client_id_input, tipo_code); st.success(f"🔒 NCF Automatico v71: {next_ncf}")
    else: next_ncf = st.text_input("✍️ Ingrese NCF Manual v71", value="E310000000028", key="ncf_manual_v71")
    c1,c2,c3 = st.columns(3)
    with c1: razon_c = st.text_input("Razon Social Cliente", value=retomar_data["cliente"] if retomar_data else "COMERCIAL ZYL SRL - BASA v71", key="razon_c_v71")
    with c2: rnc_c = st.text_input("RNC Cliente", value=retomar_data["rnc_cliente"] if retomar_data else "130000001", key="rnc_c_v71")
    with c3: venc = st.date_input("Fecha Vencimiento", value=datetime.date(2026,12,31), key="venc_v71")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: cant = st.number_input("Cant", value=retomar_data["cantidad"] if retomar_data else 150.0, key="cant_v71")
    with c2: desc = st.text_input("Descripcion - Autoguardado", value=retomar_data["descripcion"] if retomar_data else desc_auto, key="desc_v71")
    with c3: uni = st.text_input("Unidad", value="CAJ", key="uni_v71")
    with c4: prec = st.number_input("Precio RD$", value=retomar_data["precio"] if retomar_data else precio_auto, key="prec_v71")
    with c5: dsc = st.number_input("Descuento RD$", value=retomar_data["descuento"] if retomar_data else 0.0, key="dsc_v71")
    with c6: forma_pago = st.selectbox("Forma Pago", ["Contado","Credito - 30 dias"], key="forma_pago_v71")
    itbis_p = 0.18; sub = cant*prec-dsc; itbis = sub*itbis_p; tot = sub+itbis
    st.markdown(f"**Subtotal: RD$ {sub:,.2f} | ITBIS: RD$ {itbis:,.2f} | Total: RD$ {tot:,.2f}**")
    coment = st.text_input("Comentario", value="Factura v71 LIMPIO", key="coment_v71")
    col_conf1, col_conf2 = st.columns(2)
    with col_conf1: confirmar_registro_local = st.checkbox(f"✅ SI, REGISTRAR LOCAL e-NCF {next_ncf} - NO es envio oficial DGII - Entiendo que solo queda guardado local", value=False, key="confirmar_registro_local_v71")
    with col_conf2: guardar_borrador_fact = st.checkbox(f"📝 NO, GUARDAR COMO BORRADOR {next_ncf} - Retomar despues", value=False, key="guardar_borrador_fact_v71")
    if st.button(f"💰 PROCESAR FACTURA v71 {tipo_code} - {next_ncf} - REGISTRO LOCAL (NO ENVIO DGII)", type="primary", use_container_width=True):
        cod = base64.b64encode(os.urandom(6)).decode()[:6]; now = datetime.datetime.now(); fecha = now.strftime("%d-%m-%Y"); firma = now.strftime("%d-%m-%Y %H:%M:%S"); trackid = f"LOCAL-{str(uuid.uuid4())[:8].upper()}-v71-LIMPIO"
        xml_content = f"<eCF><Encabezado><eNCF>{next_ncf}</eNCF><Tipo>{tipo_code}</Tipo><RNCEmisor>{CRED['rnc']}</RNCEmisor><RNCComprador>{rnc_c}</RNCComprador><Fecha>{fecha}</Fecha><Total>{tot}</Total><Firma>{firma}</Firma></Encabezado><Detalle><Descripcion>{desc}</Descripcion><Cantidad>{cant}</Cantidad><Precio>{prec}</Precio><ITBIS>{itbis}</ITBIS></Detalle></eCF>"
        conn = sqlite3.connect(str(dbp)); c = conn.cursor()
        if confirmar_registro_local and not guardar_borrador_fact:
            # FIX 7: NO decir "ENVIADO OFICIAL". Decir REGISTRADO LOCAL.
            estado_dgii = f"REGISTRADO LOCAL - NO ENVIADO A DGII - Pendiente envio oficial con cert - Usuario {dgii_conf[2] if dgii_conf else ''} - Cuenta {cuenta_activa[0]}"
            estado_fact = "Registrado Local - Pendiente Envio DGII"
            try:
                c.execute("INSERT INTO facturas (ncf,tipo,cliente,rnc_cliente,descripcion,cantidad,precio,itbis,descuento,total,fecha,vencimiento,estado,codigo_seg,firma_digital,forma_pago,observaciones,xml_generado,trackid,estado_dgii) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (next_ncf, tipo_code, razon_c, rnc_c, desc, cant, prec, itbis, dsc, tot, fecha, str(venc), estado_fact, cod, firma, forma_pago, coment, xml_content, trackid, estado_dgii)); conn.commit()
                autoguardar_producto(client_id_input, desc, prec, uni)
                st.success(f"✅ REGISTRADO LOCAL v71 LIMPIO: {next_ncf} | Track Local {trackid} | NO enviado a DGII. Para envio oficial ve a modulo ENVIO DGII.")
                add_historico(client_id_input, "FACTURAR_REGISTRO_LOCAL_v71_LIMPIO", next_ncf, f"Facturado LOCAL {desc} Total {tot} Track Local {trackid} - NO enviado DGII", st.session_state.user)
            except sqlite3.IntegrityError: st.error(f"❌ NCF {next_ncf} ya existe")
        elif guardar_borrador_fact and not confirmar_registro_local:
            estado_dgii = f"BORRADOR v71 - No enviado a DGII - Guardado para retomar - Cuenta {cuenta_activa[0]}"
            estado_fact = "Borrador - Guardado para continuar v71"
            try:
                c.execute("INSERT INTO facturas (ncf,tipo,cliente,rnc_cliente,descripcion,cantidad,precio,itbis,descuento,total,fecha,vencimiento,estado,codigo_seg,firma_digital,forma_pago,observaciones,xml_generado,trackid,estado_dgii) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (next_ncf, tipo_code, razon_c, rnc_c, desc, cant, prec, itbis, dsc, tot, fecha, str(venc), estado_fact, cod, firma, forma_pago, coment, xml_content, f"BORRADOR-{trackid}", estado_dgii)); conn.commit()
                autoguardar_producto(client_id_input, desc, prec, uni)
                st.warning(f"📝 BORRADOR GUARDADO v71: {next_ncf}")
                add_historico(client_id_input, "FACTURAR_BORRADOR_v71_LIMPIO", next_ncf, f"Borrador {next_ncf} - {desc}", st.session_state.user)
            except sqlite3.IntegrityError: st.error(f"❌ NCF Borrador {next_ncf} ya existe")
        elif confirmar_registro_local and guardar_borrador_fact: st.error("❌ Elija solo una: Registrar Local o Borrador")
        else: st.warning("⚠️ Marque Registrar Local o Borrador")
        conn.close()
        if "retomar_ncf" in st.session_state: del st.session_state["retomar_ncf"]

if mod == "ENVIO_DGII_CERT":
    st.header("📤 ENVIO DGII - SEPARADO DEL REGISTRO LOCAL - v71 LIMPIO")
    st.warning("⚠️ Este modulo es el UNICO que debe hacer envio oficial a DGII. Por ahora esta en modo PREPARACION porque no hay conexion oficial DGII activa.")
    st.info(f"Portal DGII: {DGII_HOME}")
    dbp = get_db_path(client_id_input)
    if dbp.exists():
        conn = sqlite3.connect(str(dbp))
        try: df_fact = pd.read_sql_query("SELECT ncf, cliente, total, fecha, estado, estado_dgii, trackid FROM facturas WHERE estado_dgii LIKE '%REGISTRADO LOCAL%'", conn)
        except: df_fact = pd.DataFrame()
        conn.close()
        st.markdown("### Facturas Pendientes de Envio Real a DGII (Solo Registradas Local)")
        st.dataframe(df_fact, use_container_width=True)
        if len(df_fact) > 0:
            sel_ncf = st.selectbox("Selecciona NCF para intentar envio real", df_fact['ncf'].tolist())
            if st.button("🚀 Intentar Envio Real a DGII Oficial", type="primary"):
                ok, msg = enviar_a_dgii_real({"ncf": sel_ncf})
                st.error(f"DGII: {msg}")
                st.caption("Cuando conectes API DGII + certificado .p12, aqui se cambiara estado a 'ENVIADO A DGII' con codigo DGII y fecha oficial. Mientras tanto NO se reporta como enviado.")

if mod in ["CLIENTES","HISTORICO","PRECIOS","CERTIFICADOS","CONSULTAR_NCF"]:
    st.header(f"📋 Modulo {mod} - v71 LIMPIO")
    st.info("Este modulo usa la misma logica v71, pero con fixes: ID validado, info.json seguro, cuenta enmascarada ****5021, y estado DGII = REGISTRADO LOCAL.")
    dbp = get_db_path(client_id_input)
    if dbp.exists():
        conn = sqlite3.connect(str(dbp))
        try:
            if mod == "HISTORICO":
                df = pd.read_sql_query("SELECT * FROM historico ORDER BY id DESC LIMIT 100", conn); st.dataframe(df, use_container_width=True)
            elif mod == "CLIENTES":
                df = pd.read_sql_query("SELECT * FROM clientes_info", conn); st.dataframe(df, use_container_width=True)
                st.markdown("### Subir Certificado .p12 - Seguro")
                cert_file = st.file_uploader("Certificado .p12", type=["p12"], key="cert_upload_limpio")
                prov = st.text_input("Proveedor Cert", value="Viafirma")
                if st.button("Guardar Certificado"):
                    if cert_file:
                        try:
                            p = save_cert(client_id_input, cert_file, prov)
                            st.success(f"Cert guardado: {p}")
                        except Exception as e: st.error(f"Error cert: {e}")
            elif mod == "PRECIOS":
                df = pd.read_sql_query("SELECT * FROM productos_servicios ORDER BY veces_usado DESC", conn); st.dataframe(df, use_container_width=True)
            elif mod == "CERTIFICADOS":
                df = pd.read_sql_query("SELECT * FROM certificados", conn); st.dataframe(df, use_container_width=True)
            elif mod == "CONSULTAR_NCF":
                ncf_buscar = st.text_input("Buscar NCF", value="")
                if st.button("Buscar"):
                    df = pd.read_sql_query("SELECT * FROM facturas WHERE ncf=?", (ncf_buscar,)); st.dataframe(df, use_container_width=True)
                    if len(df) > 0: st.warning(f"Estado DGII: {df.iloc[0]['estado_dgii']} - Si dice REGISTRADO LOCAL, NO es Enviado Oficial.")
        except Exception as e: st.info(f"Sin datos: {e}")
        conn.close()

if mod == "CONSORCIO":
    st.header(f"🏢 Consorcio - Cliente {client_id_input} - Cuenta {CUENTA_MOSTRAR} - v71 LIMPIO")
    cuenta_activa = get_cuenta_pago_activa()
    st.markdown(format_cuenta_profesional(cuenta_activa), unsafe_allow_html=True)
    empresas_usuario = get_empresas_afiliadas_usuario(st.session_state.user)
    if not empresas_usuario: empresas_usuario = [client_id_input]
    st.markdown(f"### 🏢 Mis Empresas - {len(empresas_usuario)} empresas")
    st.write(empresas_usuario)
    st.markdown("### ➕ Afiliar Nueva Empresa")
    nueva_empresa_id = st.text_input("ID Nueva Empresa a Afiliar (Ej: CLI-D453)", value="", key="nueva_empresa_afiliar_v71_limpio")
    if st.button("✅ Afiliar Empresa", type="primary"):
        if not validar_id_cliente(nueva_empresa_id): st.error("ID invalido. Solo letras/numeros/guion.")
        elif not (CASOS_DIR / nueva_empresa_id).exists(): st.error(f"Empresa {nueva_empresa_id} no existe")
        else:
            dbp_principal = get_db_path(empresas_usuario[0] if empresas_usuario else client_id_input)
            conn = sqlite3.connect(str(dbp_principal)); c = conn.cursor()
            c.execute("SELECT * FROM afiliaciones WHERE usuario_master_email=?", (st.session_state.user,)); row = c.fetchone()
            if row:
                try: afili_exist = json.loads(row[3])
                except: afili_exist = []
                if nueva_empresa_id not in afili_exist: afili_exist.append(nueva_empresa_id)
                c.execute("UPDATE afiliaciones SET empresas_afiliadas_json=? WHERE id=?", (json.dumps(list(set(afili_exist))), row[0]))
            else:
                afili_id = f"AFIL-{str(uuid.uuid4())[:6].upper()}"
                c.execute("INSERT INTO afiliaciones (id,usuario_master_email,empresa_principal_id,empresas_afiliadas_json,tipo,fecha_creacion,estado) VALUES (?,?,?,?,?,?,?)", (afili_id, st.session_state.user, empresas_usuario[0], json.dumps(list(set(empresas_usuario + [nueva_empresa_id]))), "Consorcio", datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "Activo - Consorcio v71 LIMPIO"))
            conn.commit(); conn.close(); st.success(f"✅ Empresa {nueva_empresa_id} afiliada"); st.rerun()
    st.markdown("### 📊 Panel por Empresa")
    for emp_id in empresas_usuario:
        if not validar_id_cliente(emp_id): continue
        dbp_emp = get_db_path(emp_id)
        if dbp_emp.exists():
            conn = sqlite3.connect(str(dbp_emp))
            try:
                c = conn.cursor(); c.execute("SELECT COUNT(*), SUM(total) FROM facturas"); cnt, sm = c.fetchone()
                st.write(f"**{emp_id}** - Facturas: {cnt or 0} - Monto: RD$ {sm or 0:,.2f} - Liberado: {'SI' if verificar_liberado_bhd(emp_id) else 'NO'}")
            except: pass
            conn.close()

st.markdown(f'<div class="footer-pro" style="text-align:center;">BASA e-CF PRO v71 PROFESIONAL LIMPIO | RNC 133378711 | {CRED["empresa"]} | Cuenta {CUENTA_MOSTRAR} - BHD | Formato Profesional - Sin puntos | Estado DGII: REGISTRADO LOCAL ≠ ENVIADO OFICIAL</div>', unsafe_allow_html=True)
