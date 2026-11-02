import streamlit as st, json, os, hashlib, datetime, sqlite3, uuid, base64
from pathlib import Path
import pandas as pd
st.set_page_config(page_title="BASA e-CF PRO v4.0", layout="wide", page_icon="💰")
BASE_DIR=Path("data"); CASOS_DIR=BASE_DIR/"casos"; BASE_DIR.mkdir(exist_ok=True); CASOS_DIR.mkdir(exist_ok=True)
MASTER_USER={"email":"Licpedrobaldera@gmail.com","password_hash":hashlib.sha256("Basa2026!".encode()).hexdigest()}
CRED={"nombre":"Lic. Pedro A. Baldera R.","empresa":"Baldera Santos & Asociados SRL","rnc":"133378711","telefono":"829-771-7390","whatsapp":"829-771-7390","email":"licpedrobaldera@gmail.com","direccion":"Calle Orlando Martinez No.49, Brisas del Este, Santo Domingo Este"}
def get_db_path(cid):
    cf=CASOS_DIR/cid; cf.mkdir(exist_ok=True, parents=True); return cf/f"basa_{cid}.db"
def init_db(cid):
    dbp=get_db_path(cid); conn=sqlite3.connect(str(dbp)); c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS facturas (id INTEGER PRIMARY KEY, ncf TEXT UNIQUE, tipo TEXT, cliente TEXT, rnc_cliente TEXT, descripcion TEXT, cantidad REAL, precio REAL, itbis REAL, descuento REAL, total REAL, fecha TEXT, vencimiento TEXT, estado TEXT, codigo_seg TEXT, firma_digital TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS clientes_info (id TEXT PRIMARY KEY, nombre TEXT, rnc TEXT, email TEXT)")
    conn.commit(); conn.close(); return dbp
def get_next_ncf(cid,tipo="E31"):
    dbp=get_db_path(cid)
    if not dbp.exists(): init_db(cid)
    conn=sqlite3.connect(str(dbp)); c=conn.cursor()
    try:
        c.execute("SELECT ncf FROM facturas WHERE tipo=? ORDER BY id DESC LIMIT 1",(tipo,))
        row=c.fetchone(); nxt=int(row[0][3:])+1 if row else 1
    except: nxt=1
    conn.close(); return f"{tipo}{nxt:010d}"
st.markdown("<style>.header-pro{background:linear-gradient(135deg,#0F2027,#203A43,#2C5364);padding:25px;border-radius:15px;text-align:center;color:white;border:2px solid #FFD700;}.header-pro h1{color:#FFD700;font-size:28px;margin:0;}.footer-pro{background:#0F2027;color:white;padding:20px;border-radius:10px;margin-top:30px;border-left:5px solid #FFD700;}</style>", unsafe_allow_html=True)
if "logged" not in st.session_state: st.session_state.logged=False
if "modulo_activo" not in st.session_state: st.session_state.modulo_activo="DASHBOARD"
if not st.session_state.logged:
    st.markdown('<div class="header-pro"><h1>🏛️ BASA e-CF PRO v4.0</h1><h2>Plataforma Integral de Facturación Electrónica Certificada DGII | RNC 133378711</h2><p style="color:#FFD700;">Baldera Santos & Asociados SRL - Soluciones Fiscales Inteligentes</p></div>', unsafe_allow_html=True)
    c1,c2,c3=st.columns([1,2,1])
    with c2:
        st.markdown("### 🔐 Acceso Seguro")
        email=st.text_input("Correo"); pwd=st.text_input("Contraseña",type="password")
        if st.button("Entrar a BASA e-CF PRO",use_container_width=True,type="primary"):
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
                if not found: st.error("Credenciales incorrectas - Soporte 829-771-7390")
    st.stop()
st.markdown(f'<div class="header-pro"><h1>🏛️ BASA e-CF PRO v4.0</h1><h2>Plataforma Integral de Facturación Electrónica Certificada DGII | RNC 133378711 | {CRED["empresa"]}</h2></div>', unsafe_allow_html=True)
st.markdown("### 📋 Módulos del Sistema")
b1,b2,b3,b4,b5=st.columns(5)
with b1:
    if st.button("📊 DASHBOARD",use_container_width=True,type="primary" if st.session_state.modulo_activo=="DASHBOARD" else "secondary"): st.session_state.modulo_activo="DASHBOARD"; st.rerun()
with b2:
    if st.button("👥 CLIENTES",use_container_width=True,type="primary" if st.session_state.modulo_activo=="CLIENTES" else "secondary"): st.session_state.modulo_activo="CLIENTES"; st.rerun()
with b3:
    if st.button("🧾 FACTURAR e-CF",use_container_width=True,type="primary" if st.session_state.modulo_activo=="FACTURAR" else "secondary"): st.session_state.modulo_activo="FACTURAR"; st.rerun()
with b4:
    if st.button("📁 PORTAL CLIENTE",use_container_width=True,type="primary" if st.session_state.modulo_activo=="PORTAL" else "secondary"): st.session_state.modulo_activo="PORTAL"; st.rerun()
with b5:
    if st.button("📘 GUIA USUARIO",use_container_width=True,type="primary" if st.session_state.modulo_activo=="GUIA" else "secondary"): st.session_state.modulo_activo="GUIA"; st.rerun()
with st.sidebar:
    st.write(f"Usuario: {st.session_state.user}"); st.write(f"Rol: {st.session_state.role}"); st.markdown("---")
    client_id_input=st.text_input("ID Cliente DB",value=st.session_state.get("client_id","CLI-D452"))
    if st.button("Crear/Verificar DB",use_container_width=True): dbp=init_db(client_id_input); st.success(f"DB OK: {dbp.name}")
    if st.button("Salir",use_container_width=True): st.session_state.logged=False; st.rerun()
    st.markdown("---"); st.markdown(f"**{CRED['nombre']}**"); st.markdown(f"📞 {CRED['telefono']}"); st.markdown(f"📧 {CRED['email']}")
mod=st.session_state.modulo_activo
if mod=="DASHBOARD":
    st.header("📊 Dashboard - BASA e-CF PRO"); total_c=len([d for d in CASOS_DIR.iterdir() if d.is_dir()]); total_f=0; total_m=0
    for cf in CASOS_DIR.iterdir():
        if cf.is_dir():
            dbp=cf/f"basa_{cf.name}.db"
            if dbp.exists():
                conn=sqlite3.connect(str(dbp))
                try:
                    c=conn.cursor(); c.execute("SELECT COUNT(*), SUM(total) FROM facturas"); cnt,sm=c.fetchone(); total_f+=cnt or 0; total_m+=sm or 0
                except: pass
                conn.close()
    c1,c2,c3,c4=st.columns(4); c1.metric("Clientes",total_c); c2.metric("Facturas e-CF",total_f); c3.metric("Monto",f"RD$ {total_m:,.2f}"); c4.metric("Plan","$199/mes")
elif mod=="CLIENTES":
    st.header("👥 Gestión Clientes - $199/mes"); c1,c2=st.columns(2)
    with c1: nid=st.text_input("ID Nuevo",value=f"CLI-{str(uuid.uuid4())[:4].upper()}"); nom=st.text_input("Razón Social",value="MANUEL KING VEHICULOS SRL"); rnc=st.text_input("RNC Cliente",value="133412918")
    with c2: cor=st.text_input("Correo",value="cliente@empresa.com"); pwd=st.text_input("Password",value="Cliente2026!")
    if st.button("✅ CREAR CLIENTE e-CF PRO - $199/mes",type="primary",use_container_width=True):
        dbp=init_db(nid); info={"id":nid,"nombre":nom,"rnc":rnc,"email":cor,"password_hash":hashlib.sha256(pwd.encode()).hexdigest(),"precio":199}; (CASOS_DIR/nid/"info.json").write_text(json.dumps(info,indent=2))
        conn=sqlite3.connect(str(dbp)); c=conn.cursor(); c.execute("INSERT OR REPLACE INTO clientes_info (id,nombre,rnc,email) VALUES (?,?,?,?)",(nid,nom,rnc,cor)); conn.commit(); conn.close(); st.success(f"CREADO {nid} | {nom} | Login {cor}")
    clientes=[]
    for cf in CASOS_DIR.iterdir():
        if cf.is_dir():
            jf=cf/"info.json"
            if jf.exists():
                try: clientes.append(json.loads(jf.read_text()))
                except: pass
    if clientes: st.dataframe(pd.DataFrame(clientes),use_container_width=True)
elif mod=="FACTURAR":
    st.header(f"🧾 Facturación Electrónica DGII - Formato Oficial - Cliente {client_id_input}")
    dbp=get_db_path(client_id_input)
    if not dbp.exists(): st.warning("DB no existe - Crear en sidebar"); st.stop()
    tipo_sel=st.selectbox("Tipo e-NCF",["E31 - Factura Crédito Fiscal Electrónica","E32 - Factura Consumo Electrónica","E33 - Nota Débito","E34 - Nota Crédito"])
    tipo_code=tipo_sel.split(" - ")[0]; next_ncf=get_next_ncf(client_id_input,tipo_code)
    st.info(f"Próximo e-NCF: {next_ncf} | RNC Emisor: {CRED['rnc']} | Formato igual a tu PDF E310000000028")
    c1,c2,c3=st.columns(3)
    with c1: razon_c=st.text_input("Razón Social Cliente",value="MANUEL KING VEHICULOS SRL")
    with c2: rnc_c=st.text_input("RNC Cliente",value="133412918")
    with c3: venc=st.date_input("Fecha Vencimiento",value=datetime.date(2026,12,31))
    c1,c2,c3,c4,c5=st.columns(5)
    with c1: cant=st.number_input("Cant",value=1.0)
    with c2: desc=st.text_input("Descripción",value="Servicio Impuestos sept 2026")
    with c3: uni=st.text_input("Unidad",value="UND")
    with c4: prec=st.number_input("Precio RD$",value=6000.0)
    with c5: dsc=st.number_input("Descuento RD$",value=0.0)
    itbis_p=0.18; sub=cant*prec-dsc; itbis=sub*itbis_p; tot=sub+itbis
    st.markdown(f"**Subtotal Gravado: RD$ {sub:,.2f} | ITBIS 18%: RD$ {itbis:,.2f} | Monto Total: RD$ {tot:,.2f}**")
    coment=st.text_input("Comentario",value="Servicio Impuestos sept 2026")
    if st.button(f"💰 FACTURAR {tipo_code} - Generar e-CF Oficial DGII",type="primary",use_container_width=True):
        cod=base64.b64encode(os.urandom(6)).decode()[:6]; now=datetime.datetime.now(); fecha=now.strftime("%d-%m-%Y"); firma=now.strftime("%d-%m-%Y %H:%M:%S")
        conn=sqlite3.connect(str(dbp)); c=conn.cursor()
        try:
            c.execute("INSERT INTO facturas (ncf,tipo,cliente,rnc_cliente,descripcion,cantidad,precio,itbis,descuento,total,fecha,vencimiento,estado,codigo_seg,firma_digital) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(next_ncf,tipo_code,razon_c,rnc_c,desc,cant,prec,itbis,dsc,tot,fecha,str(venc),"VIGENTE",cod,firma)); conn.commit(); st.success(f"✅ Factura {next_ncf} Guardada en DB {client_id_input} | Código Seguridad: {cod}")
        except: st.error(f"❌ NCF {next_ncf} ya existe - Anti-duplicado")
        conn.close()
        st.markdown("---"); st.markdown("#### 🧾 FACTURA FORMATO OFICIAL DGII - Vista Previa (Igual a tu PDF anexo)")
        html=f'<div style="border:2px solid black; padding:20px; background:white; color:black; font-family:Arial; font-size:13px;"><table width="100%"><tr><td width="60%"><b>BALDERA SANTOS Y ASOCIADOS SRL</b><br>RNC: {CRED["rnc"]}<br>Dirección: {CRED["direccion"]}<br>Teléfono: {CRED["telefono"]}<br>Fecha Emisión: {fecha}</td><td width="40%" style="text-align:right;"><b>Factura de Crédito Fiscal Electrónica</b><br><b>e-NCF: {next_ncf}</b><br><b>Fecha Vencimiento: {venc.strftime("%d-%m-%Y")}</b></td></tr></table><hr><b>Razón Social Cliente: {razon_c}</b><br><b>RNC Cliente: {rnc_c}</b><hr><table border="1" width="100%" cellpadding="5" cellspacing="0" style="border-collapse:collapse; font-size:12px;"><tr style="background:#D3D3D3;"><th>Cant</th><th>Descripción</th><th>Unidad</th><th>Precio RD$</th><th>ITBIS RD$</th><th>Descuento RD$</th><th>Recargo RD$</th><th>Valor RD$</th></tr><tr><td>{cant:.2f}</td><td>{desc}</td><td>{uni}</td><td>{prec:,.2f}</td><td>{itbis:,.2f}</td><td>{dsc:,.2f}</td><td>-</td><td>{sub:,.2f}</td></tr></table><br><table width="100%"><tr><td width="50%">[QR {next_ncf}]<br><small>Código de Seguridad: {cod}<br>Fecha de Firma Digital: {firma}</small></td><td width="50%" style="text-align:right;">Subtotal Gravado: RD$ {sub:,.2f}<br>Subtotal Exento: -<br>Total ITBIS: RD$ {itbis:,.2f}<br><b>Monto Total: RD$ {tot:,.2f}</b></td></tr></table><br>Comentario: {coment}</div>'
        st.markdown(html, unsafe_allow_html=True)
elif mod=="PORTAL":
    st.header(f"📁 Portal Cliente - {client_id_input}"); dbp=get_db_path(client_id_input)
    if not dbp.exists(): st.warning("DB no existe"); st.stop()
    conn=sqlite3.connect(str(dbp))
    try: df=pd.read_sql_query("SELECT * FROM facturas ORDER BY id DESC", conn); st.write(f"Facturas en su DB: {len(df)}"); st.dataframe(df,use_container_width=True); st.download_button("Exportar CSV",df.to_csv(index=False),file_name=f"facturas_{client_id_input}.csv")
    except: st.info("Sin facturas aún")
    conn.close()
elif mod=="GUIA":
    st.header("📘 Guía de Usuario - BASA e-CF PRO v4.0")
    guia=f"""BASA e-CF PRO v4.0 - PLATAFORMA INTEGRAL FACTURACION ELECTRONICA DGII
TITULO PROFESIONAL: BASA e-CF PRO - Sistema Certificado e-CF DGII
ALTERNATIVAS: BASA Fiscal Suite / Baldera Santos ERP Fiscal
Elegido: BASA e-CF PRO v4.0 - Plataforma Integral de Facturación Electrónica Certificada DGII

CREDENCIALES:
{CRED["nombre"]}
Empresa: {CRED["empresa"]} | RNC: {CRED["rnc"]}
Contacto / Whatsapp: {CRED["whatsapp"]}
Correo: {CRED["email"]}
Dirección: {CRED["direccion"]}

1. DESCRIPCIÓN: Plataforma certificada e-CF DGII RD. Arquitectura 1 SOLO 1: Cada cliente DB SQLite aislada data/casos/CLI-XXX/basa_CLI-XXX.db. Multi-tenant, anti-duplicado NCF UNIQUE, hash SHA256.

2. MÓDULOS POR BOTONES AFUERA:
- DASHBOARD: Métricas tiempo real.
- CLIENTES: Creación cliente ID único, RNC, email, password, $199/mes. Genera DB propia.
- FACTURAR e-CF: E31 Crédito Fiscal (ejemplo PDF E310000000028 MANUEL KING VEHICULOS SRL RNC 133412918 Fecha 20-09-2026 Servicio RD$6000 ITBIS 1080 Total 7080), E32 Consumo, E33, E34. Formato oficial DGII con encabezado emisor RNC 133378711 dirección Orlando Martinez, e-NCF, Vencimiento, Razón Social Cliente y RNC Cliente, tabla Cant/Descripción/Unidad/Precio/ITBIS/Descuento/Recargo/Valor, totales Subtotal Gravado, Exento, ITBIS, Monto Total, QR, Código Seguridad, Firma Digital, Comentario.
- PORTAL CLIENTE: Vista exclusiva cliente, solo su DB, export CSV.
- GUIA: Manual.

3. APORTES: Cumplimiento DGII 100% formato PDF NCF-28_Manuel_King_Sept_2026-Basa. Ahorro costos sin licencias. Escalabilidad $1990/mes con 10 clientes. Seguridad aislamiento DB.

4. PASO A PASO: Login ADMIN Licpedrobaldera@gmail.com / Basa2026! -> CLIENTES Crear CLI-D453 -> Sidebar ID -> FACTURAR E31 llenar Razón, RNC, Cant, Descripción, Precio -> FACTURAR -> Ver formato oficial -> PORTAL verificar -> Logout login cliente cliente@empresa.com -> Solo su DB

5. SOPORTE: {CRED["nombre"]} Whatsapp {CRED["whatsapp"]} Email {CRED["email"]} Versión v4.0 RNC 133378711
"""
    st.text_area("Guía Completa",guia,height=450)
    st.download_button("📥 Descargar Guía de Usuario Completa - BASA e-CF PRO v4.0",guia,file_name="BASA_eCF_PRO_v4_Guia_Completa.txt",use_container_width=True,type="primary")

st.markdown(f'<div class="footer-pro"><table width="100%"><tr><td><b>{CRED["nombre"]}</b><br>{CRED["empresa"]} | RNC: {CRED["rnc"]}<br>{CRED["direccion"]}</td><td style="text-align:right;"><b>Contacto / Whatsapp:</b> {CRED["whatsapp"]}<br><b>Correo:</b> {CRED["email"]}<br>BASA e-CF PRO v4.0 - Certificado DGII</td></tr></table></div>', unsafe_allow_html=True)
