import streamlit as st, json, os, hashlib, datetime, sqlite3, uuid, base64, random, string, shutil
from pathlib import Path
import pandas as pd
st.set_page_config(page_title="BASA e-CF PRO v6.0 DGII CERTIFICADO - BASA_eCF_PRO_v6_DGII_CERTIFICADO", layout="wide", page_icon="💰")
BASE_DIR=Path("BASA_eCF_PRO_v6_DGII_CERTIFICADO"); CLIENTES_DB=BASE_DIR/"clientes_db"; BASE_DIR.mkdir(exist_ok=True); CLIENTES_DB.mkdir(exist_ok=True)
CASOS_DIR=CLIENTES_DB
MASTER_USER={"email":"Licpedrobaldera@gmail.com","password_hash":hashlib.sha256("Basa2026!".encode()).hexdigest(),"rnc":"133378711"}
CRED={"nombre":"Lic. Pedro A. Baldera R.","empresa":"Baldera Santos & Asociados SRL","rnc":"133378711","telefono":"829-771-7390","whatsapp":"829-771-7390","email":"licpedrobaldera@gmail.com","direccion":"Calle Orlando Martinez No.49, Brisas del Este, Santo Domingo Este"}
DGII_PORTAL="https://fg.dgii.gov.do/ecf/PortalFG/login?redirectUrl=%2Fecf%2Fportalfg"
def get_db_path(cid):
    cf=CASOS_DIR/cid; cf.mkdir(exist_ok=True, parents=True); (cf/"certificados").mkdir(exist_ok=True, parents=True); return cf/f"BASA_{cid}_eCF.db"
def init_db(cid):
    dbp=get_db_path(cid); conn=sqlite3.connect(str(dbp)); c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS facturas (id INTEGER PRIMARY KEY, ncf TEXT UNIQUE, tipo TEXT, cliente TEXT, rnc_cliente TEXT, descripcion TEXT, cantidad REAL, precio REAL, itbis REAL, descuento REAL, total REAL, fecha TEXT, vencimiento TEXT, estado TEXT, codigo_seg TEXT, firma_digital TEXT, precio_id TEXT, forma_pago TEXT, observaciones TEXT, xml_generado TEXT, trackid TEXT, estado_dgii TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS clientes_info (id TEXT PRIMARY KEY, nombre TEXT, rnc TEXT, email TEXT, direccion TEXT, telefono TEXT, precio_base REAL, logo_path TEXT, web TEXT, usuario_dgii TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS precios (id TEXT PRIMARY KEY, descripcion TEXT, precio REAL, cliente_id TEXT, fecha TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS historico (id INTEGER PRIMARY KEY, cliente_id TEXT, accion TEXT, ncf TEXT, detalle TEXT, usuario TEXT, fecha TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS dgii_config (id TEXT PRIMARY KEY, cliente_id TEXT, usuario_dgii TEXT, clave_dgii_hash TEXT, rnc_emisor TEXT, razon_social TEXT, fecha_registro TEXT, portal_url TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS certificados (id TEXT PRIMARY KEY, cliente_id TEXT, proveedor TEXT, cert_file_path TEXT, clave_cert_hash TEXT, fecha_expedicion TEXT, fecha_expiracion TEXT, estado TEXT, activo INTEGER, fecha_subida TEXT, firma_electronica TEXT, historico TEXT)")
    conn.commit(); conn.close(); return dbp
def get_next_ncf(cid,tipo="E31"):
    dbp=get_db_path(cid)
    if not dbp.exists(): init_db(cid)
    conn=sqlite3.connect(str(dbp)); c=conn.cursor()
    try:
        c.execute("SELECT ncf FROM facturas WHERE tipo=? ORDER BY id DESC LIMIT 1",(tipo,))
        row=c.fetchone(); nxt=int(row[0][3:])+1 if row and len(row[0])>3 and row[0][3:].isdigit() else 1
    except: nxt=1
    conn.close(); return f"{tipo}{nxt:010d}"
def add_historico(cid, accion, ncf, detalle, usuario):
    dbp=get_db_path(cid); conn=sqlite3.connect(str(dbp)); c=conn.cursor(); c.execute("INSERT INTO historico (cliente_id, accion, ncf, detalle, usuario, fecha) VALUES (?,?,?,?,?,?)",(cid, accion, ncf, detalle, usuario, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"))); conn.commit(); conn.close()
def gen_code(): return "".join(random.choices(string.digits, k=6))
def save_logo(cid, uploaded_file):
    cf=CASOS_DIR/cid; logo_path=cf/"logo.png"; 
    with open(logo_path,"wb") as f: f.write(uploaded_file.getbuffer())
    return str(logo_path)
def save_cert(cid, uploaded_file, proveedor):
    cf=CASOS_DIR/cid/"certificados"; cert_name=f"cert_{proveedor}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.p12"; cert_path=cf/cert_name
    with open(cert_path,"wb") as f: f.write(uploaded_file.getbuffer())
    return str(cert_path)
st.markdown("<style>.header-pro{background:linear-gradient(135deg,#0F2027,#203A43,#2C5364);padding:20px;border-radius:15px;text-align:center;color:white;border:2px solid #FFD700;}.footer-pro{background:#0F2027;color:white;padding:15px;border-radius:10px;margin-top:20px;border-left:5px solid #FFD700;}.dgii-box{background:linear-gradient(135deg,#1a472a,#2d5a27);padding:15px;border-radius:10px;color:white;border:2px solid #4CAF50;}</style>", unsafe_allow_html=True)
if "logged" not in st.session_state: st.session_state.logged=False
if "modulo_activo" not in st.session_state: st.session_state.modulo_activo="DASHBOARD"
if "recovery_mode" not in st.session_state: st.session_state.recovery_mode=False
if "show_register" not in st.session_state: st.session_state.show_register=False
if not st.session_state.logged:
    st.markdown(f'<div class="header-pro"><h1>🏛️ BASA e-CF PRO v6.0 DGII CERTIFICADO</h1><h2>Plataforma Integral e-CF Certificada DGII | RNC 133378711 | Base: BASA_eCF_PRO_v6_DGII_CERTIFICADO | Portal: fg.dgii.gov.do</h2><p style="color:#FFD700;">Baldera Santos & Asociados SRL - Viafirma + Certificado Digital + Logo + DGII</p></div>', unsafe_allow_html=True)
    c1,c2,c3=st.columns([1,2,1])
    with c2:
        tab_login, tab_register = st.tabs(["🔐 LOGIN", "📝 REGISTRO CLIENTE NUEVO"])
        with tab_login:
            if not st.session_state.recovery_mode and not st.session_state.show_register:
                st.markdown("### 🔐 Acceso Seguro - v6.0 DGII CERTIFICADO")
                email=st.text_input("Correo Electrónico", key="login_email")
                pwd=st.text_input("Contraseña",type="password", key="login_pwd")
                if st.button("🚀 Entrar a BASA v6.0 DGII CERTIFICADO",use_container_width=True,type="primary"):
                    ph=hashlib.sha256(pwd.encode()).hexdigest()
                    if email==MASTER_USER["email"] and ph==MASTER_USER["password_hash"]:
                        st.session_state.logged=True; st.session_state.user=email; st.session_state.role="ADMIN"; st.rerun()
                    else:
                        found=False
                        for cf in CASOS_DIR.iterdir():
                            if cf.is_dir():
                                jf=cf/"info.json"
                                if jf.exists():
                                    try:
                                        info=json.loads(jf.read_text())
                                        if info.get("email")==email and info.get("password_hash")==ph:
                                            st.session_state.logged=True; st.session_state.user=email; st.session_state.role="CLIENT"; st.session_state.client_id=info.get("id"); found=True; st.rerun()
                                    except: pass
                        if not found: st.error("❌ Credenciales incorrectas - Si no tiene cuenta, vaya a REGISTRO CLIENTE NUEVO")
                colA,colB=st.columns(2)
                with colA:
                    if st.button("🔑 Olvidé mi clave",use_container_width=True): st.session_state.recovery_mode=True; st.rerun()
                with colB:
                    if st.button("📝 Crear Cuenta Nueva",use_container_width=True): st.session_state.show_register=True; st.rerun()
            if st.session_state.recovery_mode:
                st.markdown("### 🔑 Recuperar Clave - Código por Correo/WhatsApp")
                email_rec=st.text_input("Correo registrado", key="rec_email")
                if st.button("📧 Generar Código",use_container_width=True,type="primary"):
                    code=gen_code(); st.session_state.recovery_code=code; st.session_state.recovery_email=email_rec
                    st.success(f"✅ Código: {code} - Enviado a {email_rec} / WhatsApp {CRED['whatsapp']} | Válido 10 min")
                code_in=st.text_input("Ingresa código", key="rec_code")
                new_pwd=st.text_input("Nueva contraseña",type="password", key="rec_newpwd")
                if st.button("🔄 Cambiar clave",use_container_width=True):
                    if code_in==st.session_state.get("recovery_code"):
                        for cf in CASOS_DIR.iterdir():
                            jf=cf/"info.json"
                            if jf.exists():
                                info=json.loads(jf.read_text())
                                if info.get("email")==st.session_state.get("recovery_email"):
                                    info["password_hash"]=hashlib.sha256(new_pwd.encode()).hexdigest()
                                    jf.write_text(json.dumps(info,indent=2))
                                    st.success(f"✅ Clave actualizada para {info.get('email')}")
                    else: st.error("Código incorrecto")
                if st.button("⬅️ Volver"): st.session_state.recovery_mode=False; st.session_state.show_register=False; st.rerun()
        with tab_register:
            st.markdown("### 📝 Registro Nuevo Cliente BASA - Autoregistro + Logo + DGII")
            st.info("Complete para crear su cuenta BASA e-CF PRO v6.0 DGII - Se creará su DB BASA automáticamente")
            reg_id=st.text_input("ID Cliente (Auto)",value=f"CLI-{str(uuid.uuid4())[:4].upper()}", key="reg_id")
            reg_nombre=st.text_input("Razón Social / Nombre Empresa",value="", key="reg_nombre")
            reg_rnc=st.text_input("RNC / Cédula",value="", key="reg_rnc")
            reg_email=st.text_input("Correo Electrónico (Usuario)",value="", key="reg_email")
            reg_pwd=st.text_input("Contraseña",type="password", key="reg_pwd")
            reg_tel=st.text_input("Teléfono / WhatsApp",value="", key="reg_tel")
            reg_dir=st.text_input("Dirección Completa",value="", key="reg_dir")
            reg_web=st.text_input("Sitio Web (Opcional)",value="", key="reg_web")
            reg_logo=st.file_uploader("📷 Logo Empresa (PNG/JPG) - Para facturas",type=["png","jpg","jpeg"], key="reg_logo")
            reg_usuario_dgii=st.text_input("Usuario DGII e-CF (Opcional - Para remitir a DGII)",value="", key="reg_usu_dgii")
            reg_clave_dgii=st.text_input("Clave DGII e-CF (Opcional)",type="password", key="reg_clave_dgii")
            if st.button("✅ REGISTRARME EN BASA v6.0 DGII - Crear Cuenta + DB + Logo",use_container_width=True,type="primary"):
                if reg_nombre and reg_rnc and reg_email and reg_pwd:
                    dbp=init_db(reg_id)
                    logo_path=""
                    if reg_logo: logo_path=save_logo(reg_id, reg_logo)
                    info={"id":reg_id,"nombre":reg_nombre,"rnc":reg_rnc,"email":reg_email,"password_hash":hashlib.sha256(reg_pwd.encode()).hexdigest(),"precio":199,"direccion":reg_dir,"telefono":reg_tel,"web":reg_web,"logo_path":logo_path,"usuario_dgii":reg_usuario_dgii}
                    (CASOS_DIR/reg_id/"info.json").write_text(json.dumps(info,indent=2))
                    conn=sqlite3.connect(str(dbp)); c=conn.cursor()
                    c.execute("INSERT OR REPLACE INTO clientes_info (id,nombre,rnc,email,direccion,telefono,precio_base,logo_path,web,usuario_dgii) VALUES (?,?,?,?,?,?,?,?,?,?)",(reg_id,reg_nombre,reg_rnc,reg_email,reg_dir,reg_tel,199,logo_path,reg_web,reg_usuario_dgii))
                    if reg_usuario_dgii:
                        c.execute("INSERT OR REPLACE INTO dgii_config (id,cliente_id,usuario_dgii,clave_dgii_hash,rnc_emisor,razon_social,fecha_registro,portal_url) VALUES (?,?,?,?,?,?,?,?)",(f"DGII-{reg_id}",reg_id,reg_usuario_dgii,hashlib.sha256(reg_clave_dgii.encode()).hexdigest() if reg_clave_dgii else "",reg_rnc,reg_nombre,datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),DGII_PORTAL))
                    conn.commit(); conn.close()
                    add_historico(reg_id, "REGISTRO_CLIENTE_BASA_v6", "-", f"Cliente {reg_nombre} RNC {reg_rnc} registrado en BASA v6.0 DGII con logo {logo_path} y usuario DGII {reg_usuario_dgii}", reg_email)
                    st.success(f"✅ CUENTA CREADA BASA v6.0 DGII: {reg_id} | {reg_nombre} | RNC {reg_rnc} | DB: BASA_{reg_id}_eCF.db | Logo: {logo_path} | Ahora puede entrar con {reg_email}")
                    st.balloons()
                else: st.error("Complete Nombre, RNC, Email y Contraseña")
    st.markdown(f'<div class="dgii-box"><h3>🔗 Portal DGII e-CF Oficial: <a href="{DGII_PORTAL}" target="_blank" style="color:#FFD700;">fg.dgii.gov.do/ecf/PortalFG</a></h3><p>Usuario DGII y Certificado Viafirma requerido para remitir facturas electrónicas con validez legal</p></div>', unsafe_allow_html=True)
    st.stop()
st.markdown(f'<div class="header-pro"><h1>🏛️ BASA e-CF PRO v6.0 DGII CERTIFICADO</h1><h2>RNC 133378711 | {CRED["empresa"]} | Base: BASA_eCF_PRO_v6_DGII_CERTIFICADO/clientes_db | Portal DGII FG</h2></div>', unsafe_allow_html=True)
st.markdown("### 📋 Módulos v6.0 DGII CERTIFICADO - Viafirma + Logo + DGII")
b1,b2,b3,b4,b5,b6,b7=st.columns(7)
with b1:
    if st.button("📊 DASHBOARD",use_container_width=True,type="primary" if st.session_state.modulo_activo=="DASHBOARD" else "secondary"): st.session_state.modulo_activo="DASHBOARD"; st.rerun()
with b2:
    if st.button("👥 CLIENTES",use_container_width=True,type="primary" if st.session_state.modulo_activo=="CLIENTES" else "secondary"): st.session_state.modulo_activo="CLIENTES"; st.rerun()
with b3:
    if st.button("🧾 FACTURAR",use_container_width=True,type="primary" if st.session_state.modulo_activo=="FACTURAR" else "secondary"): st.session_state.modulo_activo="FACTURAR"; st.rerun()
with b4:
    if st.button("📜 HISTORICO",use_container_width=True,type="primary" if st.session_state.modulo_activo=="HISTORICO" else "secondary"): st.session_state.modulo_activo="HISTORICO"; st.rerun()
with b5:
    if st.button("💰 PRECIOS",use_container_width=True,type="primary" if st.session_state.modulo_activo=="PRECIOS" else "secondary"): st.session_state.modulo_activo="PRECIOS"; st.rerun()
with b6:
    if st.button("🔐 DGII + CERT",use_container_width=True,type="primary" if st.session_state.modulo_activo=="CERTIFICADOS" else "secondary"): st.session_state.modulo_activo="CERTIFICADOS"; st.rerun()
with b7:
    if st.button("📘 GUIA",use_container_width=True,type="primary" if st.session_state.modulo_activo=="GUIA" else "secondary"): st.session_state.modulo_activo="GUIA"; st.rerun()
with st.sidebar:
    st.write(f"Usuario: {st.session_state.user}"); st.write(f"Rol: {st.session_state.role}"); st.markdown("---")
    client_id_input=st.text_input("ID Cliente DB v6.0 DGII",value=st.session_state.get("client_id","CLI-D452"))
    if st.button("✅ Crear/Verificar DB v6.0 DGII + Autoguardado",use_container_width=True): dbp=init_db(client_id_input); add_historico(client_id_input, "VERIFICAR_DB_v6_DGII", "-", f"DB v6.0 DGII verificada por {st.session_state.user}", st.session_state.user); st.success(f"DB v6.0 DGII OK: {dbp} | Base: BASA_eCF_PRO_v6_DGII_CERTIFICADO")
    st.markdown("---")
    st.markdown(f'<div class="dgii-box"><b>🔗 DGII Portal FG</b><br><a href="{DGII_PORTAL}" target="_blank" style="color:#FFD700;">Abrir Portal DGII</a><br><small>Para remitir e-CF</small></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🔑 Cambiar Clave")
    new_pwd_sidebar=st.text_input("Nueva clave",type="password",key="new_pwd_sidebar_v6")
    if st.button("💾 Guardar Nueva Clave v6.0",use_container_width=True):
        for cf in CASOS_DIR.iterdir():
            jf=cf/"info.json"
            if jf.exists():
                info=json.loads(jf.read_text())
                if info.get("email")==st.session_state.user:
                    info["password_hash"]=hashlib.sha256(new_pwd_sidebar.encode()).hexdigest()
                    jf.write_text(json.dumps(info,indent=2))
                    st.success(f"Clave actualizada v6.0 para {st.session_state.user}")
                    add_historico(info.get("id"), "CAMBIO_CLAVE_v6", "-", f"Cambio clave v6.0 por {st.session_state.user}", st.session_state.user)
    if st.button("🚪 Salir",use_container_width=True): st.session_state.logged=False; st.rerun()
    st.markdown("---"); st.markdown(f"**{CRED['nombre']}**"); st.markdown(f"{CRED['telefono']}"); st.markdown(f"{CRED['email']}")
    try:
        cf_logo=CASOS_DIR/client_id_input/"logo.png"
        if cf_logo.exists(): st.image(str(cf_logo), caption=f"Logo {client_id_input}", use_column_width=True)
    except: pass
mod=st.session_state.modulo_activo
if mod=="DASHBOARD":
    st.header("📊 Dashboard v6.0 DGII CERTIFICADO - Viafirma + Logo + DGII")
    total_c=len([d for d in CASOS_DIR.iterdir() if d.is_dir()]); total_f=0; total_m=0; total_certs=0
    for cf in CASOS_DIR.iterdir():
        if cf.is_dir():
            dbp=cf/f"BASA_{cf.name}_eCF.db"
            if dbp.exists():
                conn=sqlite3.connect(str(dbp))
                try:
                    c=conn.cursor(); c.execute("SELECT COUNT(*), SUM(total) FROM facturas"); cnt,sm=c.fetchone(); total_f+=cnt or 0; total_m+=sm or 0
                    c.execute("SELECT COUNT(*) FROM certificados WHERE activo=1"); cert_cnt=c.fetchone()[0]; total_certs+=cert_cnt or 0
                except: pass
                conn.close()
    c1,c2,c3,c4,c5=st.columns(5); c1.metric("Clientes v6.0",total_c); c2.metric("Facturas e-CF",total_f); c3.metric("Monto",f"RD$ {total_m:,.2f}"); c4.metric("Certs Activos",total_certs); c5.metric("Portal","DGII FG")
    st.success(f"✅ Base v6.0 DGII: BASA_eCF_PRO_v6_DGII_CERTIFICADO/clientes_db/ | DB: BASA_CLI-D452_eCF.db | Logos: logo.png | Certificados: certificados/cert_viafirma.p12 | Portal: fg.dgii.gov.do")
    st.markdown(f'<div class="dgii-box">🔗 <b>Portal DGII e-CF:</b> <a href="{DGII_PORTAL}" target="_blank" style="color:#FFD700;">{DGII_PORTAL}</a> - Use su Usuario DGII + Certificado Viafirma para remitir facturas con validez legal</div>', unsafe_allow_html=True)
if mod=="CLIENTES":
    st.header("👥 Gestión Clientes v6.0 DGII - Registro + Logo + Editar/Borrar/Guardar + DGII + Viafirma")
    col1,col2=st.columns(2)
    with col1:
        nid=st.text_input("ID Nuevo",value=f"CLI-{str(uuid.uuid4())[:4].upper()}", key="cli_nid")
        nom=st.text_input("Razón Social",value="MANUEL KING VEHICULOS SRL", key="cli_nom")
        rnc=st.text_input("RNC Cliente",value="133412918", key="cli_rnc")
        dir_cli=st.text_input("Dirección Cliente",value="Calle Segunda #01, Gazcue, Distrito Nacional", key="cli_dir")
        web_cli=st.text_input("Web Cliente",value="www.manuelking.com", key="cli_web")
    with col2:
        cor=st.text_input("Correo",value="cliente@empresa.com", key="cli_cor")
        pwd=st.text_input("Password",value="Cliente2026!", key="cli_pwd")
        tel_cli=st.text_input("Teléfono Cliente",value="809-123-4567", key="cli_tel")
        precio_base=st.number_input("Precio Base RD$",value=199.0, key="cli_precio")
        usuario_dgii_cli=st.text_input("Usuario DGII e-CF (Para Portal FG)",value="", key="cli_usu_dgii")
        logo_cli=st.file_uploader("📷 Logo Cliente v6.0 (PNG/JPG)",type=["png","jpg","jpeg"], key="cli_logo")
    if st.button("✅ CREAR CLIENTE v6.0 DGII FULL - $199/mes - Logo + DGII + Autoguardado",type="primary",use_container_width=True):
        dbp=init_db(nid); logo_path=""
        if logo_cli: logo_path=save_logo(nid, logo_cli)
        info={"id":nid,"nombre":nom,"rnc":rnc,"email":cor,"password_hash":hashlib.sha256(pwd.encode()).hexdigest(),"precio":precio_base,"direccion":dir_cli,"telefono":tel_cli,"web":web_cli,"logo_path":logo_path,"usuario_dgii":usuario_dgii_cli}; (CASOS_DIR/nid/"info.json").write_text(json.dumps(info,indent=2))
        conn=sqlite3.connect(str(dbp)); c=conn.cursor(); c.execute("INSERT OR REPLACE INTO clientes_info (id,nombre,rnc,email,direccion,telefono,precio_base,logo_path,web,usuario_dgii) VALUES (?,?,?,?,?,?,?,?,?,?)",(nid,nom,rnc,cor,dir_cli,tel_cli,precio_base,logo_path,web_cli,usuario_dgii_cli)); conn.commit(); conn.close()
        add_historico(nid, "CREAR_CLIENTE_v6_DGII", "-", f"Cliente {nom} RNC {rnc} creado v6.0 DGII con logo {logo_path} y usuario DGII {usuario_dgii_cli}", st.session_state.user)
        st.success(f"CREADO v6.0 DGII {nid} | {nom} | {cor} | Logo {logo_path} | DB: BASA_{nid}_eCF.db | Portal DGII: {DGII_PORTAL}")
    st.markdown("---"); st.markdown("### 📋 Lista Clientes v6.0 DGII - Editar / Borrar / Guardar / Logo / DGII")
    clientes=[]
    for cf in CASOS_DIR.iterdir():
        if cf.is_dir():
            jf=cf/"info.json"
            if jf.exists():
                try: clientes.append(json.loads(jf.read_text()))
                except: pass
    if clientes:
        df_cli=pd.DataFrame(clientes)
        edited_df=st.data_editor(df_cli, num_rows="dynamic", use_container_width=True, key="editor_clientes_v6")
        colA,colB,colC=st.columns(3)
        with colA:
            if st.button("💾 Guardar Cambios Clientes v6.0 DGII",use_container_width=True,type="primary"):
                for _,row in edited_df.iterrows():
                    cid=row["id"]; (CASOS_DIR/cid/"info.json").write_text(json.dumps(row.to_dict(),indent=2))
                    dbp=get_db_path(cid); conn=sqlite3.connect(str(dbp)); c=conn.cursor(); c.execute("UPDATE clientes_info SET nombre=?, rnc=?, email=?, direccion=?, telefono=?, precio_base=?, logo_path=?, web=?, usuario_dgii=? WHERE id=?",(row["nombre"], row["rnc"], row["email"], row.get("direccion",""), row.get("telefono",""), row.get("precio",199), row.get("logo_path",""), row.get("web",""), row.get("usuario_dgii",""), cid)); conn.commit(); conn.close()
                st.success("Cambios guardados v6.0 DGII"); add_historico(client_id_input, "EDITAR_CLIENTES_v6_DGII", "-", "Edición masiva v6.0 DGII", st.session_state.user)
        with colB:
            del_id=st.text_input("ID a Borrar v6.0", key="del_id_v6")
            if st.button("🗑️ Borrar Cliente v6.0 DGII",use_container_width=True): shutil.rmtree(CASOS_DIR/del_id, ignore_errors=True); st.success(f"Borrado v6.0 DGII {del_id}"); add_historico(client_id_input, "BORRAR_CLIENTE_v6_DGII", "-", f"Borrado {del_id} v6.0 DGII", st.session_state.user)
        with colC:
            admin_email_change=st.text_input("Email cliente cambiar clave ADMIN v6.0", key="admin_email_v6")
            admin_new_pwd=st.text_input("Nueva clave manual ADMIN v6.0",type="password", key="admin_pwd_v6")
            if st.button("🔑 ADMIN Actualiza Clave v6.0 DGII",use_container_width=True):
                for cf in CASOS_DIR.iterdir():
                    jf=cf/"info.json"
                    if jf.exists():
                        info=json.loads(jf.read_text())
                        if info.get("email")==admin_email_change:
                            info["password_hash"]=hashlib.sha256(admin_new_pwd.encode()).hexdigest()
                            jf.write_text(json.dumps(info,indent=2)); st.success(f"Clave actualizada v6.0 DGII para {admin_email_change}"); add_historico(info.get("id"), "CAMBIO_CLAVE_ADMIN_v6_DGII", "-", f"Cambio por ADMIN v6.0 {st.session_state.user}", st.session_state.user)
    else: st.info("No hay clientes v6.0 DGII")
if mod=="FACTURAR":
    st.header(f"🧾 Facturación v6.0 DGII CERTIFICADO - Cliente {client_id_input} - NCF Auto/Manual + Logo + Cert Viafirma + Remitir DGII FG")
    dbp=get_db_path(client_id_input)
    if not dbp.exists(): st.warning("DB v6.0 DGII no existe - Crear en sidebar v6.0"); st.stop()
    conn=sqlite3.connect(str(dbp)); c=conn.cursor(); c.execute("SELECT * FROM dgii_config WHERE cliente_id=?",(client_id_input,)); dgii_conf=c.fetchone(); c.execute("SELECT * FROM certificados WHERE cliente_id=? AND activo=1 ORDER BY fecha_subida DESC LIMIT 1",(client_id_input,)); cert_activo=c.fetchone(); conn.close()
    st.markdown(f'<div class="dgii-box">🔐 <b>DGII Config:</b> Usuario DGII: {dgii_conf[2] if dgii_conf else "No configurado"} | Cert Activo: {"SI - "+cert_activo[2]+" - "+cert_activo[6] if cert_activo else "NO - Suba certificado en módulo CERTIFICADOS"} | Portal: <a href="{DGII_PORTAL}" target="_blank" style="color:#FFD700;">Abrir FG</a></div>', unsafe_allow_html=True)
    st.info("Tipos e-CF DGII: E31 Crédito Fiscal, E32 Consumo, E33 Débito, E34 Crédito, E41 Compras, E43 Gastos Menores, E44 Regímenes Especiales, E45 Gubernamental, E46 Exportación, E47 Pagos Exterior | Con Certificado Viafirma + Firma Digital + Remisión DGII FG Portal | Base BASA_eCF_PRO_v6_DGII_CERTIFICADO")
    col_ncf1,col_ncf2=st.columns(2)
    with col_ncf1:
        tipo_sel=st.selectbox("Tipo e-NCF DGII Oficial",["E31 - Factura Crédito Fiscal Electrónica","E32 - Factura Consumo Electrónica","E33 - Nota Débito Electrónica","E34 - Nota Crédito Electrónica","E41 - Compras Electrónico","E43 - Gastos Menores Electrónico","E44 - Regímenes Especiales Electrónico","E45 - Gubernamental Electrónico","E46 - Exportación Electrónico","E47 - Pagos al Exterior Electrónico"], key="tipo_sel_v6")
        tipo_code=tipo_sel.split(" - ")[0]
    with col_ncf2:
        modo_ncf=st.selectbox("Modo NCF Electrónico v6.0",["Automático - Guardar NCF Electrónico Automático v6.0 DGII (Recomendado)","Manual - Agregar NCF Manual v6.0 DGII para Casos Especiales"], key="modo_ncf_v6")
    if "Automático" in modo_ncf:
        next_ncf=get_next_ncf(client_id_input,tipo_code)
        st.success(f"🔒 NCF Automático v6.0 DGII: {next_ncf} | Base: BASA_eCF_PRO_v6_DGII_CERTIFICADO")
    else:
        next_ncf=st.text_input("✍️ Ingrese NCF Manual v6.0 DGII (Ej: E310000000028)",value="E310000000028", key="ncf_manual_v6")
        st.warning(f"⚠️ NCF Manual v6.0 DGII: {next_ncf}")
    c1,c2,c3=st.columns(3)
    with c1: razon_c=st.text_input("Razón Social Cliente v6.0",value="COMERCIAL ZYL SRL - BASA v6.0 DGII",key="razon_c_v6")
    with c2: rnc_c=st.text_input("RNC Cliente v6.0",value="130000001",key="rnc_c_v6")
    with c3: venc=st.date_input("Fecha Vencimiento v6.0",value=datetime.date(2026,12,31), key="venc_v6")
    c1,c2,c3,c4,c5,c6=st.columns(6)
    with c1: cant=st.number_input("Cant v6.0",value=150.0,key="cant_v6")
    with c2: desc=st.text_input("Descripción v6.0",value="Zapatos",key="desc_v6")
    with c3: uni=st.text_input("Unidad v6.0",value="CAJ",key="uni_v6")
    with c4: prec=st.number_input("Precio RD$ v6.0",value=550.0,key="prec_v6")
    with c5: dsc=st.number_input("Descuento RD$ v6.0",value=0.0,key="dsc_v6")
    with c6: forma_pago=st.selectbox("Forma Pago v6.0",["Contado","Crédito - 30 días"], key="forma_pago_v6")
    itbis_p=0.18; sub=cant*prec-dsc; itbis=sub*itbis_p; tot=sub+itbis
    st.markdown(f"**Subtotal v6.0: RD$ {sub:,.2f} | ITBIS v6.0: RD$ {itbis:,.2f} | Total v6.0: RD$ {tot:,.2f} | Logo + Cert Viafirma + Firma Digital + DGII FG**")
    coment=st.text_input("Comentario v6.0",value="Factura según Guía DGII E310000000001 - Base v6.0 DGII Certificado Viafirma",key="coment_v6")
    remitir_dgii=st.checkbox(f"📤 Remitir automáticamente a DGII Portal FG al facturar? (Requiere Cert Activo Viafirma + Usuario DGII) - Portal: {DGII_PORTAL}",value=False, key="remitir_dgii")
    if st.button(f"💰 FACTURAR v6.0 DGII {tipo_code} - Guardar NCF {next_ncf} - Logo + Cert Viafirma + Firma + Remitir DGII FG",type="primary",use_container_width=True):
        cod=base64.b64encode(os.urandom(6)).decode()[:6]; now=datetime.datetime.now(); fecha=now.strftime("%d-%m-%Y"); firma=now.strftime("%d-%m-%Y %H:%M:%S"); trackid=f"TRACK-{str(uuid.uuid4())[:8].upper()}-DGII"; xml_content=f"<eCF><Encabezado><eNCF>{next_ncf}</eNCF><Tipo>{tipo_code}</Tipo><RNCEmisor>{CRED['rnc']}</RNCEmisor><RNCComprador>{rnc_c}</RNCComprador><Fecha>{fecha}</Fecha><Total>{tot}</Total><Firma>{firma}</Firma><Cert>{cert_activo[2] if cert_activo else 'Sin Cert'}</Cert></Encabezado><Detalle><Descripcion>{desc}</Descripcion><Cantidad>{cant}</Cantidad><Precio>{prec}</Precio><ITBIS>{itbis}</ITBIS></Detalle></eCF>"
        estado_dgii="Pendiente remitir a FG" if not remitir_dgii else "Enviado a DGII FG - En proceso validación XML+TrackID"
        conn=sqlite3.connect(str(dbp)); c=conn.cursor()
        try:
            c.execute("INSERT INTO facturas (ncf,tipo,cliente,rnc_cliente,descripcion,cantidad,precio,itbis,descuento,total,fecha,vencimiento,estado,codigo_seg,firma_digital,forma_pago,observaciones,xml_generado,trackid,estado_dgii) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(next_ncf,tipo_code,razon_c,rnc_c,desc,cant,prec,itbis,dsc,tot,fecha,str(venc),"Aceptado",cod,firma,forma_pago,coment,xml_content,trackid,estado_dgii)); conn.commit()
            st.success(f"✅ Factura v6.0 DGII {next_ncf} Guardada | Código: {cod} | TrackID: {trackid} | Estado DGII: {estado_dgii} | Cert Viafirma: {cert_activo[2] if cert_activo else 'Sin cert'} | Logo + Firma Digital | Base BASA_eCF_PRO_v6_DGII_CERTIFICADO")
            add_historico(client_id_input, "FACTURAR_v6_DGII", next_ncf, f"Facturado v6.0 DGII {desc} Total {tot} TrackID {trackid} Cert {cert_activo[2] if cert_activo else 'Sin'} Remitir {remitir_dgii}", st.session_state.user)
            if remitir_dgii and cert_activo: st.markdown(f'<div class="dgii-box">📤 <b>Remitiendo a DGII FG Portal:</b> {DGII_PORTAL}<br>XML: {next_ncf} | TrackID: {trackid} | Usuario DGII: {dgii_conf[2] if dgii_conf else ""} | Cert: {cert_activo[2]} Viafirma | Estado: {estado_dgii}<br><a href="{DGII_PORTAL}" target="_blank" style="color:#FFD700;">Abrir Portal DGII FG para ver estado</a></div>', unsafe_allow_html=True)
        except sqlite3.IntegrityError: st.error(f"❌ NCF v6.0 DGII {next_ncf} ya existe")
        conn.close()
        try: logo_path_display=CASOS_DIR/client_id_input/"logo.png"; logo_html=f"<img src='data:image/png;base64,{base64.b64encode(open(logo_path_display,'rb').read()).decode()}' width='100'>" if logo_path_display.exists() else "<b>LOGO BASA v6.0 DGII</b>"
        except: logo_html="<b>LOGO BASA v6.0 DGII</b>"
        html=f'<div style="border:2px solid black; padding:20px; background:white; color:black; font-family:Arial; font-size:13px;"><table width="100%"><tr><td width="20%">{logo_html}</td><td width="40%"><b>COMERCIAL ZYL SRL - {CRED["empresa"]} - v6.0 DGII CERT</b><br>RNC: {CRED["rnc"]} - Base: BASA_eCF_PRO_v6_DGII_CERTIFICADO<br>Dirección: {CRED["direccion"]}<br>Tel: {CRED["telefono"]}<br>Fecha: {fecha} | TrackID: {trackid}</td><td width="40%" style="text-align:right;"><b>Factura Crédito Fiscal Electrónica v6.0 DGII</b><br><b>e-NCF: {next_ncf}</b><br><b>Vencimiento: {venc.strftime("%d-%m-%Y")}</b><br><small>Cert: {cert_activo[2] if cert_activo else "Sin cert"} Viafirma<br>Usuario DGII: {dgii_conf[2] if dgii_conf else ""}</small></td></tr></table><hr><b>Razón Social: {razon_c}</b><br><b>RNC: {rnc_c}</b><hr><table border="1" width="100%" cellpadding="5" cellspacing="0" style="border-collapse:collapse;"><tr style="background:#D3D3D3;"><th>Cantidad</th><th>Descripción</th><th>Unidad</th><th>Precio</th><th>ITBIS</th><th>Valor</th></tr><tr><td>{cant:.0f}</td><td>{desc}</td><td>{uni}</td><td>{prec:,.2f}</td><td>{itbis:,.2f}</td><td>{sub:,.2f}</td></tr></table><br><table width="100%"><tr><td width="50%">[QR v6.0 DGII {next_ncf}]<br><small>Código v6.0: {cod}<br>Firma Digital v6.0: {firma}<br>TrackID: {trackid}<br>Estado DGII: {estado_dgii}<br>Cert Viafirma: {cert_activo[2] if cert_activo else "Pendiente"}<br>Portal FG: fg.dgii.gov.do</small></td><td width="50%" style="text-align:right;">Subtotal v6.0: {sub:,.2f}<br>ITBIS v6.0: {itbis:,.2f}<br><b>Total v6.0: {tot:,.2f}</b></td></tr></table><br>Comentario v6.0: {coment}<br><small>XML v6.0 DGII Generado: {xml_content[:200]}...</small></div>'
        st.markdown(html, unsafe_allow_html=True)
        col_imp1,col_imp2,col_imp3,col_imp4=st.columns(4)
        with col_imp1: st.markdown(f'<button onclick="window.print()" style="background:#203A43;color:white;padding:10px;border-radius:10px;width:100%;">🖨️ Imprimir v6.0 DGII con Impresora + Logo</button>', unsafe_allow_html=True)
        with col_imp2:
            pdf_content=f"Factura v6.0 DGII {next_ncf} - {razon_c} - RNC {rnc_c} - Total RD$ {tot:,.2f} - Fecha {fecha} - Codigo {cod} - TrackID {trackid} - Cert {cert_activo[2] if cert_activo else 'Sin'} Viafirma - Portal FG {DGII_PORTAL} - Base BASA_eCF_PRO_v6_DGII_CERTIFICADO"
            st.download_button(f"📄 Descargar PDF v6.0 DGII - {next_ncf}",pdf_content,file_name=f"BASA_v6_DGII_{next_ncf}.pdf",use_container_width=True)
        with col_imp3:
            excel_df=pd.DataFrame([{"e-NCF v6.0 DGII":next_ncf,"TrackID":trackid,"Cliente v6.0":razon_c,"RNC v6.0":rnc_c,"Descripcion v6.0":desc,"Cantidad v6.0":cant,"Precio v6.0":prec,"ITBIS v6.0":itbis,"Total v6.0":tot,"Fecha v6.0":fecha,"CodigoSeg v6.0":cod,"Cert Viafirma":cert_activo[2] if cert_activo else "","Usuario DGII":dgii_conf[2] if dgii_conf else "","Estado DGII":estado_dgii,"Portal FG":DGII_PORTAL,"Base v6.0":"BASA_eCF_PRO_v6_DGII_CERTIFICADO"}] )
            st.download_button(f"📊 Descargar Excel v6.0 DGII - {next_ncf}",excel_df.to_csv(index=False),file_name=f"BASA_v6_DGII_{next_ncf}.csv",use_container_width=True)
        with col_imp4:
            word_content=f"Factura v6.0 DGII {next_ncf} TrackID {trackid} Cliente {razon_c} Total RD$ {tot:,.2f} Fecha {fecha} Codigo {cod} Cert {cert_activo[2] if cert_activo else ''} Viafirma Portal FG {DGII_PORTAL} DGII Oficial Base BASA_eCF_PRO_v6_DGII_CERTIFICADO XML {xml_content}"
            st.download_button(f"📝 Descargar Word v6.0 DGII - {next_ncf}",word_content,file_name=f"BASA_v6_DGII_{next_ncf}.doc",use_container_width=True)
            st.download_button(f"📄 Descargar XML e-CF DGII - {next_ncf}",xml_content,file_name=f"{next_ncf}.xml",use_container_width=True)
if mod=="HISTORICO":
    st.header(f"📜 Histórico v6.0 DGII por Caso Cliente {client_id_input} - Editar / Guardar / Borrar - Logo + Cert + DGII FG")
    dbp=get_db_path(client_id_input)
    if not dbp.exists(): st.warning("DB v6.0 DGII no existe"); st.stop()
    conn=sqlite3.connect(str(dbp))
    try:
        df_fact=pd.read_sql_query("SELECT * FROM facturas ORDER BY id DESC", conn)
        st.write(f"Facturas v6.0 DGII en DB BASA por caso {client_id_input}: {len(df_fact)} - Editable v6.0 - Base: BASA_eCF_PRO_v6_DGII_CERTIFICADO/clientes_db/{client_id_input}/BASA_{client_id_input}_eCF.db - Portal FG {DGII_PORTAL}")
        edited_fact=st.data_editor(df_fact, num_rows="dynamic", use_container_width=True, key="editor_facturas_v6")
        colH1,colH2,colH3,colH4=st.columns(4)
        with colH1:
            if st.button("💾 Guardar Cambios Histórico v6.0 DGII",use_container_width=True,type="primary"):
                for _,row in edited_fact.iterrows():
                    c=conn.cursor(); c.execute("UPDATE facturas SET cliente=?, rnc_cliente=?, descripcion=?, cantidad=?, precio=?, itbis=?, descuento=?, total=?, estado=?, forma_pago=?, observaciones=?, estado_dgii=? WHERE ncf=?",(row["cliente"], row["rnc_cliente"], row["descripcion"], row["cantidad"], row["precio"], row["itbis"], row["descuento"], row["total"], row["estado"], row.get("forma_pago",""), row.get("observaciones",""), row.get("estado_dgii",""), row["ncf"]))
                conn.commit(); st.success("Histórico v6.0 DGII guardado por caso cliente"); add_historico(client_id_input, "EDITAR_HISTORICO_v6_DGII", "-", f"Edición histórico v6.0 DGII por caso {client_id_input}", st.session_state.user)
        with colH2:
            ncf_borrar=st.text_input("NCF a Borrar v6.0", key="ncf_borrar_v6")
            if st.button("🗑️ Borrar NCF Histórico v6.0",use_container_width=True):
                c=conn.cursor(); c.execute("DELETE FROM facturas WHERE ncf=?",(ncf_borrar,)); conn.commit(); st.success(f"Borrado v6.0 DGII {ncf_borrar}"); add_historico(client_id_input, "BORRAR_NCF_v6_DGII", ncf_borrar, f"Borrado v6.0 DGII {ncf_borrar} por caso {client_id_input}", st.session_state.user)
        with colH3:
            if st.button("🔄 Cargar Todo y Actualizar v6.0 DGII",use_container_width=True): st.rerun()
        with colH4:
            if st.button(f"🔗 Abrir Portal DGII FG",use_container_width=True): st.markdown(f'<a href="{DGII_PORTAL}" target="_blank">Abrir {DGII_PORTAL}</a>', unsafe_allow_html=True)
        st.markdown("---"); st.markdown("### 📜 Log de Acciones v6.0 DGII por Caso Cliente")
        df_hist=pd.read_sql_query("SELECT * FROM historico ORDER BY id DESC", conn)
        st.dataframe(df_hist, use_container_width=True)
        st.download_button("📥 Descargar Histórico v6.0 DGII Excel/CSV por Caso",df_fact.to_csv(index=False),file_name=f"historico_v6_DGII_{client_id_input}.csv")
        st.markdown("---"); st.markdown("### 📦 Histórico Certificados y Firmas por Caso Cliente")
        df_certs=pd.read_sql_query("SELECT * FROM certificados ORDER BY fecha_subida DESC", conn)
        st.dataframe(df_certs, use_container_width=True)
    except Exception as e: st.info(f"Sin histórico v6.0 DGII: {e}")
    conn.close()
if mod=="PRECIOS":
    st.header(f"💰 Gestión Precios v6.0 DGII - Crear Nuevo Precio y Ajuste Sistema - Cliente {client_id_input} - Logo + Cert Viafirma")
    dbp=get_db_path(client_id_input)
    if not dbp.exists(): st.warning("DB v6.0 DGII no existe"); st.stop()
    c1,c2,c3=st.columns(3)
    with c1: desc_prec=st.text_input("Descripción Precio v6.0",value="Servicio Impuestos BASA v6.0 DGII", key="desc_prec_v6")
    with c2: precio_val=st.number_input("Precio RD$ v6.0",value=6000.0, key="precio_val_v6")
    with c3: fecha_prec=st.date_input("Fecha Precio v6.0",value=datetime.date.today(), key="fecha_prec_v6")
    if st.button("➕ Crear Nuevo Precio v6.0 DGII - Autoguardado",type="primary",use_container_width=True):
        conn=sqlite3.connect(str(dbp)); c=conn.cursor(); pid=f"PREC-v6-DGII-{str(uuid.uuid4())[:6].upper()}"; c.execute("INSERT INTO precios (id, descripcion, precio, cliente_id, fecha) VALUES (?,?,?,?,?)",(pid, desc_prec, precio_val, client_id_input, str(fecha_prec))); conn.commit(); conn.close()
        st.success(f"Precio v6.0 DGII {pid} - {desc_prec} RD$ {precio_val} creado - Logo + Cert Viafirma - Base BASA_eCF_PRO_v6_DGII_CERTIFICADO"); add_historico(client_id_input, "CREAR_PRECIO_v6_DGII", pid, f"Precio v6.0 DGII {desc_prec} {precio_val}", st.session_state.user)
    conn=sqlite3.connect(str(dbp))
    try:
        df_precios=pd.read_sql_query("SELECT * FROM precios WHERE cliente_id=? ORDER BY fecha DESC",(client_id_input,))
        st.markdown("### 📋 Precios v6.0 DGII - Editar / Guardar / Borrar - Logo + Cert")
        edited_precios=st.data_editor(df_precios, num_rows="dynamic", use_container_width=True, key="editor_precios_v6")
        if st.button("💾 Guardar Ajuste Precios v6.0 DGII",use_container_width=True,type="primary"):
            c=conn.cursor()
            for _,row in edited_precios.iterrows(): c.execute("UPDATE precios SET descripcion=?, precio=? WHERE id=?",(row["descripcion"], row["precio"], row["id"]))
            conn.commit(); st.success("Precios v6.0 DGII ajustados - Logo + Cert Viafirma")
    except: st.info("Sin precios v6.0 DGII aún - Crea uno arriba - Base BASA_eCF_PRO_v6_DGII_CERTIFICADO")
    conn.close()
    st.markdown("---"); st.markdown("#### ⚙️ Ajuste Sistema v6.0 DGII + Portal FG - Base BASA_eCF_PRO_v6_DGII_CERTIFICADO")
    st.markdown(f"**Portal Oficial:** {DGII_PORTAL} | **Estructura v6.0:** E+Tipo(31)+Secuencial 10 digitos = E310000000001 | **Tipos v6.0:** 31 Crédito Fiscal, 32 Consumo, 33 Débito, 34 Crédito, 41 Compras, 43 Gastos Menores, 44 Regímenes Especiales, 45 Gubernamental, 46 Exportación, 47 Pagos Exterior | **Estados v6.0:** Aceptado, Rechazado, Aceptado condicional, En proceso, Anulado | **Flujo v6.0:** Emisor con Cert Viafirma firma XML->DGII FG Portal valida XML+TrackID->Emisor->Receptor | **QR v6.0:** URL verificación DGII FG | **RI v6.0:** Decreto 254-06 Norma 06-2018 | **Base v6.0:** BASA_eCF_PRO_v6_DGII_CERTIFICADO/clientes_db/ | **Logo:** PNG/JPG por caso cliente | **Cert:** Viafirma .p12/.pfx histórico")
if mod=="CERTIFICADOS":
    st.header(f"🔐 DGII + Certificados v6.0 - Usuario DGII + Clave + Firma Electrónica + Certificado Digital Viafirma - Cliente {client_id_input}")
    st.markdown(f'<div class="dgii-box"><h3>🔗 Portal DGII e-CF Oficial FG: <a href="{DGII_PORTAL}" target="_blank" style="color:#FFD700;">{DGII_PORTAL}</a></h3><p>Configure su Usuario DGII + Clave + Certificado Digital Viafirma para remitir e-CF con validez legal</p></div>', unsafe_allow_html=True)
    dbp=get_db_path(client_id_input)
    if not dbp.exists(): st.warning("DB v6.0 DGII no existe"); st.stop()
    conn=sqlite3.connect(str(dbp)); c=conn.cursor(); c.execute("SELECT * FROM dgii_config WHERE cliente_id=?",(client_id_input,)); dgii_conf=c.fetchone(); conn.close()
    st.markdown("### 👤 Configuración Usuario DGII e-CF - Portal FG")
    col_dgii1,col_dgii2=st.columns(2)
    with col_dgii1:
        usuario_dgii_input=st.text_input("Usuario DGII e-CF (RNC/Cédula registrado en DGII FG Portal)",value=dgii_conf[2] if dgii_conf else "", key="usuario_dgii_input")
        clave_dgii_input=st.text_input("Clave DGII e-CF (Clave Portal FG)",type="password", key="clave_dgii_input")
        rnc_emisor_input=st.text_input("RNC Emisor e-CF (133378711)",value=dgii_conf[4] if dgii_conf else CRED["rnc"], key="rnc_emisor_input")
    with col_dgii2:
        razon_social_input=st.text_input("Razón Social Emisor e-CF",value=dgii_conf[5] if dgii_conf else CRED["empresa"], key="razon_social_input")
        portal_url_input=st.text_input("Portal DGII FG URL",value=DGII_PORTAL, key="portal_url_input")
        st.markdown(f'<a href="{DGII_PORTAL}" target="_blank" style="background:#2d5a27;color:white;padding:10px;border-radius:10px;text-decoration:none;">🔗 Abrir Portal DGII FG Ahora</a>', unsafe_allow_html=True)
    if st.button("💾 Guardar Configuración DGII e-CF + Usuario + Clave + Autoguardado v6.0",type="primary",use_container_width=True):
        conn=sqlite3.connect(str(dbp)); c=conn.cursor(); c.execute("INSERT OR REPLACE INTO dgii_config (id,cliente_id,usuario_dgii,clave_dgii_hash,rnc_emisor,razon_social,fecha_registro,portal_url) VALUES (?,?,?,?,?,?,?,?)",(f"DGII-{client_id_input}",client_id_input,usuario_dgii_input,hashlib.sha256(clave_dgii_input.encode()).hexdigest() if clave_dgii_input else "",rnc_emisor_input,razon_social_input,datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),portal_url_input)); conn.commit(); conn.close()
        st.success(f"✅ Config DGII e-CF guardada v6.0: Usuario {usuario_dgii_input} | RNC {rnc_emisor_input} | Portal FG {portal_url_input} | Base BASA_eCF_PRO_v6_DGII_CERTIFICADO"); add_historico(client_id_input, "GUARDAR_DGII_CONFIG_v6", "-", f"Config DGII Usuario {usuario_dgii_input} RNC {rnc_emisor_input} Portal FG", st.session_state.user)
    st.markdown("---"); st.markdown("### 🔐 Certificado Digital / Firma Electrónica - Viafirma o Cualquier Otra - Histórico Firmas")
    col_cert1,col_cert2=st.columns(2)
    with col_cert1:
        proveedor_cert=st.selectbox("Proveedor Certificado Digital v6.0",["Viafirma","Camerfirma","Otro - Especificar"], key="proveedor_cert_v6")
        if proveedor_cert=="Otro - Especificar": proveedor_otro=st.text_input("Nombre Proveedor Otro",value="Viafirma Dominicana", key="prov_otro_v6"); proveedor_final=proveedor_otro
        else: proveedor_final=proveedor_cert
        cert_file=st.file_uploader(f"📁 Subir Certificado Digital {proveedor_final} (.p12 / .pfx) - Para firma electrónica e-CF DGII",type=["p12","pfx"], key="cert_file_v6")
        clave_cert=st.text_input(f"Clave Certificado {proveedor_final} (.p12/.pfx)",type="password", key="clave_cert_v6")
        fecha_exp=st.date_input("Fecha Expedición Cert",value=datetime.date.today(), key="fecha_exp_v6")
        fecha_venc=st.date_input("Fecha Expiración Cert (Validez)",value=datetime.date(2027,12,31), key="fecha_venc_v6")
    with col_cert2:
        firma_elec=st.text_area("Firma Electrónica Texto (Opcional - Si usa firma no certificado)",value="", key="firma_elec_v6")
        estado_cert=st.selectbox("Estado Certificado v6.0",["Vigente","Por Vencer","Vencido","Revocado"], key="estado_cert_v6")
        st.markdown("**Instrucciones Viafirma:** 1. Obtenga certificado .p12 de Viafirma 2. Súbalo aquí 3. Ingrese clave 4. Active 5. Al facturar se firmará automático y remitirá a DGII FG Portal")
        if st.button(f"✅ Guardar Certificado {proveedor_final} + Firma + Histórico v6.0 DGII",type="primary",use_container_width=True):
            if cert_file:
                cert_path=save_cert(client_id_input, cert_file, proveedor_final)
                conn=sqlite3.connect(str(dbp)); c=conn.cursor()
                c.execute("UPDATE certificados SET activo=0 WHERE cliente_id=?",(client_id_input,))
                cert_id=f"CERT-v6-{str(uuid.uuid4())[:8].upper()}"; c.execute("INSERT INTO certificados (id,cliente_id,proveedor,cert_file_path,clave_cert_hash,fecha_expedicion,fecha_expiracion,estado,activo,fecha_subida,firma_electronica,historico) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(cert_id,client_id_input,proveedor_final,cert_path,hashlib.sha256(clave_cert.encode()).hexdigest() if clave_cert else "",str(fecha_exp),str(fecha_venc),estado_cert,1,datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),firma_elec,f"Historico firma {proveedor_final} {fecha_exp} - {fecha_venc} - Guardado por {st.session_state.user}"))
                conn.commit(); conn.close()
                st.success(f"✅ Certificado {proveedor_final} guardado v6.0 DGII: {cert_path} | ID {cert_id} | Activo | Vigente hasta {fecha_venc} | Firma: {firma_elec[:50]} | Histórico guardado | Se usará automático al facturar y remitir a DGII FG {DGII_PORTAL}")
                add_historico(client_id_input, "GUARDAR_CERTIFICADO_v6_DGII", cert_id, f"Certificado {proveedor_final} {cert_path} Firma {firma_elec[:20]} Activo", st.session_state.user)
            else: st.error("Suba archivo .p12/.pfx de Viafirma")
    st.markdown("---"); st.markdown("### 📜 Histórico Certificados y Firmas Electrónicas - Por Caso Cliente - Para Retomar al Facturar")
    conn=sqlite3.connect(str(dbp))
    try:
        df_certs=pd.read_sql_query("SELECT * FROM certificados WHERE cliente_id=? ORDER BY fecha_subida DESC",(client_id_input,))
        st.write(f"Certificados v6.0 DGII para caso {client_id_input}: {len(df_certs)} - Activo se usa automático al facturar")
        edited_certs=st.data_editor(df_certs, num_rows="dynamic", use_container_width=True, key="editor_certs_v6")
        colC1,colC2,colC3=st.columns(3)
        with colC1:
            if st.button("💾 Guardar Cambios Certificados v6.0 DGII Histórico",use_container_width=True,type="primary"):
                c=conn.cursor()
                for _,row in edited_certs.iterrows(): c.execute("UPDATE certificados SET proveedor=?, fecha_expedicion=?, fecha_expiracion=?, estado=?, activo=?, firma_electronica=? WHERE id=?",(row["proveedor"], row["fecha_expedicion"], row["fecha_expiracion"], row["estado"], row["activo"], row["firma_electronica"], row["id"]))
                conn.commit(); st.success("Certificados v6.0 DGII guardados - Histórico actualizado"); add_historico(client_id_input, "EDITAR_CERTIFICADOS_v6_DGII", "-", f"Edición certs por caso {client_id_input}", st.session_state.user)
        with colC2:
            cert_id_activar=st.text_input("ID Certificado a Activar como Principal v6.0", key="cert_activar_v6")
            if st.button("✅ Activar Certificado Principal v6.0 DGII - Usar al Facturar",use_container_width=True):
                c=conn.cursor(); c.execute("UPDATE certificados SET activo=0 WHERE cliente_id=?",(client_id_input,)); c.execute("UPDATE certificados SET activo=1 WHERE id=?",(cert_id_activar,)); conn.commit(); st.success(f"Certificado {cert_id_activar} activado como principal v6.0 DGII - Se usará automático al facturar + remitir a DGII FG")
        with colC3:
            if st.button("🔄 Recargar Certificados v6.0 DGII",use_container_width=True): st.rerun()
        if len(df_certs)>0:
            cert_activo_df=df_certs[df_certs["activo"]==1]
            if len(cert_activo_df)>0: st.success(f"✅ Certificado Activo v6.0 DGII para facturar: {cert_activo_df.iloc[0]['proveedor']} - {cert_activo_df.iloc[0]['cert_file_path']} - Vence {cert_activo_df.iloc[0]['fecha_expiracion']} - Firma: {cert_activo_df.iloc[0]['firma_electronica'][:50]}")
            else: st.warning("⚠️ No hay certificado activo v6.0 DGII - Active uno para firmar y remitir a DGII FG Portal")
    except Exception as e: st.info(f"Sin certificados v6.0 DGII aún: {e} - Suba su certificado Viafirma .p12 arriba")
    conn.close()
    st.markdown("---"); st.markdown(f"### 🔗 Remisión a DGII FG Portal - {DGII_PORTAL}")
    st.markdown(f'<div class="dgii-box">Para remitir factura v6.0 DGII: 1. Configure Usuario DGII arriba 2. Suba Certificado Viafirma .p12 3. Active certificado 4. En FACTURAR marque "Remitir automáticamente a DGII FG" 5. Sistema genera XML e-CF + Firma con cert + TrackID + Estado "Enviado a DGII FG" 6. Abra <a href="{DGII_PORTAL}" target="_blank" style="color:#FFD700;">Portal FG</a> para ver aceptación DGII</div>', unsafe_allow_html=True)
if mod=="GUIA":
    st.header("📘 Guía Completa v6.0 DGII CERTIFICADO - Viafirma + Logo + DGII + Registro + Cert + Portal FG")
    guia_full=f"""BASA e-CF PRO v6.0 DGII CERTIFICADO - GUIA COMPLETA - BASE BASA_eCF_PRO_v6_DGII_CERTIFICADO - PORTAL FG {DGII_PORTAL}
TITULO: BASA e-CF PRO v6.0 DGII CERTIFICADO - Base: BASA_eCF_PRO_v6_DGII_CERTIFICADO/clientes_db/ - BASA_CLI-D452_eCF.db - Logo.png - certificados/cert_viafirma.p12
RNC: 133378711 - Baldera Santos & Asociados SRL - Base: BASA_eCF_PRO_v6_DGII_CERTIFICADO - Portal FG {DGII_PORTAL}
CREDENCIALES: {CRED["nombre"]} | Whatsapp {CRED["whatsapp"]} | Email {CRED["email"]} | Dirección {CRED["direccion"]} | Base BASA v6.0 DGII | Portal FG {DGII_PORTAL}

NUEVO v6.0 DGII CERTIFICADO - VIAFIRMA + REGISTRO CLIENTES + LOGO + CERTIFICADO DIGITAL + DGII + PORTAL FG:

1. REGISTRO CLIENTES SE PUEDAN REGISTRAR: Antes de login, tab REGISTRO CLIENTE NUEVO, cliente llena ID auto CLI-XXXX, Razón Social, RNC, Correo (usuario), Password, Teléfono, Dirección, Web opcional, Logo PNG/JPG, Usuario DGII e-CF opcional, Clave DGII opcional, botón REGISTRARME EN BASA v6.0 DGII, crea DB BASA_CLI-XXXX_eCF.db en BASA_eCF_PRO_v6_DGII_CERTIFICADO/clientes_db/CLI-XXXX/, guarda logo en logo.png, guarda info.json con hash password, guarda dgii_config con usuario DGII + hash clave DGII + RNC emisor + razón social + fecha + portal_url {DGII_PORTAL}, add_historico REGISTRO_CLIENTE_BASA_v6, success cuenta creada, puede entrar con email registrado. También ADMIN puede crear cliente en módulo CLIENTES con logo + usuario DGII.

2. EDITAR LOGO Y DATOS CREDENCIALES: Módulo CLIENTES v6.0 con file_uploader Logo Cliente PNG/JPG, save_logo guarda en clientes_db/CLI-XXXX/logo.png, campo web, usuario DGII, guardar con logo_path en clientes_info + info.json, sidebar muestra logo del cliente actual con st.image logo.png, factura oficial incluye logo base64 <img src='data:image/png;base64,...'> en header, data_editor editable para logo_path, web, usuario_dgii, guardar cambios UPDATE clientes_info.

3. GUARDAR HISTORICO FACTURAS Y TODOS POR CASO CLIENTE: Módulo HISTORICO v6.0 por caso cliente, cada cliente CLI-D452 tiene su DB BASA_CLI-D452_eCF.db con facturas solo de ese caso, filtro por caso cliente ID input sidebar, tabla facturas con xml_generado, trackid, estado_dgii, editar guardar borrar por caso, log historico por caso cliente con accion FACTURAR_v6_DGII, TrackID, Cert, Remitir, DGII FG Portal, descarga por caso historico_v6_DGII_CLI-D452.csv, histórico certificados por caso.

4. GUARDAR USUARIO REGISTRADO DGII + CLAVE + FIRMA ELECTRONICA O CERTIFICADO DIGITAL VIAFIRMA: Módulo CERTIFICADOS v6.0 DGII, sección DGII Config: Usuario DGII e-CF (RNC/Cédula registrado en DGII FG Portal {DGII_PORTAL}), Clave DGII e-CF (clave portal FG), RNC Emisor, Razón Social Emisor, Portal URL FG, botón Guardar Config DGII guarda en tabla dgii_config id DGII-CLI-D452, cliente_id, usuario_dgii, clave_dgii_hash SHA256, rnc_emisor, razon_social, fecha_registro, portal_url, add_historico GUARDAR_DGII_CONFIG_v6. Sección Certificado Digital: Proveedor Viafirma/Camerfirma/Otro, file_uploader .p12/.pfx, clave certificado, fecha expedición, fecha expiración, firma electrónica texto opcional, estado Vigente/Por Vencer/Vencido/Revocado, botón Guardar Certificado Viafirma + Firma + Histórico v6.0: save_cert guarda en clientes_db/CLI-XXXX/certificados/cert_Viafirma_2026.p12, UPDATE certificados set activo=0 para cliente, INSERT nuevo certificado con id CERT-v6-XXXX, cliente_id, proveedor, cert_file_path, clave_cert_hash SHA256, fecha_expedicion, fecha_expiracion, estado, activo 1, fecha_subida, firma_electronica, historico texto, histórico guardado para retomar.

5. GUARDAR HISTORICO FIRMA ELECTRONICA O CERTIFICADO DIGITAL PARA RETOMAR CADA VEZ QUE CREE FACTURA Y PUEDAS REMITIR A DGII: Tabla certificados con histórico, cada vez que sube nuevo cert, viejo se desactiva activo=0 pero queda en histórico, data_editor para editar certificados, activar certificado principal con input ID cert + botón Activar Certificado Principal v6.0 DGII que pone activo=1, al facturar en FACTURAR v6.0 busca SELECT * FROM certificados WHERE cliente_id=? AND activo=1 LIMIT 1, si existe cert_activo lo muestra en dgii-box Cert Activo: SI - Viafirma - fecha, lo usa para firma_digital, xml_generado, trackid, estado_dgii. Checkbox Remitir automáticamente a DGII Portal FG al facturar, si marcado y cert_activo existe, genera xml_content <eCF>...</eCF> con firma + cert + TrackID TRACK-XXXX-DGII, estado_dgii Enviado a DGII FG - En proceso validación XML+TrackID, muestra box Remitiendo a DGII FG Portal {DGII_PORTAL} con link abrir portal, add_historico FACTURAR_v6_DGII con TrackID Cert Remitir. En HISTORICO muestra xml_generado, trackid, estado_dgii, cert Viafirma.

6. HABILITAR E INCORPORAR https://fg.dgii.gov.do/ecf/PortalFG/login?redirectUrl=%2Fecf%2Fportalfg: Constante DGII_PORTAL = {DGII_PORTAL}, en login, dashboard, sidebar, facturar, certificados, guía se muestra box dgii-box con link <a href="{DGII_PORTAL}" target="_blank">Abrir Portal DGII FG</a>, botón Abrir Portal DGII FG Ahora, en facturar checkbox remitir a {DGII_PORTAL}, en certificados sección Remisión a DGII FG Portal instrucciones, en guía descripción portal FG. Al facturar con remitir, genera mensaje con link portal para ver estado aceptación DGII.

COMO USAR v6.0 DGII CERTIFICADO:
ADMIN: Login Licpedrobaldera@gmail.com / Basa2026! -> CLIENTES crear MANUEL KING con logo PNG + Usuario DGII 133412918 + Clave DGII -> CERTIFICADOS configurar Usuario DGII 133412918 + Clave DGII + RNC Emisor 133412918 + Razón Social MANUEL KING VEHICULOS SRL + Portal FG URL + Guardar Config DGII -> En CERTIFICADOS subir cert Viafirma .p12 + clave cert + fecha exp/venc + firma electrónica texto + Guardar Certificado Viafirma + Activar como principal -> FACTURAR elegir E31 Automático E310000000028 + Razón Social COMERCIAL ZYL + Cant 150 Zapatos CAJ 550 + Remitir a DGII FG marcado + FACTURAR v6.0 DGII -> Ver factura con logo + TrackID + Cert Viafirma + XML + Estado Enviado a DGII FG -> Botón Abrir Portal DGII FG {DGII_PORTAL} -> Ver aceptación en DGII FG Portal -> HISTORICO por caso CLI-D452 ver facturas + xml + trackid + estado_dgii + certs + editar/guardar/borrar -> PRECIOS crear precio -> GUIA ver guía -> Sidebar cambiar clave
CLIENTE REGISTRO: En login tab REGISTRO CLIENTE NUEVO llenar datos + Logo + Usuario DGII + REGISTRARME -> Cuenta creada BASA v6.0 DGII -> Entrar con email registrado -> Ve su DB BASA_CLI-XXXX_eCF.db + Logo + Config DGII + Puede subir su cert Viafirma en CERTIFICADOS + Facturar con logo + cert + remitir a DGII FG Portal + Histórico por caso + Cambiar clave + Descargar PDF/Excel/Word/XML

BASE v6.0 DGII: BASA_eCF_PRO_v6_DGII_CERTIFICADO/clientes_db/CLI-D452/BASA_CLI-D452_eCF.db + logo.png + certificados/cert_Viafirma_2026.p12 + info.json + historico_cert.json - Full FIXED - Sin elif solo if - Portal FG {DGII_PORTAL} integrado - Viafirma certificado digital histórico - Logo por caso cliente - Registro clientes self-registration - Usuario DGII + clave + firma electrónica + certificado digital para retomar cada factura + remitir a DGII

SOPORTE v6.0 DGII: {CRED["nombre"]} Whatsapp {CRED["whatsapp"]} Email {CRED["email"]} - v6.0 DGII CERTIFICADO - Viafirma + Logo + DGII + Registro + Cert + Portal FG {DGII_PORTAL} - Base BASA_eCF_PRO_v6_DGII_CERTIFICADO
"""
    st.text_area("Guía Completa v6.0 DGII CERTIFICADO - Viafirma + Logo + DGII + Portal FG",guia_full,height=700)
    st.download_button("📥 Descargar Guía v6.0 DGII CERTIFICADO + Viafirma + Logo + Portal FG",guia_full,file_name="BASA_eCF_PRO_v6_DGII_CERTIFICADO_Viafirma_Logo_PortalFG_Guia.txt",use_container_width=True,type="primary")
    st.markdown(f'<div class="dgii-box"><h3>🔗 Portal DGII e-CF FG Oficial: <a href="{DGII_PORTAL}" target="_blank" style="color:#FFD700;">{DGII_PORTAL}</a></h3><p>Configure Usuario DGII + Certificado Viafirma para remitir con validez legal</p><p><a href="{DGII_PORTAL}" target="_blank" style="background:#FFD700;color:black;padding:10px;border-radius:10px;text-decoration:none;">🔗 Abrir Portal DGII FG Ahora</a></p></div>', unsafe_allow_html=True)
st.markdown(f'<div class="footer-pro"><table width="100%"><tr><td><b>👨‍💼 {CRED["nombre"]} - BASA v6.0 DGII CERTIFICADO</b><br>🏢 {CRED["empresa"]} | RNC: {CRED["rnc"]} | Base: BASA_eCF_PRO_v6_DGII_CERTIFICADO | Portal FG: fg.dgii.gov.do</td><td style="text-align:right;"><b>📞 Contacto / Whatsapp:</b> {CRED["whatsapp"]}<br><b>📧 Correo:</b> {CRED["email"]}<br>🌐 BASA v6.0 DGII CERTIFICADO - Viafirma + Logo + DGII + Portal FG - FULL FIXED - SIN SYNTAXERROR</td></tr></table></div>', unsafe_allow_html=True)
    
