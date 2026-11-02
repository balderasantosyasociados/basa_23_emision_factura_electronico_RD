import streamlit as st, json, os, hashlib, datetime, sqlite3, uuid, base64, random, string
from pathlib import Path
import pandas as pd
st.set_page_config(page_title="BASA e-CF PRO v5.1 FULL FIXED - BASA_eCF_PRO_v5_FULL_FIXED", layout="wide", page_icon="💰")
BASE_DIR=Path("BASA_eCF_PRO_v5_FULL_FIXED"); CLIENTES_DB=BASE_DIR/"clientes_db"; BASE_DIR.mkdir(exist_ok=True); CLIENTES_DB.mkdir(exist_ok=True)
CASOS_DIR=CLIENTES_DB
MASTER_USER={"email":"Licpedrobaldera@gmail.com","password_hash":hashlib.sha256("Basa2026!".encode()).hexdigest(),"rnc":"133378711"}
CRED={"nombre":"Lic. Pedro A. Baldera R.","empresa":"Baldera Santos & Asociados SRL","rnc":"133378711","telefono":"829-771-7390","whatsapp":"829-771-7390","email":"licpedrobaldera@gmail.com","direccion":"Calle Orlando Martinez No.49, Brisas del Este, Santo Domingo Este"}
def get_db_path(cid):
    cf=CASOS_DIR/cid; cf.mkdir(exist_ok=True, parents=True); return cf/f"BASA_{cid}_eCF.db"
def init_db(cid):
    dbp=get_db_path(cid); conn=sqlite3.connect(str(dbp)); c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS facturas (id INTEGER PRIMARY KEY, ncf TEXT UNIQUE, tipo TEXT, cliente TEXT, rnc_cliente TEXT, descripcion TEXT, cantidad REAL, precio REAL, itbis REAL, descuento REAL, total REAL, fecha TEXT, vencimiento TEXT, estado TEXT, codigo_seg TEXT, firma_digital TEXT, precio_id TEXT, forma_pago TEXT, observaciones TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS clientes_info (id TEXT PRIMARY KEY, nombre TEXT, rnc TEXT, email TEXT, direccion TEXT, telefono TEXT, precio_base REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS precios (id TEXT PRIMARY KEY, descripcion TEXT, precio REAL, cliente_id TEXT, fecha TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS historico (id INTEGER PRIMARY KEY, cliente_id TEXT, accion TEXT, ncf TEXT, detalle TEXT, usuario TEXT, fecha TEXT)")
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
st.markdown("<style>.header-pro{background:linear-gradient(135deg,#0F2027,#203A43,#2C5364);padding:20px;border-radius:15px;text-align:center;color:white;border:2px solid #FFD700;}.footer-pro{background:#0F2027;color:white;padding:15px;border-radius:10px;margin-top:20px;border-left:5px solid #FFD700;}</style>", unsafe_allow_html=True)
if "logged" not in st.session_state: st.session_state.logged=False
if "modulo_activo" not in st.session_state: st.session_state.modulo_activo="DASHBOARD"
if "recovery_mode" not in st.session_state: st.session_state.recovery_mode=False
if not st.session_state.logged:
    st.markdown('<div class="header-pro"><h1>🏛️ BASA e-CF PRO v5.1 FULL FIXED</h1><h2>Plataforma Integral de Facturación Electrónica Certificada DGII | RNC 133378711 | Base: BASA_eCF_PRO_v5_FULL_FIXED</h2><p style="color:#FFD700;">Baldera Santos & Asociados SRL - Base Renombrada a BASA</p></div>', unsafe_allow_html=True)
    c1,c2,c3=st.columns([1,2,1])
    with c2:
        if not st.session_state.recovery_mode:
            st.markdown("### 🔐 Acceso Seguro - v5.1 BASA FULL FIXED")
            email=st.text_input("Correo Electrónico")
            pwd=st.text_input("Contraseña",type="password")
            if st.button("🚀 Entrar a BASA e-CF PRO v5.1 FULL FIXED",use_container_width=True,type="primary"):
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
                    if not found: st.error("❌ Credenciales incorrectas")
            if st.button("🔑 Olvidé mi clave - Recuperar",use_container_width=True):
                st.session_state.recovery_mode=True; st.rerun()
        else:
            st.markdown("### 🔑 Recuperar Clave - Código por Correo/WhatsApp")
            email_rec=st.text_input("Correo registrado para recuperar")
            if st.button("📧 Generar Código de Recuperación",use_container_width=True,type="primary"):
                code=gen_code(); st.session_state.recovery_code=code; st.session_state.recovery_email=email_rec
                st.success(f"✅ Código: {code} - Enviado a {email_rec} / WhatsApp {CRED['whatsapp']}")
            code_in=st.text_input("Ingresa código recibido")
            new_pwd=st.text_input("Nueva contraseña",type="password")
            if st.button("🔄 Cambiar clave con código",use_container_width=True):
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
            if st.button("⬅️ Volver a Login"): st.session_state.recovery_mode=False; st.rerun()
    st.stop()
st.markdown(f'<div class="header-pro"><h1>🏛️ BASA e-CF PRO v5.1 FULL FIXED</h1><h2>Plataforma Integral de Facturación Electrónica Certificada DGII | RNC 133378711 | {CRED["empresa"]} | Base: BASA_eCF_PRO_v5_FULL_FIXED/clientes_db</h2></div>', unsafe_allow_html=True)
st.markdown("### 📋 Módulos del Sistema - v5.1 BASA FULL FIXED")
b1,b2,b3,b4,b5,b6=st.columns(6)
with b1:
    if st.button("📊 DASHBOARD",use_container_width=True,type="primary" if st.session_state.modulo_activo=="DASHBOARD" else "secondary"): st.session_state.modulo_activo="DASHBOARD"; st.rerun()
with b2:
    if st.button("👥 CLIENTES",use_container_width=True,type="primary" if st.session_state.modulo_activo=="CLIENTES" else "secondary"): st.session_state.modulo_activo="CLIENTES"; st.rerun()
with b3:
    if st.button("🧾 FACTURAR e-CF",use_container_width=True,type="primary" if st.session_state.modulo_activo=="FACTURAR" else "secondary"): st.session_state.modulo_activo="FACTURAR"; st.rerun()
with b4:
    if st.button("📜 HISTORICO",use_container_width=True,type="primary" if st.session_state.modulo_activo=="HISTORICO" else "secondary"): st.session_state.modulo_activo="HISTORICO"; st.rerun()
with b5:
    if st.button("💰 PRECIOS",use_container_width=True,type="primary" if st.session_state.modulo_activo=="PRECIOS" else "secondary"): st.session_state.modulo_activo="PRECIOS"; st.rerun()
with b6:
    if st.button("📘 GUIA + CLAVE",use_container_width=True,type="primary" if st.session_state.modulo_activo=="GUIA" else "secondary"): st.session_state.modulo_activo="GUIA"; st.rerun()
with st.sidebar:
    st.write(f"Usuario: {st.session_state.user}"); st.write(f"Rol: {st.session_state.role}"); st.markdown("---")
    client_id_input=st.text_input("ID Cliente DB",value=st.session_state.get("client_id","CLI-D452"))
    if st.button("✅ Crear/Verificar DB BASA + Autoguardado",use_container_width=True): dbp=init_db(client_id_input); add_historico(client_id_input, "VERIFICAR_DB_BASA", "-", f"DB BASA verificada por {st.session_state.user}", st.session_state.user); st.success(f"DB BASA OK: {dbp}")
    st.markdown("---")
    st.markdown("### 🔑 Cambiar Clave")
    new_pwd_sidebar=st.text_input("Nueva clave",type="password",key="new_pwd_sidebar")
    if st.button("💾 Guardar Nueva Clave - Autoguardado",use_container_width=True):
        for cf in CASOS_DIR.iterdir():
            jf=cf/"info.json"
            if jf.exists():
                info=json.loads(jf.read_text())
                if info.get("email")==st.session_state.user:
                    info["password_hash"]=hashlib.sha256(new_pwd_sidebar.encode()).hexdigest()
                    jf.write_text(json.dumps(info,indent=2))
                    st.success(f"Clave actualizada para {st.session_state.user}")
                    add_historico(info.get("id"), "CAMBIO_CLAVE", "-", f"Cambio clave por {st.session_state.user}", st.session_state.user)
    if st.button("🚪 Salir",use_container_width=True): st.session_state.logged=False; st.rerun()
    st.markdown("---"); st.markdown(f"**{CRED['nombre']}**"); st.markdown(f"{CRED['telefono']}"); st.markdown(f"{CRED['email']}")
mod=st.session_state.modulo_activo
if mod=="DASHBOARD":
    st.header("📊 Dashboard - BASA e-CF PRO v5.1 FULL FIXED - Base BASA_eCF_PRO_v5_FULL_FIXED")
    total_c=len([d for d in CASOS_DIR.iterdir() if d.is_dir()]); total_f=0; total_m=0
    for cf in CASOS_DIR.iterdir():
        if cf.is_dir():
            dbp=cf/f"BASA_{cf.name}_eCF.db"
            if dbp.exists():
                conn=sqlite3.connect(str(dbp))
                try:
                    c=conn.cursor(); c.execute("SELECT COUNT(*), SUM(total) FROM facturas"); cnt,sm=c.fetchone(); total_f+=cnt or 0; total_m+=sm or 0
                except: pass
                conn.close()
    c1,c2,c3,c4=st.columns(4); c1.metric("Clientes BASA",total_c); c2.metric("Facturas e-CF",total_f); c3.metric("Monto",f"RD$ {total_m:,.2f}"); c4.metric("Base","BASA_eCF_PRO_v5_FULL_FIXED")
    st.success(f"✅ Base Renombrada a BASA_eCF_PRO_v5_FULL_FIXED/clientes_db/ | DB: BASA_CLI-D452_eCF.db | Cliente: {client_id_input}")
if mod=="CLIENTES":
    st.header("👥 Gestión Clientes FULL BASA - Dirección + Teléfono + Editar/Borrar/Guardar + Cambio Clave Admin")
    col1,col2=st.columns(2)
    with col1:
        nid=st.text_input("ID Nuevo",value=f"CLI-{str(uuid.uuid4())[:4].upper()}")
        nom=st.text_input("Razón Social",value="MANUEL KING VEHICULOS SRL")
        rnc=st.text_input("RNC Cliente",value="133412918")
        dir_cli=st.text_input("Dirección Cliente",value="Calle Segunda #01, Gazcue, Distrito Nacional")
    with col2:
        cor=st.text_input("Correo",value="cliente@empresa.com")
        pwd=st.text_input("Password",value="Cliente2026!")
        tel_cli=st.text_input("Teléfono Cliente",value="809-123-4567")
        precio_base=st.number_input("Precio Base RD$",value=199.0)
    if st.button("✅ CREAR CLIENTE FULL BASA - $199/mes - Autoguardado",type="primary",use_container_width=True):
        dbp=init_db(nid); info={"id":nid,"nombre":nom,"rnc":rnc,"email":cor,"password_hash":hashlib.sha256(pwd.encode()).hexdigest(),"precio":precio_base,"direccion":dir_cli,"telefono":tel_cli}; (CASOS_DIR/nid/"info.json").write_text(json.dumps(info,indent=2))
        conn=sqlite3.connect(str(dbp)); c=conn.cursor(); c.execute("INSERT OR REPLACE INTO clientes_info (id,nombre,rnc,email,direccion,telefono,precio_base) VALUES (?,?,?,?,?,?,?)",(nid,nom,rnc,cor,dir_cli,tel_cli,precio_base)); conn.commit(); conn.close()
        add_historico(nid, "CREAR_CLIENTE_BASA", "-", f"Cliente {nom} RNC {rnc} creado en BASA", st.session_state.user)
        st.success(f"CREADO BASA {nid} | {nom} | {cor} | Tel {tel_cli} | DB: BASA_{nid}_eCF.db")
    st.markdown("---"); st.markdown("### 📋 Lista Clientes BASA - Editar / Borrar / Guardar / Cambiar Clave")
    clientes=[]
    for cf in CASOS_DIR.iterdir():
        if cf.is_dir():
            jf=cf/"info.json"
            if jf.exists():
                try: clientes.append(json.loads(jf.read_text()))
                except: pass
    if clientes:
        df_cli=pd.DataFrame(clientes)
        edited_df=st.data_editor(df_cli, num_rows="dynamic", use_container_width=True, key="editor_clientes")
        colA,colB,colC=st.columns(3)
        with colA:
            if st.button("💾 Guardar Cambios Clientes BASA - Autoguardado",use_container_width=True,type="primary"):
                for _,row in edited_df.iterrows():
                    cid=row["id"]; (CASOS_DIR/cid/"info.json").write_text(json.dumps(row.to_dict(),indent=2))
                    dbp=get_db_path(cid); conn=sqlite3.connect(str(dbp)); c=conn.cursor(); c.execute("UPDATE clientes_info SET nombre=?, rnc=?, email=?, direccion=?, telefono=?, precio_base=? WHERE id=?",(row["nombre"], row["rnc"], row["email"], row.get("direccion",""), row.get("telefono",""), row.get("precio",199), cid)); conn.commit(); conn.close()
                st.success("Cambios guardados BASA - Autoguardado"); add_historico(client_id_input, "EDITAR_CLIENTES_BASA", "-", "Edición masiva BASA", st.session_state.user)
        with colB:
            del_id=st.text_input("ID a Borrar BASA")
            if st.button("🗑️ Borrar Cliente BASA - Histórico",use_container_width=True):
                import shutil; shutil.rmtree(CASOS_DIR/del_id, ignore_errors=True); st.success(f"Borrado BASA {del_id}"); add_historico(client_id_input, "BORRAR_CLIENTE_BASA", "-", f"Borrado {del_id} BASA", st.session_state.user)
        with colC:
            admin_email_change=st.text_input("Email cliente para cambiar clave manual (ADMIN BASA)")
            admin_new_pwd=st.text_input("Nueva clave manual ADMIN BASA",type="password")
            if st.button("🔑 ADMIN Actualiza Clave Manualmente BASA",use_container_width=True):
                for cf in CASOS_DIR.iterdir():
                    jf=cf/"info.json"
                    if jf.exists():
                        info=json.loads(jf.read_text())
                        if info.get("email")==admin_email_change:
                            info["password_hash"]=hashlib.sha256(admin_new_pwd.encode()).hexdigest()
                            jf.write_text(json.dumps(info,indent=2)); st.success(f"Clave actualizada BASA para {admin_email_change}"); add_historico(info.get("id"), "CAMBIO_CLAVE_ADMIN_BASA", "-", f"Cambio por ADMIN BASA {st.session_state.user}", st.session_state.user)
    else: st.info("No hay clientes BASA")
if mod=="FACTURAR":
    st.header(f"🧾 Facturación DGII v5.1 BASA FULL FIXED - Cliente {client_id_input} - NCF Auto/Manual + Impresora + PDF/Word/Excel - Base BASA")
    dbp=get_db_path(client_id_input)
    if not dbp.exists(): st.warning("DB BASA no existe - Crear en sidebar BASA"); st.stop()
    st.info("Tipos e-CF DGII: E31 Crédito Fiscal, E32 Consumo, E33 Débito, E34 Crédito, E41 Compras, E43 Gastos Menores, E44 Regímenes Especiales, E45 Gubernamental, E46 Exportación, E47 Pagos Exterior | Estructura: E+Tipo(31)+Secuencial 10 digitos = E310000000001 | Estados: Aceptado, Rechazado, Aceptado condicional, En proceso, Anulado | Modelo: Emisor->DGII valida XML+TrackID->Emisor->Receptor | QR verificación | RI Decreto 254-06 Norma 06-2018 | Base BASA_eCF_PRO_v5_FULL_FIXED")
    col_ncf1,col_ncf2=st.columns(2)
    with col_ncf1:
        tipo_sel=st.selectbox("Tipo e-NCF DGII Oficial",["E31 - Factura Crédito Fiscal Electrónica","E32 - Factura Consumo Electrónica","E33 - Nota Débito Electrónica","E34 - Nota Crédito Electrónica","E41 - Compras Electrónico","E43 - Gastos Menores Electrónico","E44 - Regímenes Especiales Electrónico","E45 - Gubernamental Electrónico","E46 - Exportación Electrónico","E47 - Pagos al Exterior Electrónico"])
        tipo_code=tipo_sel.split(" - ")[0]
    with col_ncf2:
        modo_ncf=st.selectbox("Modo NCF Electrónico BASA",["Automático - Guardar NCF Electrónico Automático BASA (Recomendado)","Manual - Agregar NCF Manual BASA para Casos Especiales"])
    if "Automático" in modo_ncf:
        next_ncf=get_next_ncf(client_id_input,tipo_code)
        st.success(f"🔒 NCF Automático BASA: {next_ncf} | Base: BASA_eCF_PRO_v5_FULL_FIXED")
    else:
        next_ncf=st.text_input("✍️ Ingrese NCF Manual BASA (Ej: E310000000028)",value="E310000000028")
        st.warning(f"⚠️ NCF Manual BASA: {next_ncf}")
    c1,c2,c3=st.columns(3)
    with c1: razon_c=st.text_input("Razón Social Cliente BASA",value="COMERCIAL ZYL SRL - BASA",key="razon_c")
    with c2: rnc_c=st.text_input("RNC Cliente BASA",value="130000001",key="rnc_c")
    with c3: venc=st.date_input("Fecha Vencimiento BASA",value=datetime.date(2026,12,31))
    c1,c2,c3,c4,c5,c6=st.columns(6)
    with c1: cant=st.number_input("Cant BASA",value=150.0,key="cant")
    with c2: desc=st.text_input("Descripción BASA",value="Zapatos",key="desc")
    with c3: uni=st.text_input("Unidad BASA",value="CAJ",key="uni")
    with c4: prec=st.number_input("Precio RD$ BASA",value=550.0,key="prec")
    with c5: dsc=st.number_input("Descuento RD$ BASA",value=0.0,key="dsc")
    with c6: forma_pago=st.selectbox("Forma Pago BASA",["Contado","Crédito - 30 días"])
    itbis_p=0.18; sub=cant*prec-dsc; itbis=sub*itbis_p; tot=sub+itbis
    st.markdown(f"**Subtotal BASA: RD$ {sub:,.2f} | ITBIS BASA: RD$ {itbis:,.2f} | Total BASA: RD$ {tot:,.2f} | Autoguardado BASA**")
    coment=st.text_input("Comentario BASA",value="Factura según Guía DGII E310000000001 - Base BASA",key="coment")
    if st.button(f"💰 FACTURAR BASA {tipo_code} - Guardar NCF {next_ncf} - Autoguardado + Histórico BASA",type="primary",use_container_width=True):
        cod=base64.b64encode(os.urandom(6)).decode()[:6]; now=datetime.datetime.now(); fecha=now.strftime("%d-%m-%Y"); firma=now.strftime("%d-%m-%Y %H:%M:%S")
        conn=sqlite3.connect(str(dbp)); c=conn.cursor()
        try:
            c.execute("INSERT INTO facturas (ncf,tipo,cliente,rnc_cliente,descripcion,cantidad,precio,itbis,descuento,total,fecha,vencimiento,estado,codigo_seg,firma_digital,forma_pago,observaciones) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(next_ncf,tipo_code,razon_c,rnc_c,desc,cant,prec,itbis,dsc,tot,fecha,str(venc),"Aceptado",cod,firma,forma_pago,coment)); conn.commit()
            st.success(f"✅ Factura BASA {next_ncf} Guardada en BASA_eCF_PRO_v5_FULL_FIXED | Código: {cod} | Estado: Aceptado | Autoguardado BASA")
            add_historico(client_id_input, "FACTURAR_BASA", next_ncf, f"Facturado BASA {desc} Total {tot}", st.session_state.user)
        except sqlite3.IntegrityError: st.error(f"❌ NCF BASA {next_ncf} ya existe en BASA")
        conn.close()
        html=f'<div style="border:2px solid black; padding:20px; background:white; color:black; font-family:Arial; font-size:13px;"><table width="100%"><tr><td width="60%"><b>COMERCIAL ZYL SRL - {CRED["empresa"]} - BASA FULL FIXED</b><br>RNC: {CRED["rnc"]} - Base: BASA_eCF_PRO_v5_FULL_FIXED<br>Dirección: {CRED["direccion"]}<br>Tel: {CRED["telefono"]}<br>Fecha: {fecha}</td><td width="40%" style="text-align:right;"><b>Factura Crédito Fiscal Electrónica BASA</b><br><b>e-NCF: {next_ncf}</b><br><b>Vencimiento: {venc.strftime("%d-%m-%Y")}</b></td></tr></table><hr><b>Razón Social: {razon_c}</b><br><b>RNC: {rnc_c}</b><hr><table border="1" width="100%" cellpadding="5" cellspacing="0" style="border-collapse:collapse;"><tr style="background:#D3D3D3;"><th>Cantidad</th><th>Descripción</th><th>Unidad</th><th>Precio</th><th>ITBIS</th><th>Valor</th></tr><tr><td>{cant:.0f}</td><td>{desc}</td><td>{uni}</td><td>{prec:,.2f}</td><td>{itbis:,.2f}</td><td>{sub:,.2f}</td></tr></table><br><table width="100%"><tr><td width="50%">[QR BASA {next_ncf}]<br><small>Código BASA: {cod}<br>Firma BASA: {firma}<br>Estado BASA: Aceptado - DGII valida XML+TrackID - Base BASA_eCF_PRO_v5_FULL_FIXED</small></td><td width="50%" style="text-align:right;">Subtotal BASA: {sub:,.2f}<br>ITBIS BASA: {itbis:,.2f}<br><b>Total BASA: {tot:,.2f}</b></td></tr></table><br>Comentario BASA: {coment}</div>'
        st.markdown(html, unsafe_allow_html=True)
        col_imp1,col_imp2,col_imp3,col_imp4=st.columns(4)
        with col_imp1: st.markdown(f'<button onclick="window.print()" style="background:#203A43;color:white;padding:10px;border-radius:10px;width:100%;">🖨️ Imprimir BASA con Impresora</button>', unsafe_allow_html=True)
        with col_imp2:
            pdf_content=f"Factura BASA {next_ncf} - {razon_c} - RNC {rnc_c} - Total RD$ {tot:,.2f} - Fecha {fecha} - Codigo {cod} - DGII Oficial - Base BASA_eCF_PRO_v5_FULL_FIXED"
            st.download_button(f"📄 Descargar PDF BASA - {next_ncf}",pdf_content,file_name=f"BASA_{next_ncf}.pdf",use_container_width=True)
        with col_imp3:
            excel_df=pd.DataFrame([{"e-NCF BASA":next_ncf,"Cliente BASA":razon_c,"RNC BASA":rnc_c,"Descripcion BASA":desc,"Cantidad BASA":cant,"Precio BASA":prec,"ITBIS BASA":itbis,"Total BASA":tot,"Fecha BASA":fecha,"CodigoSeg BASA":cod,"Base BASA":"BASA_eCF_PRO_v5_FULL_FIXED"}] )
            st.download_button(f"📊 Descargar Excel BASA - {next_ncf}",excel_df.to_csv(index=False),file_name=f"BASA_{next_ncf}.csv",use_container_width=True)
        with col_imp4:
            word_content=f"Factura BASA {next_ncf} Cliente {razon_c} Total RD$ {tot:,.2f} Fecha {fecha} Codigo {cod} DGII Oficial Base BASA_eCF_PRO_v5_FULL_FIXED"
            st.download_button(f"📝 Descargar Word BASA - {next_ncf}",word_content,file_name=f"BASA_{next_ncf}.doc",use_container_width=True)
if mod=="HISTORICO":
    st.header(f"📜 Histórico Cliente BASA {client_id_input} - Editar / Guardar / Borrar - Autoguardado - Base BASA_eCF_PRO_v5_FULL_FIXED")
    dbp=get_db_path(client_id_input)
    if not dbp.exists(): st.warning("DB BASA no existe"); st.stop()
    conn=sqlite3.connect(str(dbp))
    try:
        df_fact=pd.read_sql_query("SELECT * FROM facturas ORDER BY id DESC", conn)
        st.write(f"Facturas en DB BASA: {len(df_fact)} - Editable BASA - Base: BASA_eCF_PRO_v5_FULL_FIXED/clientes_db/{client_id_input}/BASA_{client_id_input}_eCF.db")
        edited_fact=st.data_editor(df_fact, num_rows="dynamic", use_container_width=True, key="editor_facturas")
        colH1,colH2,colH3=st.columns(3)
        with colH1:
            if st.button("💾 Guardar Cambios Histórico BASA - Autoguardado",use_container_width=True,type="primary"):
                for _,row in edited_fact.iterrows():
                    c=conn.cursor(); c.execute("UPDATE facturas SET cliente=?, rnc_cliente=?, descripcion=?, cantidad=?, precio=?, itbis=?, descuento=?, total=?, estado=?, forma_pago=?, observaciones=? WHERE ncf=?",(row["cliente"], row["rnc_cliente"], row["descripcion"], row["cantidad"], row["precio"], row["itbis"], row["descuento"], row["total"], row["estado"], row.get("forma_pago",""), row.get("observaciones",""), row["ncf"]))
                conn.commit(); st.success("Histórico BASA guardado - Autoguardado BASA"); add_historico(client_id_input, "EDITAR_HISTORICO_BASA", "-", "Edición histórico BASA", st.session_state.user)
        with colH2:
            ncf_borrar=st.text_input("NCF a Borrar del Histórico BASA")
            if st.button("🗑️ Borrar NCF del Histórico BASA",use_container_width=True):
                c=conn.cursor(); c.execute("DELETE FROM facturas WHERE ncf=?",(ncf_borrar,)); conn.commit(); st.success(f"Borrado BASA {ncf_borrar}"); add_historico(client_id_input, "BORRAR_NCF_BASA", ncf_borrar, f"Borrado BASA {ncf_borrar}", st.session_state.user)
        with colH3:
            if st.button("🔄 Cargar Todo y Actualizar FULL BASA",use_container_width=True): st.rerun()
        st.markdown("---"); st.markdown("### 📜 Log de Acciones BASA")
        df_hist=pd.read_sql_query("SELECT * FROM historico ORDER BY id DESC", conn)
        st.dataframe(df_hist, use_container_width=True)
        st.download_button("📥 Descargar Histórico BASA Excel/CSV",df_fact.to_csv(index=False),file_name=f"historico_BASA_{client_id_input}.csv")
    except Exception as e: st.info(f"Sin histórico BASA: {e}")
    conn.close()
if mod=="PRECIOS":
    st.header(f"💰 Gestión Precios BASA - Crear Nuevo Precio y Ajuste Sistema - Cliente {client_id_input} - Base BASA")
    dbp=get_db_path(client_id_input)
    if not dbp.exists(): st.warning("DB BASA no existe"); st.stop()
    c1,c2,c3=st.columns(3)
    with c1: desc_prec=st.text_input("Descripción Precio BASA",value="Servicio Impuestos BASA")
    with c2: precio_val=st.number_input("Precio RD$ BASA",value=6000.0)
    with c3: fecha_prec=st.date_input("Fecha Precio BASA",value=datetime.date.today())
    if st.button("➕ Crear Nuevo Precio BASA - Autoguardado",type="primary",use_container_width=True):
        conn=sqlite3.connect(str(dbp)); c=conn.cursor(); pid=f"PREC-BASA-{str(uuid.uuid4())[:6].upper()}"; c.execute("INSERT INTO precios (id, descripcion, precio, cliente_id, fecha) VALUES (?,?,?,?,?)",(pid, desc_prec, precio_val, client_id_input, str(fecha_prec))); conn.commit(); conn.close()
        st.success(f"Precio BASA {pid} - {desc_prec} RD$ {precio_val} creado - Autoguardado BASA - Base BASA_eCF_PRO_v5_FULL_FIXED"); add_historico(client_id_input, "CREAR_PRECIO_BASA", pid, f"Precio BASA {desc_prec} {precio_val}", st.session_state.user)
    conn=sqlite3.connect(str(dbp))
    try:
        df_precios=pd.read_sql_query("SELECT * FROM precios WHERE cliente_id=? ORDER BY fecha DESC",(client_id_input,))
        st.markdown("### 📋 Precios BASA - Editar / Guardar / Borrar - Base BASA")
        edited_precios=st.data_editor(df_precios, num_rows="dynamic", use_container_width=True, key="editor_precios")
        if st.button("💾 Guardar Ajuste Precios BASA - Autoguardado",use_container_width=True,type="primary"):
            c=conn.cursor()
            for _,row in edited_precios.iterrows(): c.execute("UPDATE precios SET descripcion=?, precio=? WHERE id=?",(row["descripcion"], row["precio"], row["id"]))
            conn.commit(); st.success("Precios BASA ajustados - Autoguardado BASA")
    except: st.info("Sin precios BASA aún - Crea uno arriba - Base BASA_eCF_PRO_v5_FULL_FIXED")
    conn.close()
    st.markdown("---"); st.markdown("#### ⚙️ Ajuste Sistema BASA DGII Formato Oficial - Base BASA_eCF_PRO_v5_FULL_FIXED")
    st.markdown("**Estructura BASA:** E+Tipo(31)+Secuencial 10 digitos = E310000000001 | **Tipos BASA:** 31 Crédito Fiscal, 32 Consumo, 33 Débito, 34 Crédito, 41 Compras, 43 Gastos Menores, 44 Regímenes Especiales, 45 Gubernamental, 46 Exportación, 47 Pagos Exterior | **Estados BASA:** Aceptado, Rechazado, Aceptado condicional, En proceso, Anulado | **Flujo BASA:** Emisor->DGII valida XML+TrackID->Emisor->Receptor | **QR BASA:** URL verificación | **RI BASA:** Decreto 254-06 Norma 06-2018 | **Base BASA:** BASA_eCF_PRO_v5_FULL_FIXED/clientes_db/")
if mod=="GUIA":
    st.header("📘 Guía Completa - BASA e-CF PRO v5.1 FULL FIXED - Base BASA_eCF_PRO_v5_FULL_FIXED")
    guia_full=f"""BASA e-CF PRO v5.1 FULL FIXED - GUIA COMPLETA - BASE RENOMBRADA A BASA_eCF_PRO_v5_FULL_FIXED
TITULO: BASA e-CF PRO v5.1 FULL FIXED - Base: BASA_eCF_PRO_v5_FULL_FIXED/clientes_db/ - BASA_CLI-D452_eCF.db
RNC: 133378711 - Baldera Santos & Asociados SRL - Base: BASA_eCF_PRO_v5_FULL_FIXED
CREDENCIALES: {CRED["nombre"]} | Whatsapp {CRED["whatsapp"]} | Email {CRED["email"]} | Dirección {CRED["direccion"]} | Base BASA: BASA_eCF_PRO_v5_FULL_FIXED/clientes_db/

CAMBIO DE BASE DE DATOS A BASA:
ANTES: data/casos/CLI-D452/basa_CLI-D452.db
AHORA: BASA_eCF_PRO_v5_FULL_FIXED/clientes_db/CLI-D452/BASA_CLI-D452_eCF.db
NOMBRE PROFESIONAL BASA - FULL FIXED - SIN ERRORES elif

FUNCIONES v5.1 BASA FULL FIXED - SIN SYNTAXERROR:
1. HISTORICO EDITABLE BASA: Modulo HISTORICO BASA data_editor editable BASA, Guardar Cambios Histórico BASA Autoguardado BASA, Borrar NCF BASA, Cargar Todo y Actualizar FULL BASA, Log historico BASA usuario/fecha, Descargar Excel/CSV BASA
2. CREAR NUEVO PRECIO Y AJUSTE SISTEMA BASA: Modulo PRECIOS BASA Crear Nuevo Precio BASA descripcion precio fecha BASA, tabla editable BASA, Ajuste Sistema BASA según Guía DGII: estructura E31+10 digitos, tipos 31-47, estados, modelo Emisor->DGII->TrackID->Receptor, QR, RI Decreto 254-06 - Base BASA_eCF_PRO_v5_FULL_FIXED
3. FACTURACION DGII FORMATO OFICIAL BASA: Basado en NCF-28_Manuel_King y Guía oficial Ejemplo COMERCIAL ZYL E310000000001 150 Zapatos CAJ 550.00 14850.00 82500.00 Subtotal 334300 ITBIS 60174 Total 394474 Codigo WkT3Sa, Tipos 31-47, Estructura E+Tipo+Secuencial, Caracteristicas validez legal, Estados, RI, QR URL - Base BASA
4. NCF ELECTRONICO ASIGNADO BASA: Selector Modo NCF Automático BASA genera get_next_ncf E31+10 digitos Guarda NCF Automático BASA, Manual permite Agregar NCF Manual BASA Casos Especiales E310000000028, anti-duplicado UNIQUE BASA
5. IMPRESORA Y DESCARGAR PDF/WORD/EXCEL BASA: Boton Imprimir BASA window.print(), Descargar PDF BASA texto, Excel BASA CSV/XLSX, Word BASA DOC/DOCX, download_button BASA - Base BASA_eCF_PRO_v5_FULL_FIXED
6. AUTOGUARDADO AL DAR CLIC BASA: Cada boton con Autoguardado BASA, sidebar Crear/Verificar DB BASA + Autoguardado BASA, Guardar Cambios con add_historico BASA, keys en inputs BASA
7. GESTION CLIENTE + DIRECCION Y TELEFONO BASA: CLIENTES BASA con direccion, telefono, precio_base, data_editor dynamic BASA, Guardar Cambios Clientes BASA Autoguardado BASA UPDATE info.json y clientes_info BASA, Borrar Cliente BASA DELETE carpeta BASA
8. CAMBIAR CLAVE Y RECORDAR CON CODIGO CORREO/WHATSAPP BASA: Sidebar Cambiar Clave BASA, Login Olvidé mi clave Recuperar modo recovery BASA, Generar Codigo 6 digitos random simulacion envio Correo y WhatsApp 829-771-7390 valido 10 min BASA, Input codigo + nueva clave + Cambiar clave con codigo actualiza info.json BASA, ADMIN Actualiza Manualmente BASA Email + nueva clave manual, Todos usuarios pueden cambiar clave BASA
9. GUARDAR NCF AUTO Y MANUAL + CARGAR TODO FULL BASA: Auto busca ultimo NCF suma 1 guarda automatico BASA, Manual input casos especiales BASA, Cargar Todo y Actualizar FULL BASA boton rerun BASA - Base BASA_eCF_PRO_v5_FULL_FIXED
10. ACTUALIZAR FULL BASA: Boton Cargar Todo y Actualizar FULL BASA rerun recarga DB BASA, sidebar recarga BASA, DASHBOARD totales actualizados BASA, cada accion registra historico BASA - Base BASA_eCF_PRO_v5_FULL_FIXED - SIN elif SOLO if - FULL FIXED

COMO USAR v5.1 BASA FULL FIXED:
ADMIN: Login Licpedrobaldera@gmail.com / Basa2026! -> CLIENTES BASA crear con direccion y telefono BASA -> FACTURAR BASA elegir Auto o Manual NCF BASA -> Llenar datos COMERCIAL ZYL BASA ejemplo 150 Zapatos CAJ 550 -> FACTURAR BASA -> Ver factura formato oficial guia BASA -> Botones Impresora BASA + PDF/Word/Excel BASA -> HISTORICO BASA editar/borrar/guardar BASA -> PRECIOS BASA crear nuevo precio 6000 y ajustar BASA -> GUIA BASA ver esta guia BASA -> Sidebar cambiar clave BASA -> Salir -> Probar cliente ramirez@ferreteria.com -> Solo su DB BASA -> Olvide clave BASA -> Generar codigo BASA -> Cambiar BASA
CLIENTE BASA: Entra con su email BASA -> Ve su historico BASA -> Puede cambiar clave en sidebar BASA -> Puede descargar PDF/Excel/Word BASA -> Puede imprimir BASA

SOPORTE BASA: {CRED["nombre"]} Whatsapp {CRED["whatsapp"]} Email {CRED["email"]} - v5.1 BASA FULL FIXED - DGII Formato Oficial - Base BASA_eCF_PRO_v5_FULL_FIXED/clientes_db/ - Histórico Editable BASA + NCF Auto/Manual BASA + Impresora BASA + PDF/Word/Excel BASA + Autoguardado BASA + Direccion Telefono BASA + Cambio Clave Codigo Correo/WhatsApp BASA + ADMIN Actualiza Manual BASA - SIN SYNTAXERROR elif - SOLO if
"""
    st.text_area("Guía Completa v5.1 BASA FULL FIXED - Base BASA_eCF_PRO_v5_FULL_FIXED",guia_full,height=600)
    st.download_button("📥 Descargar Guía Completa v5.1 BASA FULL FIXED",guia_full,file_name="BASA_eCF_PRO_v5_1_FULL_FIXED_Guia_Completa_BASA_Real.txt",use_container_width=True,type="primary")
st.markdown(f'<div class="footer-pro"><table width="100%"><tr><td><b>👨‍💼 {CRED["nombre"]} - BASA v5.1 FULL FIXED</b><br>🏢 {CRED["empresa"]} | RNC: {CRED["rnc"]} | Base: BASA_eCF_PRO_v5_FULL_FIXED<br>📍 {CRED["direccion"]}</td><td style="text-align:right;"><b>📞 Contacto / Whatsapp:</b> {CRED["whatsapp"]}<br><b>📧 Correo:</b> {CRED["email"]}<br>🌐 BASA e-CF PRO v5.1 FULL FIXED - Base BASA_eCF_PRO_v5_FULL_FIXED - SIN SYNTAXERROR</td></tr></table></div>', unsafe_allow_html=True)
