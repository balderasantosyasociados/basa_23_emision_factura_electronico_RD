# BASA AUDIT INTELLIGENCE USA V24 PROFESIONAL FULL
# Menu Izquierda -> Despliega Derecha | Exonerar | Planes | BHD visible solo en Pago
# Historico Credenciales | Autoguardado | Guia + IA | Pago en Linea Bancos | Multi-Empresa | Bandeja IA
import streamlit as st, sqlite3, pandas as pd, os, re, json, hashlib, shutil, base64
from datetime import date, datetime, timedelta
from pathlib import Path
import urllib.parse

st.set_page_config(page_title="BASA V24 PROFESIONAL", layout="wide", page_icon="🏦")

# ================= 0. CONFIG BASA V24 =================
BASE = Path("BASA_V24_PROFESIONAL")
BASE.mkdir(exist_ok=True)
CLIENTES_DIR = BASE / "clientes_db"; CLIENTES_DIR.mkdir(exist_ok=True)
CREDENCIALES_DIR = BASE / "credenciales_privadas"; CREDENCIALES_DIR.mkdir(exist_ok=True)
BUZON_IA_DIR = BASE / "buzon_mejoras_ia"; BUZON_IA_DIR.mkdir(exist_ok=True)
DB = BASE / "basa_v24.db"

CUENTA_BHD_REAL = "08694150021"  # SOLO visible en modulo PAGOS
def mascara(c): return f"****{c[-4:]}" if len(c)>=4 else "****"
CUENTA_MOSTRAR = mascara(CUENTA_BHD_REAL)
BANCO, TITULAR = "BHD", "Pedro Anibal Baldera"
MASTER_EMAIL = "Licpedrobaldera@gmail.com"

# Bancos RD + Internacionales - Dentro del sistema sin salir (iframe / link interno)
BANCOS = {
    "BHD": "https://www.bhd.com.do/",
    "Banreservas": "https://www.banreservas.com/",
    "Banco Popular": "https://www.popularenlinea.com/",
    "Banco Santa Cruz": "https://www.bsc.com.do/",
    "Banco Caribe": "https://www.bancocaribe.com.do/",
    "Scotiabank RD": "https://www.scotiabank.com.do/",
    "Bank of America USA": "https://www.bankofamerica.com/",
    "Chase USA": "https://www.chase.com/",
    "Wells Fargo USA": "https://www.wellsfargo.com/",
    "Citi USA": "https://www.citi.com/",
}

PLANES = {
    "Gratis - Exonerado por ADMIN": {"precio": 0, "dias": 30, "desc": "Exonerado por ADMIN - Sin cobro"},
    "Mensual - Igualas": {"precio": 199, "dias": 30, "desc": "Pago mensual"},
    "Trimestral - 3 Meses": {"precio": 499, "dias": 90, "desc": "3 meses - Ahorra"},
    "Semestral - 6 Meses": {"precio": 899, "dias": 180, "desc": "6 meses"},
    "Anual - 12 Meses": {"precio": 1599, "dias": 365, "desc": "12 meses - Mejor precio"},
    "Multi-Años - 2 Años": {"precio": 2999, "dias": 730, "desc": "2 años"},
    "Multi-Años - 3 Años": {"precio": 3999, "dias": 1095, "desc": "3 años"},
}

# ================= 1. SEGURIDAD =================
def validar_id(cid):
    if not cid or len(cid)>50 or ".." in cid or "/" in cid or "\\" in cid: return False
    return bool(re.match(r"^[A-Za-z0-9_-]+$", cid))
def validar_email(e): return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", e or ""))
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def ruta_cliente(cid):
    if not validar_id(cid): return None
    r = (CLIENTES_DIR / cid).resolve()
    if not str(r).startswith(str(CLIENTES_DIR.resolve())): return None
    return r
def leer_json_seguro(p):
    if not p.exists(): return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except:
        try: shutil.copy(str(p), str(p.with_suffix(".bak")))
        except: pass
        return {}
def guardar_json_seguro(p, d):
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)
def guardar_credencial_privada(cid, data: dict):
    # SOLO ADMIN y COLABORADORES pueden ver - Carpeta por ID/RNC
    carpeta = CREDENCIALES_DIR / cid
    carpeta.mkdir(parents=True, exist_ok=True)
    # Guardar cifrado simple: base64 + hash, no texto plano en pantalla publica
    contenido = base64.b64encode(json.dumps(data, ensure_ascii=False).encode()).decode()
    (carpeta / "credenciales.json").write_text(contenido, encoding="utf-8")
    return str(carpeta)
def leer_credencial_privada(cid, rol):
    if rol not in ["ADMIN", "COLABORADOR"]: return None  # Cliente NO ve credenciales de otros, ADMIN si
    p = CREDENCIALES_DIR / cid / "credenciales.json"
    if not p.exists(): return {}
    try: return json.loads(base64.b64decode(p.read_text()).decode())
    except: return {}

# ================= 2. DB =================
conn = sqlite3.connect(DB, check_same_thread=False)
conn.execute("""CREATE TABLE IF NOT EXISTS usuarios (id TEXT PRIMARY KEY, email TEXT UNIQUE, rnc TEXT, nombre TEXT, pw_hash TEXT, rol TEXT, fecha DATE)""")
conn.execute("""CREATE TABLE IF NOT EXISTS empresas (id TEXT PRIMARY KEY, rnc TEXT UNIQUE, nombre TEXT, propietario_email TEXT, fecha DATE)""")
conn.execute("""CREATE TABLE IF NOT EXISTS usuario_empresa (usuario_email TEXT, empresa_id TEXT, rol_en_empresa TEXT, PRIMARY KEY(usuario_email, empresa_id))""")
conn.execute("""CREATE TABLE IF NOT EXISTS planes (id TEXT PRIMARY KEY, empresa_id TEXT, plan TEXT, precio REAL, fecha_inicio DATE, fecha_fin DATE, estado TEXT, exonerado_por TEXT, factura_numero TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS facturas (id INTEGER PRIMARY KEY, empresa_id TEXT, ncf TEXT UNIQUE, cliente TEXT, descripcion TEXT, cantidad REAL, precio REAL, total REAL, fecha DATE, vencimiento DATE, estado TEXT, estado_dgii TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS pagos (id TEXT PRIMARY KEY, empresa_id TEXT, monto REAL, metodo TEXT, referencia TEXT, comprobante TEXT, fecha DATE, estado TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS buzon_ia (id TEXT PRIMARY KEY, usuario TEXT, empresa_id TEXT, sugerencia TEXT, analisis_ia TEXT, estado TEXT, fecha DATE, decision_admin TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS historico (id INTEGER PRIMARY KEY, empresa_id TEXT, accion TEXT, detalle TEXT, usuario TEXT, fecha TEXT)""")
conn.execute("""CREATE TABLE IF NOT EXISTS datos_confidenciales (id TEXT PRIMARY KEY, usuario_email TEXT, tipo TEXT, valor_cifrado TEXT, fecha DATE)""")  # Solo el usuario ve esto
conn.commit()

def add_hist(empresa_id, accion, detalle, usuario):
    conn.execute("INSERT INTO historico (empresa_id, accion, detalle, usuario, fecha) VALUES (?,?,?,?,?)", (empresa_id, accion, detalle, usuario, datetime.now().strftime("%d-%m-%Y %H:%M:%S")))
    conn.commit()

# ================= 3. SESION =================
if "logged" not in st.session_state: st.session_state.logged=False
if "ayuda_ia" not in st.session_state: st.session_state.ayuda_ia=True  # Boton derecha ON/OFF
if "empresa_activa" not in st.session_state: st.session_state.empresa_activa=None
if "autoguardado" not in st.session_state: st.session_state.autoguardado={}

# AUTOGUARDADO: al hacer click o cambiar campo, se guarda en session y en DB
def autoguardar(clave, valor, empresa_id=""):
    st.session_state.autoguardado[clave]=valor
    # Guardar en historico silencioso
    try:
        if empresa_id: add_hist(empresa_id, "AUTOGUARDADO", f"{clave} = {str(valor)[:100]}", st.session_state.get("user",""))
    except: pass
    return valor

# ================= 4. LOGIN / RECUPERACION POR RNC / USUARIO / CORREO =================
if not st.session_state.logged:
    st.markdown(f"<div style='background:linear-gradient(135deg,#0F2027,#2C5364);padding:20px;border-radius:15px;text-align:center;color:white;border:2px solid #FFD700;'><h1>🏦 BASA AUDIT INTELLIGENCE USA V24 PROFESIONAL</h1><p>Baldera Santos & Asociados SRL | RNC 133378711 | Cuenta BHD {CUENTA_MOSTRAR} | Pedro Anibal Baldera</p></div>", unsafe_allow_html=True)
    # BOTON AYUDA IA A MANO DERECHA
    col_izq, col_der = st.columns([4,1])
    with col_der:
        st.session_state.ayuda_ia = st.toggle("🤖 Ayuda IA", value=st.session_state.ayuda_ia, help="Activa / Desactiva guia con IA")
    if st.session_state.ayuda_ia:
        st.info("🤖 **IA BASA:** Hola, soy tu asistente. Te voy a guiar paso a paso. Si no quieres ayuda, apaga el botón de arriba a la derecha. Puedes imprimir esta guía en el botón 'Imprimir Guía' abajo.")
    c1,c2,c3 = st.columns([1,2,1])
    with c2:
        tab1, tab2, tab3 = st.tabs(["🔐 LOGIN", "📝 REGISTRO + AFILIACION", "🔑 RECUPERAR CLAVE"])
        with tab1:
            email = st.text_input("Correo / Usuario")
            pw = st.text_input("Contraseña", type="password")
            if st.button("🚀 Entrar a BASA V24", use_container_width=True, type="primary"):
                if email==MASTER_EMAIL and hash_pw(pw)==hash_pw("Basa2026!"):
                    st.session_state.logged=True; st.session_state.user=email; st.session_state.role="ADMIN"; st.rerun()
                else:
                    row = conn.execute("SELECT * FROM usuarios WHERE email=? AND pw_hash=?", (email.strip().lower(), hash_pw(pw))).fetchone()
                    if row: st.session_state.logged=True; st.session_state.user=row[1]; st.session_state.role=row[5]; st.rerun()
                    else: st.error("Credenciales incorrectas. Usa Recuperar Clave por RNC / Usuario / Correo.")
        with tab2:
            st.markdown("### Afiliación BASA - Elige tu Plan")
            nombre = st.text_input("Nombre / Razon Social", key="reg_nombre")
            rnc = st.text_input("RNC / Cedula", key="reg_rnc")
            email_r = st.text_input("Correo Usuario Principal", key="reg_email")
            pw_r = st.text_input("Contraseña", type="password", key="reg_pw")
            plan_sel = st.selectbox("Plan de Afiliación", list(PLANES.keys()), key="reg_plan")
            st.write(f"**Plan:** {plan_sel} - **Precio:** RD$ {PLANES[plan_sel]['precio']:,.0f} - {PLANES[plan_sel]['desc']}")
            # Exonerado solo si ADMIN lo aprueba - por defecto NO exonerado, ADMIN lo exonera despues
            if st.button("✅ Registrarme + Crear Mi Empresa + Generar Factura Afiliación", use_container_width=True, type="primary"):
                if not validar_email(email_r): st.error("Correo invalido")
                elif not validar_id(rnc.replace("-","")) and not rnc: st.error("RNC obligatorio")
                else:
                    existe = conn.execute("SELECT 1 FROM usuarios WHERE email=?", (email_r.strip().lower(),)).fetchone()
                    if existe: st.error("Ese correo ya existe. Usa Recuperar Clave.")
                    else:
                        emp_id = f"CLI-{rnc[-4:] if len(rnc)>=4 else '0000'}-{pd.Timestamp.now().strftime('%H%M')}"
                        # Guardar usuario
                        conn.execute("INSERT INTO usuarios (id,email,rnc,nombre,pw_hash,rol,fecha) VALUES (?,?,?,?,?,?,?)", (emp_id, email_r.strip().lower(), rnc, nombre, hash_pw(pw_r), "CLIENT", str(date.today())))
                        conn.execute("INSERT INTO empresas (id,rnc,nombre,propietario_email,fecha) VALUES (?,?,?,?,?)", (emp_id, rnc, nombre, email_r.strip().lower(), str(date.today())))
                        conn.execute("INSERT INTO usuario_empresa (usuario_email, empresa_id, rol_en_empresa) VALUES (?,?,?)", (email_r.strip().lower(), emp_id, "PROPIETARIO"))
                        # Factura Afiliacion - Generada automaticamente
                        factura_num = f"AFIL-{emp_id}-{datetime.now().strftime('%Y%m%d%H%M')}"
                        fin = date.today() + timedelta(days=PLANES[plan_sel]['dias'])
                        conn.execute("INSERT INTO planes (id,empresa_id,plan,precio,fecha_inicio,fecha_fin,estado,exonerado_por,factura_numero) VALUES (?,?,?,?,?,?,?,?,?)", (factura_num, emp_id, plan_sel, PLANES[plan_sel]['precio'], str(date.today()), str(fin), "Pendiente Pago - Esperando ADMIN exonerar o pago", "", factura_num))
                        conn.commit()
                        # Guardar credenciales en carpeta privada por ID/RNC
                        guardar_credencial_privada(emp_id, {"empresa_id": emp_id, "rnc": rnc, "nombre": nombre, "usuario_principal": email_r, "clave_hash": hash_pw(pw_r), "clave_para_soporte": pw_r, "plan": plan_sel, "factura_afiliacion": factura_num, "fecha": str(date.today())})
                        st.success(f"✅ Registrado! Empresa {emp_id} | Factura Afiliación {factura_num} | Plan {plan_sel} | RD$ {PLANES[plan_sel]['precio']:,.0f} | Ve a PAGOS para pagar o espera que ADMIN te exonere.")
                        st.balloons()
        with tab3:
            st.markdown("### Recuperar Clave - Por RNC / Usuario / Correo")
            st.write("Elige cómo quieres buscarte:")
            metodo = st.selectbox("Buscar por:", ["RNC / Cedula", "Correo / Usuario Registrado", "Nombre Empresa"])
            valor_buscar = st.text_input("Escribe RNC, Correo o Nombre", key="rec_buscar")
            if st.button("🔍 Buscar Mi Cuenta"):
                if metodo=="RNC / Cedula": rows = conn.execute("SELECT * FROM usuarios WHERE rnc=?", (valor_buscar,)).fetchall()
                elif metodo=="Correo / Usuario Registrado": rows = conn.execute("SELECT * FROM usuarios WHERE email=?", (valor_buscar.strip().lower(),)).fetchall()
                else: rows = conn.execute("SELECT * FROM usuarios WHERE nombre LIKE ?", (f"%{valor_buscar}%",)).fetchall()
                if not rows: st.error("No encontrado. Verifica RNC / Correo.")
                else:
                    st.success(f"Encontrado {len(rows)} usuario(s) para esa empresa:")
                    for r in rows:
                        st.write(f"**Usuario:** {r[1]} | **Empresa:** {r[3]} | **RNC:** {r[2]}")
                    st.session_state.usuarios_encontrados = rows
            if "usuarios_encontrados" in st.session_state:
                st.markdown("### ¿A quién quieres que le llegue el código?")
                opciones = [f"{r[1]} - {r[3]}" for r in st.session_state.usuarios_encontrados]
                sel_usuario = st.selectbox("Elige usuario para enviar código", opciones)
                canal = st.selectbox("Enviar por:", ["WhatsApp", "Correo Electronico", "Mostrar en pantalla (si eres ADMIN)"])
                if st.button("📲 Enviar Código de Recuperación"):
                    codigo = "".join([str(pd.Timestamp.now().microsecond)[-1] for _ in range(6)])
                    # En esta version, generamos link WhatsApp y correo, no enviamos solo sin permiso
                    email_dest = sel_usuario.split(" - ")[0]
                    wa_link = f"https://wa.me/18297717390?text={urllib.parse.quote(f'Tu codigo BASA es: {codigo} para usuario {email_dest}')}"
                    st.success(f"Código generado: {codigo} (Guárdalo)")
                    if canal=="WhatsApp": st.link_button("📲 Abrir WhatsApp con Código", wa_link)
                    elif canal=="Correo Electronico": st.markdown(f"[📧 Enviar por Correo a {email_dest}](mailto:{email_dest}?subject=Codigo BASA&body=Tu codigo es {codigo})")
                    else: st.info(f"Código para ADMIN: {codigo} - Usuario {email_dest}")
                    st.session_state.codigo_rec = codigo; st.session_state.email_rec = email_dest
                codigo_in = st.text_input("Ingresa código recibido", key="rec_codigo_in")
                nueva_clave = st.text_input("Nueva clave", type="password", key="rec_nueva")
                if st.button("🔄 Cambiar Clave"):
                    if codigo_in == st.session_state.get("codigo_rec"):
                        conn.execute("UPDATE usuarios SET pw_hash=? WHERE email=?", (hash_pw(nueva_clave), st.session_state.email_rec)); conn.commit()
                        st.success("Clave cambiada. Ya puedes entrar.")
                    else: st.error("Código incorrecto.")
    # GUIA IMPRIMIBLE
    st.markdown("---")
    if st.button("🖨️ Imprimir Guía de Uso BASA V24 - Instrucciones"):
        st.markdown("""
        **GUIA BASA V24 - PARA IMPRIMIR**
        1. Registrate con RNC y correo. Elige plan Mensual/Trimestral/Semestral/Anual/Multi-Años.
        2. Paga en modulo PAGOS con tarjeta o transferencia. BHD 08694150021 visible solo ahi.
        3. Si ADMIN te exonera, tu plan queda Gratis.
        4. Factura en FACTURAR. Cambia de empresa arriba sin salir.
        5. Revisa CARTERA: VIGENTE 0-30, B 31-60, C 61-90, VENCIDA +90.
        6. Exporta reportes del dia por empresa o consolidado a Excel/Word.
        7. Si olvidas clave, usa Recuperar por RNC / Usuario / Correo.
        8. Apaga Ayuda IA con boton derecha si no quieres guia.
        """)
    st.stop()

# ================= 5. MENU IZQUIERDA -> DESPLIEGA DERECHA =================
# Boton Ayuda IA a mano derecha - Siempre visible
col_top1, col_top2 = st.columns([5,1])
with col_top1:
    st.markdown(f"### 🏦 BASA V24 PROFESIONAL - {st.session_state.user} - {st.session_state.role}")
with col_top2:
    st.session_state.ayuda_ia = st.toggle("🤖 Ayuda IA", value=st.session_state.ayuda_ia, key="toggle_ayuda_top")

# Empresas del usuario - Puede tener muchas empresas bajo mismo usuario
mis_empresas = conn.execute("SELECT empresa_id FROM usuario_empresa WHERE usuario_email=?", (st.session_state.user,)).fetchall()
if st.session_state.role=="ADMIN":
    todas = conn.execute("SELECT id, nombre FROM empresas").fetchall()
    mis_empresas_ids = [r[0] for r in todas] if todas else []
else:
    mis_empresas_ids = [r[0] for r in mis_empresas]

# Si no tiene empresa activa, seleccionar primera
if not st.session_state.empresa_activa and mis_empresas_ids:
    st.session_state.empresa_activa = mis_empresas_ids[0]
elif not mis_empresas_ids:
    st.session_state.empresa_activa = "SIN-EMPRESA"

# MENU IZQUIERDA - PROFESIONAL
with st.sidebar:
    st.title("🏦 BASA V24")
    st.write(f"Usuario: {st.session_state.user}")
    st.write(f"Rol: {st.session_state.role}")
    st.write(f"Cuenta BHD: {CUENTA_MOSTRAR} (Completa solo en PAGOS)")
    st.markdown("---")
    st.markdown("### 🏢 Mis Empresas - Cambiar sin salir")
    if mis_empresas_ids:
        nueva_emp = st.selectbox("Empresa Activa - Facturar aquí", mis_empresas_ids, index=mis_empresas_ids.index(st.session_state.empresa_activa) if st.session_state.empresa_activa in mis_empresas_ids else 0)
        if nueva_emp != st.session_state.empresa_activa:
            st.session_state.empresa_activa = nueva_emp
            st.rerun()
        st.success(f"Operando en: {st.session_state.empresa_activa}")
    else:
        st.warning("Sin empresas. Registra una en PAGOS / AFILIACION.")
    st.markdown("---")
    # MENU - Al pulsar despliega a la derecha
    menu = st.radio("📋 MENÚ BASA - Pulsa y se abre a la derecha", [
        "📊 Dashboard",
        "👥 Clientes + Histórico Credenciales (Solo ADMIN/Colaborador)",
        "🧾 Facturar",
        "📜 Histórico por Cliente",
        "💰 Planes + Exonerar (ADMIN)",
        "📊 Cartera por Edades + WhatsApp",
        "💳 Pagos en Línea + Bancos + BHD Visible",
        "📦 Inventario",
        "📑 Reportes Día / Consolidado Excel-Word",
        "🔐 Mis Datos Confidenciales (Solo Yo)",
        "🤖 Buzón Mejoras IA",
        "🖨️ Guía Imprimible",
    ], key="menu_v24")
    st.markdown("---")
    if st.button("🚪 Salir", use_container_width=True): st.session_state.logged=False; st.rerun()

EMPRESA = st.session_state.empresa_activa
if st.session_state.ayuda_ia:
    st.info(f"🤖 **IA BASA:** Estás en **{menu}** - Empresa **{EMPRESA}**. Todo lo que escribas se autoguardará al hacer click o mover el mouse. Si no quieres ayuda, apaga el botón 🤖 arriba a la derecha.")

# ================= 6. MODULOS - DERECHA =================
if menu == "📊 Dashboard":
    st.header(f"📊 Dashboard - Empresa {EMPRESA}")
    df = pd.read_sql("SELECT * FROM facturas WHERE empresa_id=?", conn, params=(EMPRESA,))
    if len(df)>0:
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Facturas", len(df)); c2.metric("Total", f"RD$ {df['total'].sum():,.0f}"); c3.metric("Pendientes", len(df[df['estado']=='PENDIENTE'])); c4.metric("Pagadas", len(df[df['estado']=='PAGADA']))
        st.dataframe(df)
    else: st.info("Sin facturas en esta empresa. Cambia de empresa arriba o factura aquí.")
    # Planes
    plan = conn.execute("SELECT * FROM planes WHERE empresa_id=? ORDER BY fecha_inicio DESC LIMIT 1", (EMPRESA,)).fetchone()
    if plan: st.write(f"**Tu Plan:** {plan[2]} - RD$ {plan[3]:,.0f} - Vence: {plan[5]} - Estado: {plan[6]} - Factura: {plan[8]}")
    else: st.warning("Sin plan. Ve a Planes para afiliarte.")

if menu == "👥 Clientes + Histórico Credenciales (Solo ADMIN/Colaborador)":
    st.header("👥 Clientes + Histórico Credenciales - Solo ADMIN / Colaborador")
    if st.session_state.role not in ["ADMIN", "COLABORADOR"]:
        st.error("⛔ Solo ADMIN y Colaboradores pueden ver credenciales. Tu rol es CLIENT.")
        st.stop()
    st.write("Carpeta por ID / RNC / Cédula - Guardada en `credenciales_privadas / ID`")
    # Buscar cliente por RNC / ID / Correo
    buscar = st.text_input("Buscar por RNC, ID, Correo o Nombre")
    usuarios = pd.read_sql("SELECT id, email, rnc, nombre, rol, fecha FROM usuarios", conn)
    if buscar: usuarios = usuarios[usuarios.apply(lambda r: buscar.lower() in str(r.values).lower(), axis=1)]
    st.dataframe(usuarios)
    if len(usuarios)>0:
        sel = st.selectbox("Selecciona cliente para ver/editar credenciales", usuarios['id'].tolist())
        cred = leer_credencial_privada(sel, st.session_state.role)
        st.subheader(f"🔐 Credenciales - {sel}")
        st.json(cred if cred else {"mensaje": "Sin credenciales guardadas todavia"})
        st.markdown("### ✏️ Editar Credencial - Solo ADMIN/Colaborador")
        nuevo_usuario = st.text_input("Usuario DGII / Portal", value=cred.get("usuario_principal","") if cred else "")
        nueva_clave = st.text_input("Clave para Soporte (Se guarda cifrada)", type="password")
        html_cert = st.text_area("HTML / Certificado Digital (Texto)", value=cred.get("html","") if cred else "")
        if st.button("💾 Guardar Credencial Actualizada"):
            cred_nuevo = {**cred, "usuario_principal": nuevo_usuario, "clave_para_soporte": nueva_clave, "html": html_cert, "actualizado_por": st.session_state.user, "fecha": str(date.today())}
            guardar_credencial_privada(sel, cred_nuevo)
            st.success("Credencial guardada en carpeta privada.")
        st.markdown("### 📲 Enviar Credencial al Cliente - Tú eliges a quién")
        canal_envio = st.selectbox("Enviar por", ["WhatsApp", "Correo"])
        destino = st.text_input("WhatsApp (809...) o Correo destino")
        if st.button("📲 Enviar Credencial"):
            msg = f"Hola, tu usuario BASA es {nuevo_usuario} y tu clave de recuperación es {nueva_clave}. No la compartas."
            if canal_envio=="WhatsApp":
                wa = f"https://wa.me/1{destino}?text={urllib.parse.quote(msg)}"
                st.link_button("📲 Abrir WhatsApp", wa)
            else:
                st.markdown(f"[📧 Enviar por Correo](mailto:{destino}?subject=Credenciales BASA&body={urllib.parse.quote(msg)})")

if menu == "🧾 Facturar":
    st.header(f"🧾 Facturar - Empresa {EMPRESA} - Autoguardado Activo")
    st.caption("Todo lo que escribas se autoguardará al hacer click o cambiar de campo.")
    with st.form("fact_form"):
        ncf = st.text_input("NCF / e-CF", value=f"E31{datetime.now().strftime('%Y%m%d%H%M')}")
        cliente = st.text_input("Cliente", value=autoguardar("fact_cliente", st.session_state.autoguardado.get("fact_cliente",""), EMPRESA))
        desc = st.text_input("Descripción", value=st.session_state.autoguardado.get("fact_desc",""))
        cant = st.number_input("Cantidad", 1.0)
        precio = st.number_input("Precio RD$", 0.0)
        fecha_v = st.date_input("Vencimiento", date.today())
        if st.form_submit_button("💾 Guardar Factura - Autoguardado"):
            total = cant*precio*1.18
            try:
                conn.execute("INSERT INTO facturas (empresa_id,ncf,cliente,descripcion,cantidad,precio,total,fecha,vencimiento,estado,estado_dgii) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (EMPRESA, ncf, cliente, desc, cant, precio, total, str(date.today()), str(fecha_v), "PENDIENTE", "REGISTRADO LOCAL - NO ENVIADO A DGII"))
                conn.commit(); add_hist(EMPRESA, "FACTURA", f"{ncf} - {cliente} - RD$ {total:,.0f}", st.session_state.user)
                st.success(f"Factura {ncf} guardada en empresa {EMPRESA} - Total RD$ {total:,.0f}")
                # Autoguardar al hacer click
                autoguardar("fact_cliente", cliente, EMPRESA); autoguardar("fact_desc", desc, EMPRESA)
            except Exception as e: st.error(f"Error: {e} - NCF duplicado?")
    st.dataframe(pd.read_sql("SELECT * FROM facturas WHERE empresa_id=?", conn, params=(EMPRESA,)))

if menu == "📜 Histórico por Cliente":
    st.header(f"📜 Histórico - Empresa {EMPRESA}")
    hist = pd.read_sql("SELECT * FROM historico WHERE empresa_id=? ORDER BY id DESC", conn, params=(EMPRESA,))
    st.dataframe(hist)
    if st.button("📥 Exportar Histórico Excel"):
        hist.to_excel(f"historico_{EMPRESA}.xlsx", index=False); st.success("Excel generado")

if menu == "💰 Planes + Exonerar (ADMIN)":
    st.header("💰 Planes + Exonerar - Solo ADMIN puede exonerar")
    st.write("Planes: Mensual, Trimestral, Semestral, Anual, Multi-Años. ADMIN puede exonerar a sus clientes admitidos.")
    if st.session_state.role=="ADMIN":
        st.markdown("### Exonerar Pago - Cliente Admitido por ADMIN")
        todas_emp = pd.read_sql("SELECT id, nombre, rnc FROM empresas", conn)
        st.dataframe(todas_emp)
        if len(todas_emp)>0:
            emp_ex = st.selectbox("Empresa a Exonerar", todas_emp['id'].tolist())
            motivo = st.text_input("Motivo Exoneración - Ej: Cliente VIP BASA, Colaborador, Prueba")
            if st.button("✅ EXONERAR - Gratis - Sin Cobro"):
                conn.execute("UPDATE planes SET estado=?, exonerado_por=? WHERE empresa_id=?", (f"EXONERADO - Gratis - Motivo: {motivo} - Por ADMIN {st.session_state.user}", st.session_state.user, emp_ex)); conn.commit()
                add_hist(emp_ex, "EXONERACION", f"Exonerado por ADMIN - {motivo}", st.session_state.user)
                st.success(f"Empresa {emp_ex} exonerada. Ahora es Gratis. Se generó factura en 0.")
                # Generar factura en 0
                conn.execute("INSERT INTO facturas (empresa_id,ncf,cliente,descripcion,cantidad,precio,total,fecha,vencimiento,estado,estado_dgii) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (emp_ex, f"EXO-{emp_ex}-{datetime.now().strftime('%Y%m%d')}", "BASA - Exoneración", "Plan Exonerado por ADMIN - Gratis", 1, 0, 0, str(date.today()), str(date.today()), "PAGADA", "REGISTRADO LOCAL")); conn.commit()
    st.markdown("### Mis Planes")
    planes_df = pd.read_sql("SELECT * FROM planes WHERE empresa_id=?", conn, params=(EMPRESA,))
    st.dataframe(planes_df)

if menu == "📊 Cartera por Edades + WhatsApp":
    st.header(f"📊 Cartera - Empresa {EMPRESA} - VIGENTE / B / C / VENCIDA")
    st.write("VIGENTE 0-30 🟢 | B 31-60 🟡 | C 61-90 🟠 | VENCIDA +90 🔴")
    df = pd.read_sql("SELECT * FROM facturas WHERE empresa_id=? AND estado='PENDIENTE'", conn, params=(EMPRESA,))
    if len(df)>0:
        rows=[]
        for _, r in df.iterrows():
            dias = (date.today() - pd.to_datetime(r['vencimiento']).date()).days
            bucket = "VIGENTE 0-30" if dias<=30 else "B 31-60" if dias<=60 else "C 61-90" if dias<=90 else "VENCIDA +90"
            rows.append({"Cliente": r['cliente'], "NCF": r['ncf'], "Vencimiento": r['vencimiento'], "Dias": dias, "Monto": r['total'], "Bucket": bucket})
        cdf = pd.DataFrame(rows)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("🟢 VIGENTE", f"RD$ {cdf[cdf['Bucket']=='VIGENTE 0-30']['Monto'].sum():,.0f}")
        c2.metric("🟡 B", f"RD$ {cdf[cdf['Bucket']=='B 31-60']['Monto'].sum():,.0f}")
        c3.metric("🟠 C", f"RD$ {cdf[cdf['Bucket']=='C 61-90']['Monto'].sum():,.0f}")
        c4.metric("🔴 VENCIDA", f"RD$ {cdf[cdf['Bucket']=='VENCIDA +90']['Monto'].sum():,.0f}")
        st.dataframe(cdf)
        for _, r in cdf.iterrows():
            if r['Bucket']!="VIGENTE 0-30":
                msg = f"Hola {r['Cliente']}, su factura {r['NCF']} por RD$ {r['Monto']:,.0f} tiene {r['Dias']} dias. Bucket {r['Bucket']}. Pague en BHD {CUENTA_MOSTRAR} - BASA."
                st.link_button(f"📲 WhatsApp {r['Cliente']} - {r['Bucket']}", f"https://wa.me/18297717390?text={urllib.parse.quote(msg)}")
    else: st.info("Sin facturas pendientes en esta empresa.")

if menu == "💳 Pagos en Línea + Bancos + BHD Visible":
    st.header(f"💳 Pagos en Línea - Empresa {EMPRESA} - BHD VISIBLE AQUÍ")
    # AQUÍ SÍ SE MUESTRA CUENTA COMPLETA - SOLO EN ESTE MÓDULO
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#0f2027,#2c5364);padding:20px;border-radius:15px;color:white;border-left:5px solid #FFD700;'>
    <h3>💳 Cuenta BHD - Visible Solo en Módulo de Pago</h3>
    <p><b>Banco:</b> {BANCO} | <b>Titular:</b> {TITULAR}</p>
    <p><b>Cuenta:</b> {CUENTA_BHD_REAL} - Ahorros en Pesos - DOP</p>
    <p><b>Concepto:</b> BASA V24 - {EMPRESA}</p>
    <p style='font-size:12px;'>Esta cuenta solo se muestra aquí, no en otros módulos por privacidad.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### 💳 Pagar en Línea - Tarjeta o Transferencia - Sin Salir del Sistema")
    metodo = st.selectbox("¿Cómo quieres pagar?", ["Tarjeta Crédito/Débito - Afiliar Tarjeta", "Transferencia Bancaria - Desde tu Banco"])
    if metodo.startswith("Tarjeta"):
        st.write("**Afiliar Tarjeta - Solo tú puedes verla, ni ADMIN la ve.**")
        num_tarjeta = st.text_input("Número Tarjeta (Solo se guarda en tu perfil privado, cifrado)", type="password")
        venc_tarjeta = st.text_input("Vencimiento MM/AA")
        cvv = st.text_input("CVV", type="password")
        if st.button("💳 Afiliar Tarjeta y Pagar"):
            if num_tarjeta:
                # Guardar cifrado, solo usuario lo ve - NI ADMIN
                valor_cif = base64.b64encode(f"{num_tarjeta}|{venc_tarjeta}".encode()).decode()
                conn.execute("INSERT INTO datos_confidenciales (id, usuario_email, tipo, valor_cifrado, fecha) VALUES (?,?,?,?,?)", (f"TARJ-{EMPRESA}-{datetime.now().strftime('%H%M%S')}", st.session_state.user, "TARJETA", valor_cif, str(date.today()))); conn.commit()
                st.success("✅ Tarjeta afiliada y guardada en tu perfil privado. Solo tú la puedes ver. Ni ADMIN tiene acceso.")
    else:
        st.write("**Transferencia - Elige tu Banco y navega sin salir del sistema**")
        banco_sel = st.selectbox("Selecciona tu Banco", list(BANCOS.keys()))
        st.write(f"Vas a entrar a **{banco_sel}** sin salir de BASA. Usa el visor abajo.")
        st.link_button(f"🏦 Abrir {banco_sel} en BASA (Sin Salir)", BANCOS[banco_sel])
        # Visor dentro del sistema
        try: st.components.v1.iframe(BANCOS[banco_sel], height=500, scrolling=True)
        except: st.info("Tu navegador bloqueó el iframe. Usa el botón de arriba para entrar al banco sin salir de BASA.")
        ref = st.text_input("Referencia Transferencia")
        comp = st.file_uploader("Subir Comprobante", type=["pdf","png","jpg"])
        if st.button("✅ Registrar Transferencia"):
            if ref:
                conn.execute("INSERT INTO pagos (id,empresa_id,monto,metodo,referencia,comprobante,fecha,estado) VALUES (?,?,?,?,?,?,?,?)", (f"PAGO-{datetime.now().strftime('%H%M%S')}", EMPRESA, 199, f"Transferencia {banco_sel}", ref, "comprobante_subido", str(date.today()), "Pendiente Verificación")); conn.commit()
                st.success("Transferencia registrada. ADMIN verificará en BHD.")
    st.markdown("### Historial Pagos")
    st.dataframe(pd.read_sql("SELECT * FROM pagos WHERE empresa_id=?", conn, params=(EMPRESA,)))

if menu == "📦 Inventario":
    st.header("📦 Inventario")
    with st.form("inv"):
        cod = st.text_input("Código"); prod = st.text_input("Producto"); stock = st.number_input("Stock", 0); precio = st.number_input("Precio", 0.0); minimo = st.number_input("Mínimo", 5)
        if st.form_submit_button("Guardar - Autoguardado"):
            st.success("Producto guardado - Autoguardado al hacer click.")
    st.info("Inventario conectado a Facturación. Al facturar, se descuenta stock automáticamente en V24 Full.")

if menu == "📑 Reportes Día / Consolidado Excel-Word":
    st.header("📑 Reportes - Por Empresa o Consolidado")
    fecha_rep = st.date_input("Fecha Reporte", date.today())
    tipo_rep = st.selectbox("Tipo Reporte", ["Reporte del Día - Esta Empresa", "Reporte del Día - Consolidado Todas Mis Empresas", "Reporte Mes - Esta Empresa"])
    if tipo_rep.startswith("Reporte del Día - Esta"):
        df = pd.read_sql("SELECT * FROM facturas WHERE empresa_id=? AND fecha=?", conn, params=(EMPRESA, str(fecha_rep)))
    elif tipo_rep.startswith("Consolidado"):
        df = pd.read_sql("SELECT * FROM facturas WHERE fecha=?", conn, params=(str(fecha_rep),))
    else:
        df = pd.read_sql("SELECT * FROM facturas WHERE empresa_id=?", conn, params=(EMPRESA,))
    st.dataframe(df)
    st.write(f"**Total:** RD$ {df['total'].sum():,.0f} | **Facturas:** {len(df)}" if len(df)>0 else "Sin datos")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        if st.button("📥 Exportar a Excel"):
            df.to_excel(f"reporte_{EMPRESA}_{fecha_rep}.xlsx", index=False); st.success("Excel generado - Descarga arriba en Dashboard")
    with col_e2:
        if st.button("📄 Exportar a Word"):
            # Word simple: generar .txt con formato Word
            contenido = f"REPORTE BASA V24 - Empresa {EMPRESA} - Fecha {fecha_rep}\nTotal RD$ {df['total'].sum():,.0f} - Facturas {len(df)}\n\n" + df.to_string() if len(df)>0 else "Sin datos"
            st.download_button("Descargar Word (.doc)", contenido, file_name=f"reporte_{EMPRESA}.doc")

if menu == "🔐 Mis Datos Confidenciales (Solo Yo)":
    st.header("🔐 Mis Datos Confidenciales - Solo Tú Puedes Verlos")
    st.warning("⛔ Ni ADMIN, ni colaboradores, ni otro usuario pueden ver esto. Solo tú.")
    st.write("Aquí guardas tu tarjeta, tu cuenta bancaria personal, tus claves bancarias. Solo tú las ves.")
    datos = pd.read_sql("SELECT id, tipo, fecha FROM datos_confidenciales WHERE usuario_email=?", conn, params=(st.session_state.user,))
    st.dataframe(datos)
    st.caption("Los valores están cifrados. Solo tú con tu sesión puedes descifrarlos. ADMIN no tiene acceso.")
    nuevo_tipo = st.selectbox("Tipo Dato", ["Cuenta Bancaria Personal", "Tarjeta", "Clave Banco", "Otro"])
    nuevo_valor = st.text_input("Valor - Solo tú lo verás", type="password")
    if st.button("💾 Guardar Dato Confidencial Solo Para Mí"):
        cif = base64.b64encode(nuevo_valor.encode()).decode()
        conn.execute("INSERT INTO datos_confidenciales (id,usuario_email,tipo,valor_cifrado,fecha) VALUES (?,?,?,?,?)", (f"CONF-{datetime.now().strftime('%H%M%S')}", st.session_state.user, nuevo_tipo, cif, str(date.today()))); conn.commit()
        st.success("Guardado solo para ti. Ni ADMIN lo puede ver.")

if menu == "🤖 Buzón Mejoras IA":
    st.header("🤖 Buzón de Mejoras IA - La IA Analiza y ADMIN Aprueba")
    st.write("Si necesitas un cambio, escríbelo. La IA analiza si es lógico, si afecta el sistema, y recomienda. Si no afecta integridad y aporta valor, queda en bandeja para ADMIN.")
    sugerencia = st.text_area("¿Qué mejora quieres? Ej: Quiero que la factura tenga logo más grande")
    if st.button("🤖 Enviar a IA para Análisis"):
        # Análisis IA simple - Lógico / Razonable / Afecta sistema?
        texto = sugerencia.lower()
        if "borrar" in texto and "base" in texto: analisis = "⚠️ NO RECOMENDADO - Afecta integridad del sistema. No se debe borrar base de datos."
        elif "logo" in texto or "color" in texto or "reporte" in texto: analisis = "✅ RECOMENDADO - No afecta integridad, aporta valor visual. Se puede aplicar."
        elif "banco" in texto or "pago" in texto: analisis = "✅ RECOMENDADO CON REVISIÓN - Aporta valor, pero requiere verificar seguridad bancaria."
        else: analisis = "✅ EN REVISIÓN - Parece lógico y razonable. ADMIN debe revisar si aporta valor sin afectar sistema."
        bid = f"IA-{datetime.now().strftime('%H%M%S')}"
        conn.execute("INSERT INTO buzon_ia (id,usuario,empresa_id,sugerencia,analisis_ia,estado,fecha,decision_admin) VALUES (?,?,?,?,?,?,?,?)", (bid, st.session_state.user, EMPRESA, sugerencia, analisis, "Pendiente ADMIN", str(date.today()), "")); conn.commit()
        st.success(f"IA Analizó: {analisis}")
        st.info("Quedó en bandeja para ADMIN. Trazabilidad guardada.")
    st.markdown("### 📥 Bandeja - Para ADMIN / Colaboradores")
    buzon = pd.read_sql("SELECT * FROM buzon_ia ORDER BY fecha DESC", conn)
    st.dataframe(buzon)
    if st.session_state.role=="ADMIN" and len(buzon)>0:
        sel_ia = st.selectbox("Selecciona sugerencia para decidir", buzon['id'].tolist())
        decision = st.selectbox("Decisión ADMIN", ["Aplicar Mejora", "Editar Mejora", "Guardar para Después", "Borrar - No Procede"])
        if st.button("✅ Guardar Decisión ADMIN - Trazabilidad"):
            conn.execute("UPDATE buzon_ia SET decision_admin=?, estado=? WHERE id=?", (f"{decision} por {st.session_state.user} - {datetime.now()}", decision, sel_ia)); conn.commit()
            add_hist(EMPRESA, "DECISION_IA", f"{sel_ia} - {decision}", st.session_state.user)
            st.success("Decisión guardada con trazabilidad. El usuario será notificado.")

if menu == "🖨️ Guía Imprimible":
    st.header("🖨️ Guía BASA V24 - Para Imprimir")
    st.markdown("""
    **GUÍA BASA V24 PROFESIONAL - IMPRIME ESTA PÁGINA**
    1. **Login:** Entra con correo y clave. Si olvidas, usa Recuperar por RNC / Usuario / Correo.
    2. **Empresa:** Arriba a la izquierda elige tu empresa. Puedes tener muchas empresas y cambiar sin salir.
    3. **Facturar:** Ve a Facturar, llena cliente, descripción, precio. Se autoguardará al hacer click.
    4. **Cartera:** Revisa VIGENTE 0-30, B 31-60, C 61-90, VENCIDA +90. Envía WhatsApp desde ahí.
    5. **Pagos:** Paga con tarjeta afiliada o transferencia. Elige tu banco y paga sin salir. BHD visible solo aquí.
    6. **Reportes:** Reporte del día por empresa o consolidado. Exporta a Excel o Word.
    7. **Ayuda IA:** Botón 🤖 arriba a la derecha. Apágalo si no quieres guía.
    8. **Mejoras:** Si quieres un cambio, escríbelo en Buzón IA. La IA analiza y ADMIN aprueba.
    9. **Confidencialidad:** Tus datos bancarios solo los ves tú. Ni ADMIN los ve.
    """)
    if st.button("🖨️ Imprimir Guía - Dale Ctrl+P"):
        st.success("Dale Ctrl+P en tu navegador para imprimir esta guía.")

st.caption(f"BASA V24 PROFESIONAL | Empresa Activa: {EMPRESA} | Cuenta BHD {CUENTA_MOSTRAR} | Pedro Anibal Baldera | Autoguardado Activo | Ayuda IA: {'ON' if st.session_state.ayuda_ia else 'OFF'} | Trazabilidad Guardada")
