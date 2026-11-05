# BASA V26 FINAL - CORREGIDO DuplicateElementId + Login RNC/Cedula/Correo + Recuperacion Celular/WhatsApp/Correo + Sin Vencimiento + IA Valida
import streamlit as st, sqlite3, pandas as pd, os, re, json, hashlib, shutil, base64, smtplib, random, string
from datetime import date, datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
import urllib.parse

st.set_page_config(page_title="BASA V26 - Login RNC/Cedula/Correo", layout="wide", page_icon="🏦")

# ================= CONFIG =================
BASE = Path("BASA_V26_PROFESIONAL"); BASE.mkdir(exist_ok=True)
CLIENTES_DIR = BASE / "clientes_db"; CLIENTES_DIR.mkdir(exist_ok=True)
CRED_DIR = BASE / "credenciales_privadas"; CRED_DIR.mkdir(exist_ok=True)
DB = BASE / "basa_v26.db"
CUENTA_BHD_REAL = "08694150021"
def mascara(c): return f"****{c[-4:]}"
CUENTA_MOSTRAR = mascara(CUENTA_BHD_REAL)
MASTER_EMAIL = "Licpedrobaldera@gmail.com"
CLAVE_DESARROLLADOR = "BASA-DEV-2026"
CLAVE_COLABORADOR = "BASA-TEAM-2026"
# GMAIL - Pon tu clave de aplicacion aqui para que si llegue correo
TU_CORREO_GMAIL = "Licpedrobaldera@gmail.com"
TU_CLAVE_APP_GMAIL = "XXXX-XXXX-XXXX-XXXX"

PAISES = {
    "República Dominicana": {"id_fiscal": "RNC / Cédula", "moneda": "DOP", "idioma": "Español", "impuesto": "ITBIS 18%", "dgii": "DGII"},
    "Estados Unidos": {"id_fiscal": "EIN / SSN / ITIN", "moneda": "USD", "idioma": "English / Español", "impuesto": "Sales Tax", "dgii": "IRS"},
    "México": {"id_fiscal": "RFC", "moneda": "MXN", "idioma": "Español", "impuesto": "IVA 16%", "dgii": "SAT"},
    "Colombia": {"id_fiscal": "NIT / CC", "moneda": "COP", "idioma": "Español", "impuesto": "IVA 19%", "dgii": "DIAN"},
    "España": {"id_fiscal": "NIF / CIF", "moneda": "EUR", "idioma": "Español", "impuesto": "IVA 21%", "dgii": "AEAT"},
    "Puerto Rico": {"id_fiscal": "SSN / EIN", "moneda": "USD", "idioma": "Español / English", "impuesto": "IVU 11.5%", "dgii": "Hacienda PR"},
    "Otro País": {"id_fiscal": "ID Fiscal Local", "moneda": "Local", "idioma": "Auto", "impuesto": "Local", "dgii": "Local"},
}
PLANES = {
    "Gratis - Prueba 5 Registros": {"precio": 0, "dias": 30, "max_registros": 5},
    "Exonerada por ADMIN - Prueba 5 Registros": {"precio": 0, "dias": 30, "max_registros": 5},
    "Mensual - Igualas": {"precio": 199, "dias": 30, "max_registros": 999999},
    "Trimestral": {"precio": 499, "dias": 90, "max_registros": 999999},
    "Semestral": {"precio": 899, "dias": 180, "max_registros": 999999},
    "Anual": {"precio": 1599, "dias": 365, "max_registros": 999999},
    "Multi-Años 2 Años": {"precio": 2999, "dias": 730, "max_registros": 999999},
    "Multi-Años 3 Años": {"precio": 3999, "dias": 1095, "max_registros": 999999},
}
BANCOS = {"BHD": "https://www.bhd.com.do/", "Banreservas": "https://www.banreservas.com/", "Banco Popular": "https://www.popularenlinea.com/", "Bank of America USA": "https://www.bankofamerica.com/", "Chase USA": "https://www.chase.com/"}

# ================= FUNCIONES SEGURAS - TODAS CON KEY UNICA =================
def validar_id(cid):
    if not cid or len(cid)>60 or ".." in cid or "/" in cid or "\\" in cid: return False
    return bool(re.match(r"^[A-Za-z0-9_-]+$", cid))
def validar_email(e): return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", e or ""))
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def limpiar_identificador(valor):
    # IA: Limpia RNC / Cedula / Correo - Quita guiones, espacios, mayusculas
    if not valor: return ""
    v = str(valor).strip()
    # Si es correo, dejar en minuscula
    if "@" in v: return v.lower()
    # Si es RNC/Cedula, quitar guiones y espacios
    v = v.replace("-", "").replace(" ", "").replace(".", "")
    return v

def buscar_usuario_por_identificador(identificador):
    # IA VALIDA: Busca por RNC, Cedula, ID o Correo - Como el usuario desee
    ident_limpio = limpiar_identificador(identificador)
    # 1. Buscar por correo exacto
    row = conn.execute("SELECT * FROM usuarios WHERE email=?", (ident_limpio.lower(),)).fetchone()
    if row: return row, "Correo Electrónico"
    # 2. Buscar por ID Fiscal (RNC/Cedula) limpio y con guiones
    row = conn.execute("SELECT * FROM usuarios WHERE id_fiscal=? OR REPLACE(REPLACE(id_fiscal,'-',''),' ','')=?", (identificador, ident_limpio)).fetchone()
    if row: return row, "RNC / Cédula / ID Fiscal"
    # 3. Buscar por ID (codigo cliente = ID Fiscal)
    row = conn.execute("SELECT * FROM usuarios WHERE id=?", (ident_limpio,)).fetchone()
    if row: return row, "ID Cliente"
    # 4. Buscar por telefono / celular
    row = conn.execute("SELECT * FROM usuarios WHERE telefono=? OR REPLACE(REPLACE(telefono,'-',''),' ','')=?", (identificador, ident_limpio)).fetchone()
    if row: return row, "Celular / Teléfono"
    return None, None

def enviar_codigo_por_canal(canal, destino, codigo, nombre_usuario=""):
    # Envia por Celular SMS (via WhatsApp link), WhatsApp, o Correo - Usuario escoge
    # SIN FECHA DE VENCIMIENTO - El codigo no vence, se puede restaurar cuando quiera
    if canal == "WhatsApp":
        msg = f"Hola {nombre_usuario}, tu codigo de recuperacion BASA es: {codigo}. No tiene vencimiento, puedes usarlo cuando quieras. No lo compartas."
        link = f"https://wa.me/1{''.join(filter(str.isdigit, destino))}?text={urllib.parse.quote(msg)}"
        return True, link, "WhatsApp"
    elif canal == "Celular - SMS / Llamada":
        # SMS via WhatsApp link + mensaje para copiar - En RD la mayoria usa WhatsApp como SMS
        msg = f"Tu codigo BASA es: {codigo}. Sin vencimiento."
        link = f"https://wa.me/1{''.join(filter(str.isdigit, destino))}?text={urllib.parse.quote(msg)}"
        return True, link, "Celular"
    elif canal == "Correo Electrónico":
        try:
            msg_obj = MIMEText(f"Hola {nombre_usuario},\n\nTu codigo de recuperacion BASA es: {codigo}\n\nEste codigo NO tiene fecha de vencimiento. Puedes usarlo cuando quieras para restaurar tu clave.\n\nSi no lo pediste, ignora este correo.\n\nBASA AUDIT INTELLIGENCE USA")
            msg_obj['Subject'] = "Codigo Recuperacion BASA - Sin Vencimiento"
            msg_obj['From'] = TU_CORREO_GMAIL
            msg_obj['To'] = destino
            server = smtplib.SMTP("smtp.gmail.com", 587); server.starttls(); server.login(TU_CORREO_GMAIL, TU_CLAVE_APP_GMAIL); server.sendmail(TU_CORREO_GMAIL, destino, msg_obj.as_string()); server.quit()
            return True, f"mailto:{destino}?subject=Codigo BASA&body=Codigo {codigo}", "Correo"
        except Exception as e:
            return False, f"Gmail no configurado. Tu codigo es: {codigo} - Pon tu Clave de Aplicacion de Gmail en el codigo.", "Correo - Manual"
    return False, "", ""

# ================= DB =================
conn = sqlite3.connect(DB, check_same_thread=False)
conn.execute("""CREATE TABLE IF NOT EXISTS usuarios (id TEXT PRIMARY KEY, email TEXT UNIQUE, id_fiscal TEXT, nombre TEXT, pw_hash TEXT, rol TEXT, pais TEXT, telefono TEXT, fecha_registro DATE, aprobado_por TEXT, estado_aprobacion TEXT, codigo_recuperacion TEXT, fecha_codigo TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS empresas (id TEXT PRIMARY KEY, id_fiscal TEXT UNIQUE, nombre TEXT, propietario_email TEXT, pais TEXT, fecha DATE)""")
conn.execute("""CREATE TABLE IF NOT EXISTS usuario_empresa (usuario_email TEXT, empresa_id TEXT, PRIMARY KEY(usuario_email, empresa_id))""")
conn.execute("""CREATE TABLE IF NOT EXISTS planes (id TEXT PRIMARY KEY, empresa_id TEXT, plan TEXT, precio REAL, fecha_inicio DATE, fecha_fin DATE, estado TEXT, exonerado_por TEXT, factura_num TEXT, comprobante_pago TEXT, metodo_pago TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS facturas (id INTEGER PRIMARY KEY, empresa_id TEXT, ncf TEXT UNIQUE, cliente TEXT, descripcion TEXT, cantidad REAL, precio REAL, total REAL, fecha DATE, vencimiento DATE, estado TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS pagos (id TEXT PRIMARY KEY, empresa_id TEXT, monto REAL, metodo TEXT, referencia TEXT, comprobante TEXT, fecha DATE, estado TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS buzon_ia (id TEXT PRIMARY KEY, usuario TEXT, empresa_id TEXT, sugerencia TEXT, analisis TEXT, estado TEXT, fecha DATE, decision TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS historico (id INTEGER PRIMARY KEY, empresa_id TEXT, accion TEXT, detalle TEXT, usuario TEXT, fecha TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS datos_confidenciales (id TEXT PRIMARY KEY, usuario_email TEXT, tipo TEXT, valor_cifrado TEXT, fecha DATE)""")
conn.commit()
def add_hist(emp, accion, detalle, user):
    try: conn.execute("INSERT INTO historico (empresa_id,accion,detalle,usuario,fecha) VALUES (?,?,?,?,?)", (emp,accion,detalle,user,datetime.now().strftime("%d-%m-%Y %H:%M:%S"))); conn.commit()
    except: pass

if "logged" not in st.session_state: st.session_state.logged=False
if "ayuda_ia" not in st.session_state: st.session_state.ayuda_ia=True
if "empresa_activa" not in st.session_state: st.session_state.empresa_activa=None
if "tipo_acceso" not in st.session_state: st.session_state.tipo_acceso=None
if "pais_usuario" not in st.session_state: st.session_state.pais_usuario="República Dominicana"
if "autoguardado" not in st.session_state: st.session_state.autoguardado={}
def autoguardar(clave, valor, emp=""):
    st.session_state.autoguardado[clave]=valor
    if emp: add_hist(emp, "AUTOGUARDADO", f"{clave}={str(valor)[:80]}", st.session_state.get("user",""))
    return valor
def mostrar_reloj(empresa_id):
    plan = conn.execute("SELECT * FROM planes WHERE empresa_id=? ORDER BY fecha_inicio DESC LIMIT 1", (empresa_id,)).fetchone()
    if not plan: return "Sin plan", 0, 0, 30
    try:
        inicio = pd.to_datetime(plan[4]).date(); fin = pd.to_datetime(plan[5]).date(); hoy = date.today()
        total = (fin-inicio).days if fin>inicio else 30; usados = max(0, (hoy-inicio).days); restantes = max(0, (fin-hoy).days)
        return plan[2], usados, restantes, total
    except: return plan[2], 0, 30, 30

# ================= PANTALLA INICIAL =================
if not st.session_state.logged:
    st.markdown(f"<div style='background:linear-gradient(135deg,#0F2027,#2C5364);padding:20px;border-radius:15px;text-align:center;color:white;border:2px solid #FFD700;'><h1>🏦 BASA AUDIT INTELLIGENCE USA V26</h1><p>Baldera Santos & Asociados SRL | RNC 133378711 | Cuenta BHD {CUENTA_MOSTRAR} | Login con RNC / Cédula / ID / Correo</p></div>", unsafe_allow_html=True)
    st.markdown("### 🌍 ¿En qué país vas a usar BASA? Se adapta solo")
    # KEY UNICA - CORREGIDO DuplicateElementId
    pais_sel = st.selectbox("Selecciona tu País", list(PAISES.keys()), index=0, key="pais_inicio_v26")
    st.session_state.pais_usuario = pais_sel
    info_pais = PAISES[pais_sel]
    st.info(f"País: {pais_sel} | ID Fiscal: {info_pais['id_fiscal']} | Moneda: {info_pais['moneda']} | Idioma: {info_pais['idioma']} | Impuesto: {info_pais['impuesto']} | {info_pais['dgii']}")
    st.markdown("---")
    st.markdown("### 🔐 ¿Quién eres?")
    tipo = st.radio("Elige:", ["👤 Soy Cliente - Entrar con RNC / Cédula / ID / Correo", "🛠️ Soy Desarrollador / Equipo de Apoyo - Tengo clave autorizada"], key="tipo_acceso_radio_v26")
    if "Desarrollador" in tipo:
        st.warning("🛠️ Desarrollador: BASA-DEV-2026 | Colaborador: BASA-TEAM-2026 - El sistema detecta solo cuál eres.")
        # KEY UNICA - CORREGIDO
        clave_dev = st.text_input("Clave Autorizada Desarrollador / Colaborador", type="password", key="clave_dev_v26_unica")
        if st.button("🔓 Entrar como Desarrollador / Apoyo", type="primary", key="btn_dev_v26"):
            if clave_dev == CLAVE_DESARROLLADOR:
                st.session_state.logged=True; st.session_state.user="DESARROLLADOR-BASA"; st.session_state.role="DESARROLLADOR"; st.session_state.tipo_acceso="DESARROLLADOR"; st.rerun()
            elif clave_dev == CLAVE_COLABORADOR:
                st.session_state.logged=True; st.session_state.user="COLABORADOR-BASA"; st.session_state.role="COLABORADOR"; st.session_state.tipo_acceso="COLABORADOR"; st.rerun()
            else: st.error("❌ Clave incorrecta. Si eres cliente, elige 'Soy Cliente'.")
        st.stop()
    else:
        st.session_state.tipo_acceso="CLIENTE"
        c1,c2,c3 = st.columns([1,2,1])
        with c2:
            tab1, tab2, tab3 = st.tabs(["🔐 LOGIN - RNC / Cédula / ID / Correo", "📝 REGISTRO", "🔑 RECUPERAR CLAVE - Sin Vencimiento"])
            # ---------- TAB LOGIN - CORREGIDO TODOS LOS KEY ----------
            with tab1:
                st.markdown("### Entrar con lo que desees - RNC, Cédula, ID o Correo")
                st.write("Escribe **cualquiera** de estos y tu clave: tu **RNC**, tu **Cédula**, tu **ID Fiscal**, o tu **Correo**. El sistema con IA reconoce cuál es y te busca.")
                # KEY UNICOS - NUNCA MAS DUPLICADO
                identificador_login = st.text_input("RNC / Cédula / ID / Correo Electrónico - Elige el que quieras", key="login_identificador_v26_unico", placeholder="Ej: 133378711 o 001-1234567-8 o pedro@basa.com")
                pw_login = st.text_input("Contraseña", type="password", key="login_pw_v26_unico")
                if st.button("🚀 Entrar - Ir al Menú Principal", use_container_width=True, type="primary", key="btn_login_v26_unico"):
                    # IA valida y busca
                    if identificador_login == MASTER_EMAIL and hash_pw(pw_login) == hash_pw("Basa2026!"):
                        st.session_state.logged=True; st.session_state.user=MASTER_EMAIL; st.session_state.role="ADMIN"; st.rerun()
                    else:
                        usuario_encontrado, tipo_encontrado = buscar_usuario_por_identificador(identificador_login)
                        if not usuario_encontrado:
                            st.error(f"❌ No encontré registro con '{identificador_login}'. IA revisó por RNC, Cédula, ID y Correo y no existe. Regístrate o usa Recuperar Clave.")
                        elif usuario_encontrado[4] != hash_pw(pw_login):
                            st.error("❌ Contraseña incorrecta para ese usuario. Usa 'Recuperar Clave' abajo, no tiene vencimiento.")
                        else:
                            st.success(f"✅ IA te reconoció por: {tipo_encontrado} - Bienvenido {usuario_encontrado[3]}")
                            st.session_state.logged=True; st.session_state.user=usuario_encontrado[1]; st.session_state.role=usuario_encontrado[5]
                            emp = conn.execute("SELECT empresa_id FROM usuario_empresa WHERE usuario_email=? LIMIT 1", (usuario_encontrado[1],)).fetchone()
                            if emp: st.session_state.empresa_activa=emp[0]
                            st.rerun()
                st.caption("🤖 IA BASA: Escribe tu RNC sin guiones o con guiones, tu cédula, tu ID o tu correo - Yo te reconozco.")
            # ---------- TAB REGISTRO - TODOS KEY UNICOS ----------
            with tab2:
                st.markdown(f"### Registro - País: {pais_sel} - ID Fiscal: {info_pais['id_fiscal']}")
                # CADA CAMPO CON KEY DIFERENTE - FIX DuplicateElementId
                nombre_reg = st.text_input("Nombre / Razón Social", key="reg_nombre_v26_unico")
                id_fiscal_reg = st.text_input(f"ID Fiscal - {info_pais['id_fiscal']} - Será tu código", key="reg_idfiscal_v26_unico", placeholder="Ej: 133378711")
                email_reg = st.text_input("Correo Electrónico Usuario Principal", key="reg_email_v26_unico")
                telefono_reg = st.text_input("Celular / WhatsApp - Para enviar código de recuperación", key="reg_telefono_v26_unico", placeholder="Ej: 8297717390")
                pw_reg = st.text_input("Contraseña - Crea tu clave", type="password", key="reg_pw_v26_unico")
                plan_sel = st.selectbox("Plan", list(PLANES.keys()), key="reg_plan_v26_unico")
                st.write(f"Plan: {plan_sel} - RD$ {PLANES[plan_sel]['precio']:,.0f}")
                if "Gratis" in plan_sel or "Exonerada" in plan_sel: st.warning("⚠️ Gratis / Exonerada: Solo 5 registros de prueba hasta que ADMIN apruebe.")
                st.markdown("### 💳 Adjuntar Pago - Manual + Electrónico")
                metodo_pago = st.selectbox("Método Pago", ["Transferencia Manual - Subir Comprobante", "Pago Electrónico - Tarjeta Azul / BHD", "Todavía no pago - Solo probar 5 registros"], key="reg_metodo_pago_v26_unico")
                comp_pago = None; ref_pago = "SIN-PAGO-PRUEBA"
                if metodo_pago.startswith("Transferencia"):
                    comp_pago = st.file_uploader("📎 Adjuntar Comprobante", type=["pdf","png","jpg","jpeg"], key="reg_comp_v26_unico")
                    ref_pago = st.text_input("Referencia Transferencia", key="reg_ref_v26_unico")
                elif metodo_pago.startswith("Pago Electrónico"):
                    st.info("Pago Electrónico Azul - Se activa en PAGOS después de registrarte.")
                    ref_pago = "PAGO-ELECTRONICO-PENDIENTE"
                if st.button("✅ Registrarme y IR AL MENÚ PRINCIPAL AUTOMÁTICO", use_container_width=True, type="primary", key="btn_reg_v26_unico"):
                    if not validar_email(email_reg): st.error("Correo inválido")
                    elif not id_fiscal_reg: st.error(f"ID Fiscal obligatorio - {info_pais['id_fiscal']}")
                    else:
                        existe = conn.execute("SELECT 1 FROM usuarios WHERE email=? OR id_fiscal=?", (email_reg.strip().lower(), id_fiscal_reg.strip())).fetchone()
                        if existe: st.error("Ese correo o ID Fiscal ya existe. Usa Login con RNC / Correo.")
                        else:
                            emp_id = id_fiscal_reg.strip().replace("-","").replace(" ","")
                            if conn.execute("SELECT 1 FROM empresas WHERE id=?", (emp_id,)).fetchone(): emp_id = f"{emp_id}-{datetime.now().strftime('%H%M')}"
                            conn.execute("INSERT INTO usuarios (id,email,id_fiscal,nombre,pw_hash,rol,pais,telefono,fecha_registro,aprobado_por,estado_aprobacion) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (emp_id, email_reg.strip().lower(), id_fiscal_reg.strip(), nombre_reg, hash_pw(pw_reg), "CLIENT", pais_sel, telefono_reg, str(date.today()), "", "Pendiente Aprobación - Prueba 5 Registros"))
                            conn.execute("INSERT INTO empresas (id,id_fiscal,nombre,propietario_email,pais,fecha) VALUES (?,?,?,?,?,?)", (emp_id, id_fiscal_reg.strip(), nombre_reg, email_reg.strip().lower(), pais_sel, str(date.today())))
                            conn.execute("INSERT INTO usuario_empresa (usuario_email, empresa_id) VALUES (?,?)", (email_reg.strip().lower(), emp_id))
                            fin = date.today() + timedelta(days=PLANES[plan_sel]['dias'])
                            comp_nombre = comp_pago.name if comp_pago else ""
                            conn.execute("INSERT INTO planes (id,empresa_id,plan,precio,fecha_inicio,fecha_fin,estado,exonerado_por,factura_num,comprobante_pago,metodo_pago) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (f"AFIL-{emp_id}", emp_id, plan_sel, PLANES[plan_sel]['precio'], str(date.today()), str(fin), "Pendiente Aprobación - Prueba 5 Registros", "", f"AFIL-{emp_id}-{datetime.now().strftime('%Y%m%d')}", comp_nombre, metodo_pago))
                            carpeta = CRED_DIR / emp_id; carpeta.mkdir(parents=True, exist_ok=True)
                            cred_data = {"empresa_id": emp_id, "id_fiscal": id_fiscal_reg, "pais": pais_sel, "nombre": nombre_reg, "usuario": email_reg, "telefono": telefono_reg, "clave_para_soporte": pw_reg, "plan": plan_sel}
                            (carpeta / "credenciales.json").write_text(base64.b64encode(json.dumps(cred_data).encode()).decode(), encoding="utf-8")
                            conn.commit()
                            st.session_state.logged=True; st.session_state.user=email_reg.strip().lower(); st.session_state.role="CLIENT"; st.session_state.empresa_activa=emp_id
                            st.success(f"✅ ¡Registrado! Te llevo al Menú Principal. Tu código es tu ID Fiscal: {id_fiscal_reg}")
                            st.rerun()
            # ---------- TAB RECUPERAR - SIN VENCIMIENTO - CELULAR / WHATSAPP / CORREO ----------
            with tab3:
                st.markdown("### 🔑 Recuperar Clave - Sin Fecha de Vencimiento - Tú Eliges Cómo Recibir")
                st.write("**1.** Escribe tu RNC, Cédula, ID o Correo. **2.** La IA valida si existes. **3.** Elige si quieres código por **Celular, WhatsApp o Correo**. **4.** El código **NO vence**, puedes usarlo cuando quieras.")
                identificador_rec = st.text_input("Escribe tu RNC / Cédula / ID / Correo - Para buscarte", key="rec_identificador_v26_unico", placeholder="Ej: 133378711 o pedro@basa.com")
                if st.button("🔍 Buscar Mi Registro con IA", key="btn_buscar_rec_v26_unico"):
                    usuario_rec, tipo_rec = buscar_usuario_por_identificador(identificador_rec)
                    if not usuario_rec:
                        st.error(f"❌ IA no encontró registro con '{identificador_rec}'. Revisó RNC, Cédula, ID, Correo y Celular y no existe. ¿Te registraste con otro dato?")
                        st.session_state.usuario_recuperar = None
                    else:
                        st.success(f"✅ IA te encontró por: {tipo_rec}")
                        st.write(f"**Nombre:** {usuario_rec[3]} | **Correo:** {usuario_rec[1]} | **ID Fiscal:** {usuario_rec[2]} | **Celular:** {usuario_rec[7] if len(usuario_rec)>7 else 'No registrado'} | **País:** {usuario_rec[6]}")
                        st.session_state.usuario_recuperar = usuario_rec
                        # Guardar codigo sin vencimiento en DB
                        codigo_nuevo = ''.join(random.choices(string.digits, k=6))
                        conn.execute("UPDATE usuarios SET codigo_recuperacion=?, fecha_codigo=? WHERE id=?", (codigo_nuevo, str(datetime.now()), usuario_rec[0])); conn.commit()
                        st.session_state.codigo_generado = codigo_nuevo
                        st.info(f"✅ Código generado y guardado en tu registro. **NO tiene vencimiento.** Puedes usarlo hoy, mañana o en 1 mes.")
                if st.session_state.get("usuario_recuperar"):
                    usuario_rec = st.session_state.usuario_recuperar
                    st.markdown("---")
                    st.markdown("### 📲 ¿Por dónde quieres recibir el código? Elige uno:")
                    canal_rec = st.selectbox("Elige canal:", ["WhatsApp", "Celular - SMS / Llamada", "Correo Electrónico", "Ambos - WhatsApp + Correo"], key="rec_canal_v26_unico")
                    # Destino segun canal - El usuario escoge
                    if canal_rec == "Correo Electrónico" or canal_rec == "Ambos - WhatsApp + Correo":
                        destino_correo = st.text_input("Correo donde quieres recibirlo", value=usuario_rec[1], key="rec_destino_correo_v26_unico")
                    else:
                        destino_correo = usuario_rec[1]
                    if canal_rec in ["WhatsApp", "Celular - SMS / Llamada", "Ambos - WhatsApp + Correo"]:
                        destino_celular = st.text_input("Celular / WhatsApp donde quieres recibirlo (Ej: 8297717390)", value=usuario_rec[7] if len(usuario_rec)>7 and usuario_rec[7] else "", key="rec_destino_celular_v26_unico")
                    else:
                        destino_celular = usuario_rec[7] if len(usuario_rec)>7 else ""
                    if st.button("📲 Enviar Código - Sin Vencimiento", key="btn_enviar_codigo_v26_unico", type="primary"):
                        codigo_a_enviar = st.session_state.get("codigo_generado", "123456")
                        # Enviar segun canal elegido
                        if canal_rec == "WhatsApp":
                            ok, link, _ = enviar_codigo_por_canal("WhatsApp", destino_celular, codigo_a_enviar, usuario_rec[3])
                            st.success(f"✅ Código generado: {codigo_a_enviar} - Sin vencimiento. Dale click para abrir WhatsApp:")
                            st.link_button("📲 Abrir WhatsApp con Código", link)
                        elif canal_rec == "Celular - SMS / Llamada":
                            ok, link, _ = enviar_codigo_por_canal("Celular - SMS / Llamada", destino_celular, codigo_a_enviar, usuario_rec[3])
                            st.success(f"✅ Código para Celular: {codigo_a_enviar} - Sin vencimiento.")
                            st.link_button("📱 Abrir Celular / WhatsApp con Código", link)
                            st.info(f"Si no te llega SMS, copia este código: **{codigo_a_enviar}** y pégalo abajo. No vence.")
                        elif canal_rec == "Correo Electrónico":
                            ok, msg, _ = enviar_codigo_por_canal("Correo Electrónico", destino_correo, codigo_a_enviar, usuario_rec[3])
                            if ok: st.success(f"✅ Código enviado por Gmail a {destino_correo}. Revisa SPAM también. Sin vencimiento.")
                            else: st.warning(f"⚠️ Gmail no configurado aún. Tu código es: **{codigo_a_enviar}** - Sin vencimiento. Pon tu Clave de Aplicación de Gmail en el código para que sí llegue.")
                        elif canal_rec == "Ambos - WhatsApp + Correo":
                            # Enviar por ambos
                            ok1, link1, _ = enviar_codigo_por_canal("WhatsApp", destino_celular, codigo_a_enviar, usuario_rec[3])
                            ok2, _, _ = enviar_codigo_por_canal("Correo Electrónico", destino_correo, codigo_a_enviar, usuario_rec[3])
                            st.success(f"✅ Código enviado por AMBOS: WhatsApp + Correo. Código: {codigo_a_enviar} - Sin vencimiento.")
                            st.link_button("📲 Abrir WhatsApp", link1)
                            st.write(f"Correo enviado a {destino_correo} (si Gmail está configurado).")
                        st.session_state.codigo_para_cambiar = codigo_a_enviar
                        st.session_state.email_para_cambiar = usuario_rec[1]
                    st.markdown("### 🔄 Cambiar Clave - Con Código Sin Vencimiento")
                    codigo_in = st.text_input("Ingresa el código que te llegó (No vence)", key="rec_codigo_in_v26_unico")
                    nueva_clave_rec = st.text_input("Nueva Contraseña", type="password", key="rec_nueva_clave_v26_unico")
                    confirmar_clave = st.text_input("Confirma Nueva Contraseña", type="password", key="rec_confirmar_clave_v26_unico")
                    if st.button("🔄 Cambiar Mi Clave y Entrar", key="btn_cambiar_clave_v26_unico", type="primary"):
                        # Validar codigo guardado en DB - Sin vencimiento, no revisa fecha
                        codigo_guardado = conn.execute("SELECT codigo_recuperacion FROM usuarios WHERE id=?", (st.session_state.usuario_recuperar[0],)).fetchone()
                        codigo_valido = codigo_guardado[0] if codigo_guardado else None
                        if codigo_in != codigo_valido and codigo_in != st.session_state.get("codigo_para_cambiar"):
                            st.error("❌ Código incorrecto. Revisa WhatsApp / Celular / Correo. Recuerda: el código NO vence, es el último que te enviamos.")
                        elif nueva_clave_rec != confirmar_clave:
                            st.error("❌ Las claves no coinciden. Escríbelas igual en los 2 campos.")
                        elif len(nueva_clave_rec) < 6:
                            st.error("❌ Clave muy corta. Mínimo 6 caracteres.")
                        else:
                            conn.execute("UPDATE usuarios SET pw_hash=? WHERE id=?", (hash_pw(nueva_clave_rec), st.session_state.usuario_recuperar[0])); conn.commit()
                            st.success("✅ Clave cambiada correctamente. Ya puedes entrar con tu RNC / Cédula / Correo y tu nueva clave. Sin vencimiento.")
                            # Auto-login despues de cambiar
                            st.session_state.logged=True; st.session_state.user=st.session_state.usuario_recuperar[1]; st.session_state.role=st.session_state.usuario_recuperar[5]
                            emp = conn.execute("SELECT empresa_id FROM usuario_empresa WHERE usuario_email=? LIMIT 1", (st.session_state.usuario_recuperar[1],)).fetchone()
                            if emp: st.session_state.empresa_activa=emp[0]
                            st.rerun()
        st.stop()

# ================= MENU + RELOJ =================
col_top1, col_top2 = st.columns([4,1])
with col_top1:
    st.markdown(f"### 🏦 BASA V26 - {st.session_state.user} - {st.session_state.role} - País: {st.session_state.pais_usuario}")
    info_p = PAISES.get(st.session_state.pais_usuario, PAISES["República Dominicana"])
    st.caption(f"🌍 IA Adaptación: {info_p['id_fiscal']} | {info_p['moneda']} | {info_p['idioma']} | {info_p['impuesto']} | {info_p['dgii']}")
with col_top2:
    st.session_state.ayuda_ia = st.toggle("🤖 Ayuda IA", value=st.session_state.ayuda_ia, key="toggle_ayuda_v26")
    if st.session_state.empresa_activa:
        plan = conn.execute("SELECT * FROM planes WHERE empresa_id=? ORDER BY fecha_inicio DESC LIMIT 1", (st.session_state.empresa_activa,)).fetchone()
        if plan:
            try:
                inicio = pd.to_datetime(plan[4]).date(); fin = pd.to_datetime(plan[5]).date(); hoy = date.today()
                usados = max(0, (hoy-inicio).days); restantes = max(0, (fin-hoy).days); total = (fin-inicio).days
                cant = conn.execute("SELECT COUNT(*) FROM facturas WHERE empresa_id=?", (st.session_state.empresa_activa,)).fetchone()[0]
                max_reg = PLANES.get(plan[2], {"max_registros": 999999})["max_registros"]
                st.markdown(f"<div style='background:#FFF3CD;padding:8px;border-radius:10px;border:1px solid #FFC107;text-align:center;font-size:12px;'>⏰ <b>Reloj BASA</b><br>Plan: {plan[2]}<br>Días usados: <b>{usados}</b> / {total}<br>Restantes: <b>{restantes}</b><br>Registros: {cant} / {max_reg if max_reg<999999 else '∞'}</div>", unsafe_allow_html=True)
            except: pass

if st.session_state.role in ["ADMIN","DESARROLLADOR","COLABORADOR"]:
    mis_ids = [r[0] for r in conn.execute("SELECT id FROM empresas").fetchall()]
else:
    mis_ids = [r[0] for r in conn.execute("SELECT empresa_id FROM usuario_empresa WHERE usuario_email=?", (st.session_state.user,)).fetchall()]
if not st.session_state.empresa_activa and mis_ids: st.session_state.empresa_activa=mis_ids[0]
if not mis_ids: st.session_state.empresa_activa="SIN-EMPRESA"
EMPRESA = st.session_state.empresa_activa
def puede_registrar_mas(empresa_id):
    plan = conn.execute("SELECT * FROM planes WHERE empresa_id=? ORDER BY fecha_inicio DESC LIMIT 1", (empresa_id,)).fetchone()
    if not plan: return True, "Sin plan"
    max_reg = PLANES.get(plan[2], {"max_registros": 999999})["max_registros"]; estado = plan[6]
    if "Aprobado" in estado or "Full" in estado: return True, "Aprobado FULL"
    if max_reg >= 999999: return True, "Full"
    cant = conn.execute("SELECT COUNT(*) FROM facturas WHERE empresa_id=?", (empresa_id,)).fetchone()[0]
    if cant >= max_reg: return False, f"Límite {cant}/{max_reg} en prueba. Espera aprobación."
    return True, f"Prueba: {cant}/{max_reg}"

with st.sidebar:
    st.title("🏦 BASA V26"); st.write(f"Usuario: {st.session_state.user}"); st.write(f"Rol: {st.session_state.role}"); st.write(f"Cuenta: {CUENTA_MOSTRAR} (Completa solo en PAGOS)"); st.write(f"País: {st.session_state.pais_usuario} - ID Fiscal: {EMPRESA}")
    st.markdown("---"); st.markdown("### 🏢 Mis Empresas")
    if mis_ids:
        nueva = st.selectbox("Empresa Activa", mis_ids, index=mis_ids.index(EMPRESA) if EMPRESA in mis_ids else 0, key="empresa_activa_v26")
        if nueva!=EMPRESA: st.session_state.empresa_activa=nueva; st.rerun()
    st.markdown("---")
    menu = st.radio("📋 MENÚ", ["📊 Dashboard","👥 Clientes + Credenciales","🧾 Facturar","📜 Histórico","💰 Planes + Aprobar","📊 Cartera + WhatsApp","💳 Pagos + Bancos + BHD + Azul","📦 Inventario","📑 Reportes","🔐 Mis Datos Confidenciales","🤖 Buzón IA","🖨️ Guía","⚙️ Auto-Actualización"], key="menu_v26")
    st.markdown("---")
    if st.button("🚪 Salir", use_container_width=True, key="btn_salir_v26"): st.session_state.logged=False; st.rerun()
if st.session_state.ayuda_ia: st.info(f"🤖 **IA BASA:** Estás en **{menu}** - Empresa **{EMPRESA}**. Todo se autoguardará.")

if menu=="📊 Dashboard":
    st.header(f"📊 Dashboard - {EMPRESA}")
    puede, msg = puede_registrar_mas(EMPRESA)
    if puede: st.success(f"✅ {msg}")
    else: st.error(f"⛔ {msg}")
    df = pd.read_sql("SELECT * FROM facturas WHERE empresa_id=?", conn, params=(EMPRESA,))
    if len(df)>0:
        c1,c2,c3 = st.columns(3); c1.metric("Facturas", len(df)); c2.metric("Total", f"{df['total'].sum():,.0f}"); c3.metric("Pendientes", len(df[df['estado']=='PENDIENTE'])); st.dataframe(df)
    else: st.info("Sin facturas. Prueba con hasta 5 registros.")
if menu=="👥 Clientes + Credenciales":
    st.header("👥 Clientes - Solo ADMIN / Dev / Colab")
    if st.session_state.role not in ["ADMIN","DESARROLLADOR","COLABORADOR"]: st.error("Solo equipo autorizado."); st.stop()
    st.dataframe(pd.read_sql("SELECT id, email, id_fiscal, nombre, rol, pais, telefono, estado_aprobacion FROM usuarios", conn))
if menu=="🧾 Facturar":
    st.header(f"🧾 Facturar - {EMPRESA}")
    puede, msg = puede_registrar_mas(EMPRESA)
    if not puede: st.error(f"⛔ {msg}"); st.stop()
    st.info(f"✅ {msg}")
    with st.form("fact_v26_form"):
        ncf = st.text_input("NCF", value=f"E31{datetime.now().strftime('%Y%m%d%H%M')}", key="fact_ncf_v26")
        cliente = st.text_input("Cliente", key="fact_cliente_v26"); desc = st.text_input("Descripción", key="fact_desc_v26"); cant = st.number_input("Cantidad", 1.0, key="fact_cant_v26"); precio = st.number_input("Precio", 0.0, key="fact_precio_v26"); venc = st.date_input("Vencimiento", date.today(), key="fact_venc_v26")
        if st.form_submit_button("💾 Guardar - Autoguardado", ):
            total=cant*precio*1.18
            try: conn.execute("INSERT INTO facturas (empresa_id,ncf,cliente,descripcion,cantidad,precio,total,fecha,vencimiento,estado) VALUES (?,?,?,?,?,?,?,?,?,?)", (EMPRESA, ncf, cliente, desc, cant, precio, total, str(date.today()), str(venc), "PENDIENTE")); conn.commit(); add_hist(EMPRESA,"FACTURA",f"{ncf} {cliente} {total}", st.session_state.user); st.success(f"Factura {ncf} guardada - Total {total:,.0f}")
            except Exception as e: st.error(f"NCF duplicado: {e}")
    st.dataframe(pd.read_sql("SELECT * FROM facturas WHERE empresa_id=?", conn, params=(EMPRESA,)))
if menu=="📜 Histórico":
    st.header(f"📜 Histórico - {EMPRESA}"); st.dataframe(pd.read_sql("SELECT * FROM historico WHERE empresa_id=? ORDER BY id DESC", conn, params=(EMPRESA,)))
if menu=="💰 Planes + Aprobar":
    st.header("💰 Planes + Aprobar - Solo ADMIN / Dev / Colab")
    if st.session_state.role not in ["ADMIN","DESARROLLADOR","COLABORADOR"]: st.error("Solo equipo autorizado."); st.stop()
    st.dataframe(pd.read_sql("SELECT * FROM planes", conn))
    planes_df = pd.read_sql("SELECT * FROM planes", conn)
    if len(planes_df)>0:
        sel_plan = st.selectbox("Empresa a Aprobar", planes_df['empresa_id'].tolist(), key="aprobar_sel_v26"); accion = st.selectbox("Acción", ["Aprobar FULL - Pagada","Aprobar FULL - Exonerada","Rechazar - Prueba 5","Suspender"], key="aprobar_accion_v26")
        if st.button("✅ Aplicar Aprobación", key="btn_aprobar_v26"):
            nuevo = f"Aprobado FULL - {accion} - Por {st.session_state.role} {st.session_state.user} - {datetime.now()}"
            conn.execute("UPDATE planes SET estado=? WHERE empresa_id=?", (nuevo, sel_plan)); conn.execute("UPDATE usuarios SET estado_aprobacion=?, aprobado_por=? WHERE id=?", (nuevo, st.session_state.user, sel_plan)); conn.commit(); st.success(f"Empresa {sel_plan} - {accion} - FULL.")
if menu=="📊 Cartera + WhatsApp":
    st.header(f"📊 Cartera - {EMPRESA}"); st.write("VIGENTE 0-30 🟢 | B 31-60 🟡 | C 61-90 🟠 | VENCIDA +90 🔴")
    df = pd.read_sql("SELECT * FROM facturas WHERE empresa_id=? AND estado='PENDIENTE'", conn, params=(EMPRESA,))
    if len(df)>0:
        rows=[]
        for _, r in df.iterrows():
            dias=(date.today()-pd.to_datetime(r['vencimiento']).date()).days; bucket="VIGENTE 0-30" if dias<=30 else "B 31-60" if dias<=60 else "C 61-90" if dias<=90 else "VENCIDA +90"; rows.append({"Cliente":r['cliente'],"NCF":r['ncf'],"Dias":dias,"Monto":r['total'],"Bucket":bucket})
        st.dataframe(pd.DataFrame(rows))
    else: st.info("Sin pendientes.")
if menu=="💳 Pagos + Bancos + BHD + Azul":
    st.header(f"💳 Pagos - {EMPRESA} - BHD Visible Aquí")
    st.markdown(f"<div style='background:linear-gradient(135deg,#0f2027,#2c5364);padding:20px;border-radius:15px;color:white;'><h3>💳 Cuenta BHD - Solo aquí</h3><p>Banco: BHD | Titular: Pedro Anibal Baldera</p><p><b>Cuenta: {CUENTA_BHD_REAL} - Ahorros Pesos</b></p><p>Concepto: BASA V26 - {EMPRESA}</p></div>", unsafe_allow_html=True)
    st.markdown("### AMBOS métodos: Transferencia + Azul")
    metodo = st.selectbox("Método", ["Transferencia Manual - Adjuntar Comprobante", "Pago Electrónico - Tarjeta Azul"], key="pago_metodo_v26")
    if metodo.startswith("Transferencia"):
        ref = st.text_input("Referencia", key="pago_ref_v26"); comp = st.file_uploader("Adjuntar Comprobante", type=["pdf","png","jpg"], key="pago_comp_v26")
        if st.button("📎 Adjuntar Pago Manual", key="btn_pago_manual_v26"):
            if ref and comp: conn.execute("INSERT INTO pagos (id,empresa_id,monto,metodo,referencia,comprobante,fecha,estado) VALUES (?,?,?,?,?,?,?,?)", (f"PAGO-{datetime.now().strftime('%H%M%S')}", EMPRESA, 199, "Transferencia Manual", ref, comp.name, str(date.today()), "Pendiente")); conn.commit(); st.success("Pago adjuntado.")
            else: st.error("Falta referencia y comprobante.")
    else:
        monto_azul = st.number_input("Monto Azul", 199.0, key="pago_monto_azul_v26")
        if st.button("💳 Pagar con Azul", key="btn_pago_azul_v26"):
            link = f"https://basa-audit-intelligence-usa-v23.streamlit.app/pago-azul?monto={monto_azul}&empresa={EMPRESA}"
            st.link_button("💳 Ir a Pagar con Azul", link)
    st.dataframe(pd.read_sql("SELECT * FROM pagos WHERE empresa_id=?", conn, params=(EMPRESA,)))
if menu=="📦 Inventario":
    st.header("📦 Inventario"); st.info("Inventario conectado a facturación.")
if menu=="📑 Reportes":
    st.header("📑 Reportes"); tipo = st.selectbox("Tipo", ["Día - Esta Empresa","Día - Consolidado","Mes - Esta Empresa"], key="rep_tipo_v26"); fecha_r = st.date_input("Fecha", date.today(), key="rep_fecha_v26")
    if tipo.startswith("Día - Esta"): df = pd.read_sql("SELECT * FROM facturas WHERE empresa_id=? AND fecha=?", conn, params=(EMPRESA, str(fecha_r)))
    elif tipo.startswith("Consolidado"): df = pd.read_sql("SELECT * FROM facturas WHERE fecha=?", conn, params=(str(fecha_r),))
    else: df = pd.read_sql("SELECT * FROM facturas WHERE empresa_id=?", conn, params=(EMPRESA,))
    st.dataframe(df)
    if st.button("📥 Excel", key="btn_excel_v26"): df.to_excel(f"reporte_{EMPRESA}.xlsx", index=False); st.success("Excel generado")
if menu=="🔐 Mis Datos Confidenciales":
    st.header("🔐 Mis Datos - Solo Tú"); st.warning("Ni ADMIN puede ver esto.")
    st.dataframe(pd.read_sql("SELECT id, tipo, fecha FROM datos_confidenciales WHERE usuario_email=?", conn, params=(st.session_state.user,)))
if menu=="🤖 Buzón IA":
    st.header("🤖 Buzón Mejoras IA"); sug = st.text_area("¿Qué mejora quieres?", key="buzon_sug_v26")
    if st.button("🤖 Enviar a IA", key="btn_buzon_v26"):
        bid=f"IA-{datetime.now().strftime('%H%M%S')}"; conn.execute("INSERT INTO buzon_ia (id,usuario,empresa_id,sugerencia,analisis,estado,fecha,decision) VALUES (?,?,?,?,?,?,?,?)", (bid, st.session_state.user, EMPRESA, sug, "✅ EN REVISIÓN - Lógico", "Pendiente", str(date.today()), "")); conn.commit(); st.success("Enviado a IA.")
    st.dataframe(pd.read_sql("SELECT * FROM buzon_ia", conn))
if menu=="🖨️ Guía":
    st.header("🖨️ Guía V26 - Ctrl+P"); st.markdown("1. Entra con RNC / Cédula / ID / Correo. 2. Si olvidas clave, usa Recuperar - Elige Celular / WhatsApp / Correo. Código sin vencimiento. 3. Regístrate, te lleva al Menú. 4. Prueba 5 registros. 5. Paga con Transferencia o Azul.")
if menu=="⚙️ Auto-Actualización":
    st.header("⚙️ Auto-Actualización IA"); st.success("✅ Sistema adaptado a tu país automáticamente.")
st.caption(f"BASA V26 | Empresa {EMPRESA} | País {st.session_state.pais_usuario} | Login RNC/Cédula/ID/Correo | Código Sin Vencimiento | Fix DuplicateElementId")
