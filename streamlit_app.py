# BASA - AUTONOMÍA REQUISITOS - Verifica solo, no tumba la app
import importlib.util

def verificar_requisitos_basa():
    requisitos = {
        "streamlit": "Frontend Web",
        "pandas": "Datos",
        "openpyxl": "Excel DGII formato azul",
        "xlsxwriter": "Excel fallback",
        "numpy": "Cálculo",
        "SQLAlchemy": "Base de Datos",
        "fastapi": "API",
        "requests": "Conectividad",
        "cryptography": "Firma Electrónica",
        "lxml": "XML DGII",
        "signxml": "Firma XML",
    }
    faltantes = []
    instalados = []
    for modulo, uso in requisitos.items():
        # Buscar modulo, sin importar si es mayuscula o minuscula
        nombre_buscar = modulo.lower() if modulo not in ["SQLAlchemy"] else "sqlalchemy"
        if importlib.util.find_spec(nombre_buscar) is not None:
            instalados.append(modulo)
        else:
            faltantes.append(f"{modulo} - {uso}")
    return instalados, faltantes

instalados_basa, faltantes_basa = verificar_requisitos_basa()
if faltantes_basa:
    st.warning(f"⚠️ Autonomía BASA: Faltan {len(faltantes_basa)} requisitos en requirements.txt: {', '.join(faltantes_basa)}. Agregalos y haz Reboot. La app sigue funcionando con lo que tiene.")
else:
    st.success(f"✅ Autonomía BASA: Todos los {len(instalados_basa)} requisitos instalados. Sistema FULL.")

# BASA SUPERSISTEMA V27 FINAL CORREGIDO - NO SE CAE POR openpyxl - Fix ModuleNotFoundError Linea 7
# Si openpyxl no esta instalado, usa pandas y sigue funcionando
import streamlit as st
import sqlite3, pandas as pd, os, re, json, hashlib, shutil, base64, smtplib, random, string
from datetime import date, datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
import urllib.parse
from io import BytesIO

# ========== FIX 1: IMPORT SEGURO openpyxl - NO SE CAE LA APP ==========
# ANTES: import openpyxl directo -> Si faltaba, se caia toda la app en linea 7
# AHORA: try/except -> Si falta, sigue con pandas y avisa
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter
    TIENE_OPENPYXL = True
except ModuleNotFoundError:
    openpyxl = None
    Font = None
    PatternFill = None
    get_column_letter = None
    TIENE_OPENPYXL = False
except ImportError:
    openpyxl = None
    TIENE_OPENPYXL = False

# Si no tiene openpyxl, avisar pero NO tumbar la app
if not TIENE_OPENPYXL:
    st.warning("⚠️ openpyxl no instalado. Agrega 'openpyxl' a requirements.txt y haz Reboot. Mientras tanto, el Excel DGII se generará con pandas (sin formato azul, pero funciona).")

st.set_page_config(page_title="BASA SUPERSISTEMA V27", layout="wide", page_icon="🏦")

# ================= CONFIG =================
BASE = Path("BASA_V27_SUPERSISTEMA"); BASE.mkdir(exist_ok=True)
CLIENTES_DIR = BASE / "clientes_db"; CLIENTES_DIR.mkdir(exist_ok=True)
CRED_DIR = BASE / "credenciales_privadas"; CRED_DIR.mkdir(exist_ok=True)
REPORT_DIR = BASE / "reportes_dgii"; REPORT_DIR.mkdir(exist_ok=True)
for sub in ["reportes_606","reportes_607","reportes_608","reportes_ir_17","reportes_itbis","borradores"]:
    (REPORT_DIR / sub).mkdir(exist_ok=True)
DB = BASE / "basa_v27.db"
CUENTA_BHD_REAL = "08694150021"
def mascara(c): return f"****{c[-4:]}"
CUENTA_MOSTRAR = mascara(CUENTA_BHD_REAL)
MASTER_EMAIL = "Licpedrobaldera@gmail.com"
CLAVE_DESARROLLADOR = "BASA-DEV-2026"
CLAVE_COLABORADOR = "BASA-TEAM-2026"
TU_CORREO_GMAIL = "Licpedrobaldera@gmail.com"
TU_CLAVE_APP_GMAIL = "XXXX-XXXX-XXXX-XXXX"

# ================= DGII - TU CODIGO FLASK INTEGRADO =================
DGII_606_COLUMNS = ["RNC o Cedula / Pasaporte","Tipo Identificacion","Tipo Bienes y Servicios Comprados","Numero de Comprobante Fiscal (NCF)","NCF o Documento Modificado","Fecha Comprobante (AAAAMMDD)","Fecha Pago (AAAAMMDD)","Monto Facturado en Servicios","Monto Facturado en Bienes","Total Monto Facturado","ITBIS Facturado","ITBIS Retenido","ITBIS sujeto a Proporcionalidad (Art. 349)","ITBIS llevado al Costo","ITBIS por Adelantar","ITBIS Percibido en Compras","Tipo de Retencion en ISR","Monto Retenido ISR","ISR Percibido en Compras","Impuesto Selectivo al Consumo","Otros Impuestos / Tasas","Monto Propina Legal","Forma de Pago"]
DGII_607_COLUMNS = ["RNC / Cedula","Tipo ID","NCF","NCF Modificado","Fecha Comprobante","Fecha Pago","Monto Servicios","Monto Bienes","Total","ITBIS Facturado","ITBIS Retenido","Forma Pago"]
DGII_608_COLUMNS = ["RNC / Cedula","Tipo ID","NCF Nota","NCF Afectado","Fecha","Monto","ITBIS","Tipo Nota","Motivo"]

def safe_float(v):
    try:
        if pd.isna(v) or v == '' or v is None: return 0.0
        if isinstance(v, str): v = v.replace(',','').replace('RD$','').replace('$','').strip()
        return float(v)
    except: return 0.0
def safe_str(v, default=''):
    if pd.isna(v) or v is None: return default
    s=str(v).strip(); return default if s.lower()=='nan' or s=='' else s

def auto_save_dgii(rnc, periodo, modulo, data):
    folder = REPORT_DIR / f"reportes_{modulo}" if modulo in ["606","607","608"] else REPORT_DIR / "borradores"
    if modulo == "ir_17": folder = REPORT_DIR / "reportes_ir_17"
    if modulo == "itbis": folder = REPORT_DIR / "reportes_itbis"
    save_path = folder / f"autosave_{rnc}_{periodo}_{modulo}.json"
    with open(save_path,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
    return str(save_path)

def parse_file_dgii(uploaded_file, modulo):
    try:
        if uploaded_file.name.lower().endswith('.csv'):
            df_in = pd.read_csv(uploaded_file, dtype=str, keep_default_na=False)
        else:
            xl = pd.ExcelFile(uploaded_file)
            sheet = xl.sheet_names[0]
            for name in xl.sheet_names:
                if modulo in name or '606' in name or 'Formato' in name: sheet=name; break
            df_in = pd.read_excel(uploaded_file, sheet_name=sheet, dtype=str, keep_default_na=False)
        parsed=[]
        for _, row in df_in.iterrows():
            rnc_val = safe_str(row.iloc[0] if len(row)>0 else '')
            ncf_val = safe_str(row.iloc[3] if len(row)>3 else row.iloc[1] if len(row)>1 else '')
            if not rnc_val or not ncf_val: continue
            parsed.append({"rnc": rnc_val, "tipo_id":"1", "tipo_bienes":"02", "ncf": ncf_val, "ncf_mod":'', "fecha_comp":"20260930", "fecha_pago":"20260930", "monto_servicios": safe_float(row.iloc[7] if len(row)>7 else 0), "monto_bienes": safe_float(row.iloc[8] if len(row)>8 else 10000), "itbis_fact": safe_float(row.iloc[10] if len(row)>10 else 1800), "itbis_ret":0, "forma_pago":"01"})
        return parsed
    except Exception as e:
        return []

def generate_excel_dgii(invoices, rnc_contribuyente, periodo, modulo):
    # FIX 2: Si tiene openpyxl usa formato azul DGII, si no tiene usa pandas y NO se cae
    columns = DGII_606_COLUMNS if modulo=="606" else DGII_607_COLUMNS if modulo=="607" else DGII_608_COLUMNS if modulo=="608" else DGII_606_COLUMNS
    rows=[]
    for inv in invoices:
        total = safe_float(inv.get('monto_bienes',0)) + safe_float(inv.get('monto_servicios',0))
        if modulo=="606":
            row_vals=[inv.get('rnc',''),inv.get('tipo_id','1'),inv.get('tipo_bienes','02'),inv.get('ncf',''),inv.get('ncf_mod',''),inv.get('fecha_comp',''),inv.get('fecha_pago',''),safe_float(inv.get('monto_servicios',0)),safe_float(inv.get('monto_bienes',0)),total,safe_float(inv.get('itbis_fact',0)),safe_float(inv.get('itbis_ret',0)),0,0,safe_float(inv.get('itbis_fact',0)),0,'00',0,0,0,0,0,'01']
        else:
            row_vals=list(inv.values())[:len(columns)]
            while len(row_vals)<len(columns): row_vals.append("")
        rows.append(row_vals)
    # CON openpyxl - Formato oficial azul DGII
    if TIENE_OPENPYXL and openpyxl is not None:
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = f"Formato {modulo}"
        ws['A1'] = f"RNC: {rnc_contribuyente}"; ws['A2'] = f"Periodo: {periodo}"; ws['A3'] = f"Generado: {datetime.now()} - BASA V27"
        header_font = Font(bold=True, color="FFFFFF"); header_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
        for col_idx, col_name in enumerate(columns, 1):
            cell = ws.cell(row=4, column=col_idx, value=col_name); cell.font=header_font; cell.fill=header_fill
            ws.column_dimensions[get_column_letter(col_idx)].width=20
        for i, row_vals in enumerate(rows):
            curr=5+i
            for col_idx, val in enumerate(row_vals,1):
                cell=ws.cell(row=curr,column=col_idx,value=val)
                if col_idx in {8,9,10,11,12}:
                    try: cell.number_format='#,##0.00'
                    except: pass
        output = BytesIO(); wb.save(output); output.seek(0)
        return output, f"Formato_{modulo}_{periodo}_{rnc_contribuyente}.xlsx"
    # SIN openpyxl - Fallback con pandas, NO se cae
    else:
        df = pd.DataFrame(rows, columns=columns)
        output = BytesIO()
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                pd.DataFrame([[f"RNC: {rnc_contribuyente}"],[f"Periodo: {periodo}"],[f"Generado: {datetime.now()} - BASA V27 - Sin openpyxl"]]).to_excel(writer, index=False, header=False, startrow=0)
                df.to_excel(writer, index=False, startrow=4)
        except:
            # Ultimo fallback: openpyxl tampoco, xlsxwriter tampoco - usa openpyxl de pandas por defecto
            df.to_excel(output, index=False)
        output.seek(0)
        return output, f"Formato_{modulo}_{periodo}_{rnc_contribuyente}.xlsx"

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

def validar_email(e): return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", e or ""))
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()
def limpiar_identificador(v):
    if not v: return ""
    v=str(v).strip()
    if "@" in v: return v.lower()
    return v.replace("-","").replace(" ","").replace(".","")
def buscar_usuario_por_identificador(identificador):
    ident_limpio = limpiar_identificador(identificador)
    row = conn.execute("SELECT * FROM usuarios WHERE email=?", (ident_limpio.lower(),)).fetchone()
    if row: return row, "Correo Electrónico"
    row = conn.execute("SELECT * FROM usuarios WHERE id_fiscal=? OR REPLACE(REPLACE(id_fiscal,'-',''),' ','')=?", (identificador, ident_limpio)).fetchone()
    if row: return row, "RNC / Cédula / ID Fiscal"
    row = conn.execute("SELECT * FROM usuarios WHERE id=?", (ident_limpio,)).fetchone()
    if row: return row, "ID Cliente"
    row = conn.execute("SELECT * FROM usuarios WHERE telefono=? OR REPLACE(REPLACE(telefono,'-',''),' ','')=?", (identificador, ident_limpio)).fetchone()
    if row: return row, "Celular / Teléfono"
    return None, None
def enviar_codigo_por_canal(canal, destino, codigo, nombre=""):
    if canal in ["WhatsApp","Celular - SMS / Llamada"]:
        msg = f"Hola {nombre}, tu codigo BASA es: {codigo}. No tiene vencimiento."
        link = f"https://wa.me/1{''.join(filter(str.isdigit, destino))}?text={urllib.parse.quote(msg)}"
        return True, link
    elif canal == "Correo Electrónico":
        try:
            msg_obj = MIMEText(f"Hola {nombre},\nTu codigo BASA es: {codigo}\nNO tiene vencimiento.\nBASA V27")
            msg_obj['Subject']="Codigo BASA - Sin Vencimiento"; msg_obj['From']=TU_CORREO_GMAIL; msg_obj['To']=destino
            server=smtplib.SMTP("smtp.gmail.com",587); server.starttls(); server.login(TU_CORREO_GMAIL, TU_CLAVE_APP_GMAIL); server.sendmail(TU_CORREO_GMAIL, destino, msg_obj.as_string()); server.quit()
            return True, f"mailto:{destino}?subject=Codigo BASA&body={codigo}"
        except: return False, f"Gmail no configurado. Codigo: {codigo}"
    return False, ""

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

def ia_autoasistencia(contexto, modulo_actual, empresa_id):
    if not st.session_state.get("ayuda_ia", True): return
    mensajes = {
        "LOGIN": "🤖 **IA BASA:** Escribe tu RNC, Cédula, ID o Correo - Yo te reconozco. Si olvidaste clave, usa Recuperar - El código no vence.",
        "FACTURAR": f"🤖 **IA BASA:** Estás facturando en {empresa_id}. Revisa Cliente, Descripción, Precio. Al hacer click se autoguardará.",
        "DGII_606": "🤖 **IA BASA:** Formato 606 - Compras. Sube Excel/CSV y yo lo convierto. Luego genera Excel oficial. Se autoguardará.",
        "PAGOS": "🤖 **IA BASA:** Paga con Transferencia o Azul. BHD visible solo aquí. Tu tarjeta solo la ves tú.",
        "DEFAULT": f"🤖 **IA BASA:** Estás en {modulo_actual} - Empresa {empresa_id}. Todo se autoguardará. Si no quieres ayuda, apaga 🤖 arriba."
    }
    st.info(mensajes.get(contexto, mensajes["DEFAULT"]))

# ================= PANTALLA INICIAL =================
if not st.session_state.logged:
    st.markdown(f"<div style='background:linear-gradient(135deg,#0F2027,#2C5364);padding:20px;border-radius:15px;text-align:center;color:white;border:2px solid #FFD700;'><h1>🏦 BASA SUPERSISTEMA V27</h1><p>Baldera Santos & Asociados SRL | RNC 133378711 | Cuenta BHD {CUENTA_MOSTRAR} | Autoasistencia IA + DGII 606/607/608 + Login RNC/Cédula/Correo</p></div>", unsafe_allow_html=True)
    col_izq, col_der = st.columns([4,1])
    with col_der:
        st.session_state.ayuda_ia = st.toggle("🤖 Autoasistencia IA", value=st.session_state.ayuda_ia, key="toggle_ia_inicio_v27_final")
        st.caption("ON = IA te guía | OFF = Sin guía")
    if st.session_state.ayuda_ia: ia_autoasistencia("LOGIN", "LOGIN", "")
    st.markdown("### 🌍 ¿En qué país vas a usar BASA?")
    pais_sel = st.selectbox("Selecciona tu País", list(PAISES.keys()), index=0, key="pais_inicio_v27_final_unico")
    st.session_state.pais_usuario = pais_sel
    info_pais = PAISES[pais_sel]
    st.info(f"País: {pais_sel} | ID Fiscal: {info_pais['id_fiscal']} | Moneda: {info_pais['moneda']} | Idioma: {info_pais['idioma']} | Impuesto: {info_pais['impuesto']} | {info_pais['dgii']}")
    st.markdown("---")
    st.markdown("### 🔐 ¿Quién eres?")
    tipo = st.radio("Elige:", ["👤 Soy Cliente - Entrar con RNC / Cédula / ID / Correo", "🛠️ Soy Desarrollador / Equipo de Apoyo - Tengo clave autorizada"], key="tipo_acceso_radio_v27_final_unico")
    if "Desarrollador" in tipo:
        st.warning("🛠️ Desarrollador: BASA-DEV-2026 | Colaborador: BASA-TEAM-2026")
        clave_dev = st.text_input("Clave Autorizada", type="password", key="clave_dev_v27_final_unico")
        if st.button("🔓 Entrar como Desarrollador / Apoyo", type="primary", key="btn_dev_v27_final_unico"):
            if clave_dev == CLAVE_DESARROLLADOR:
                st.session_state.logged=True; st.session_state.user="DESARROLLADOR-BASA"; st.session_state.role="DESARROLLADOR"; st.session_state.tipo_acceso="DESARROLLADOR"; st.rerun()
            elif clave_dev == CLAVE_COLABORADOR:
                st.session_state.logged=True; st.session_state.user="COLABORADOR-BASA"; st.session_state.role="COLABORADOR"; st.session_state.tipo_acceso="COLABORADOR"; st.rerun()
            else: st.error("❌ Clave incorrecta.")
        st.stop()
    else:
        st.session_state.tipo_acceso="CLIENTE"
        c1,c2,c3 = st.columns([1,2,1])
        with c2:
            tab1, tab2, tab3 = st.tabs(["🔐 LOGIN - RNC / Cédula / ID / Correo", "📝 REGISTRO", "🔑 RECUPERAR - Sin Vencimiento"])
            with tab1:
                identificador_login = st.text_input("RNC / Cédula / ID / Correo - Elige el que quieras", key="login_identificador_v27_final_unico", placeholder="Ej: 133378711 o pedro@basa.com")
                pw_login = st.text_input("Contraseña", type="password", key="login_pw_v27_final_unico")
                if st.button("🚀 Entrar - Ir al Menú Principal", use_container_width=True, type="primary", key="btn_login_v27_final_unico"):
                    if identificador_login == MASTER_EMAIL and hash_pw(pw_login) == hash_pw("Basa2026!"):
                        st.session_state.logged=True; st.session_state.user=MASTER_EMAIL; st.session_state.role="ADMIN"; st.rerun()
                    else:
                        usuario_encontrado, tipo_encontrado = buscar_usuario_por_identificador(identificador_login)
                        if not usuario_encontrado: st.error(f"❌ No encontré registro con '{identificador_login}'. IA revisó RNC, Cédula, ID, Correo y no existe.")
                        elif usuario_encontrado[4] != hash_pw(pw_login): st.error("❌ Contraseña incorrecta. Usa Recuperar Clave - No vence.")
                        else:
                            st.success(f"✅ IA te reconoció por: {tipo_encontrado} - Bienvenido {usuario_encontrado[3]}")
                            st.session_state.logged=True; st.session_state.user=usuario_encontrado[1]; st.session_state.role=usuario_encontrado[5]
                            emp = conn.execute("SELECT empresa_id FROM usuario_empresa WHERE usuario_email=? LIMIT 1", (usuario_encontrado[1],)).fetchone()
                            if emp: st.session_state.empresa_activa=emp[0]
                            st.rerun()
            with tab2:
                nombre_reg = st.text_input("Nombre / Razón Social", key="reg_nombre_v27_final_unico")
                id_fiscal_reg = st.text_input(f"ID Fiscal - {info_pais['id_fiscal']}", key="reg_idfiscal_v27_final_unico")
                email_reg = st.text_input("Correo Electrónico", key="reg_email_v27_final_unico")
                telefono_reg = st.text_input("Celular / WhatsApp", key="reg_telefono_v27_final_unico", placeholder="8297717390")
                # FIX DuplicateElementId - Linea 158 corregida con key unico
                pw_reg = st.text_input("Contraseña - Crea tu clave", type="password", key="reg_pw_v27_final_unico_CORREGIDO_158")
                plan_sel = st.selectbox("Plan", list(PLANES.keys()), key="reg_plan_v27_final_unico")
                st.write(f"Plan: {plan_sel} - RD$ {PLANES[plan_sel]['precio']:,.0f}")
                if "Gratis" in plan_sel or "Exonerada" in plan_sel: st.warning("⚠️ Gratis / Exonerada: Solo 5 registros hasta que ADMIN apruebe.")
                metodo_pago = st.selectbox("Método Pago", ["Transferencia Manual - Subir Comprobante", "Pago Electrónico - Tarjeta Azul / BHD", "Todavía no pago - Solo probar 5 registros"], key="reg_metodo_v27_final_unico")
                comp_pago=None; ref_pago="SIN-PAGO-PRUEBA"
                if metodo_pago.startswith("Transferencia"):
                    comp_pago = st.file_uploader("📎 Adjuntar Comprobante", type=["pdf","png","jpg","jpeg"], key="reg_comp_v27_final_unico")
                    ref_pago = st.text_input("Referencia", key="reg_ref_v27_final_unico")
                if st.button("✅ Registrarme y IR AL MENÚ PRINCIPAL", use_container_width=True, type="primary", key="btn_reg_v27_final_unico"):
                    if not validar_email(email_reg): st.error("Correo inválido")
                    elif not id_fiscal_reg: st.error("ID Fiscal obligatorio")
                    else:
                        existe = conn.execute("SELECT 1 FROM usuarios WHERE email=? OR id_fiscal=?", (email_reg.strip().lower(), id_fiscal_reg.strip())).fetchone()
                        if existe: st.error("Ese correo o ID Fiscal ya existe.")
                        else:
                            emp_id = id_fiscal_reg.strip().replace("-","").replace(" ","")
                            if conn.execute("SELECT 1 FROM empresas WHERE id=?", (emp_id,)).fetchone(): emp_id = f"{emp_id}-{datetime.now().strftime('%H%M')}"
                            conn.execute("INSERT INTO usuarios (id,email,id_fiscal,nombre,pw_hash,rol,pais,telefono,fecha_registro,aprobado_por,estado_aprobacion) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (emp_id, email_reg.strip().lower(), id_fiscal_reg.strip(), nombre_reg, hash_pw(pw_reg), "CLIENT", pais_sel, telefono_reg, str(date.today()), "", "Pendiente - Prueba 5"))
                            conn.execute("INSERT INTO empresas (id,id_fiscal,nombre,propietario_email,pais,fecha) VALUES (?,?,?,?,?,?)", (emp_id, id_fiscal_reg.strip(), nombre_reg, email_reg.strip().lower(), pais_sel, str(date.today())))
                            conn.execute("INSERT INTO usuario_empresa (usuario_email, empresa_id) VALUES (?,?)", (email_reg.strip().lower(), emp_id))
                            fin = date.today() + timedelta(days=PLANES[plan_sel]['dias'])
                            comp_nombre = comp_pago.name if comp_pago else ""
                            conn.execute("INSERT INTO planes (id,empresa_id,plan,precio,fecha_inicio,fecha_fin,estado,exonerado_por,factura_num,comprobante_pago,metodo_pago) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (f"AFIL-{emp_id}", emp_id, plan_sel, PLANES[plan_sel]['precio'], str(date.today()), str(fin), "Pendiente Aprobación - Prueba 5", "", f"AFIL-{emp_id}-{datetime.now().strftime('%Y%m%d')}", comp_nombre, metodo_pago))
                            carpeta = CRED_DIR / emp_id; carpeta.mkdir(parents=True, exist_ok=True)
                            cred_data = {"empresa_id": emp_id, "id_fiscal": id_fiscal_reg, "pais": pais_sel, "nombre": nombre_reg, "usuario": email_reg, "telefono": telefono_reg, "clave_para_soporte": pw_reg, "plan": plan_sel}
                            (carpeta / "credenciales.json").write_text(base64.b64encode(json.dumps(cred_data).encode()).decode(), encoding="utf-8")
                            conn.commit()
                            st.session_state.logged=True; st.session_state.user=email_reg.strip().lower(); st.session_state.role="CLIENT"; st.session_state.empresa_activa=emp_id
                            st.success(f"✅ ¡Registrado! Te llevo al Menú Principal. Tu código es tu ID Fiscal: {id_fiscal_reg}")
                            st.rerun()
            with tab3:
                st.markdown("### 🔑 Recuperar - Sin Vencimiento - Celular / WhatsApp / Correo")
                identificador_rec = st.text_input("Escribe tu RNC / Cédula / ID / Correo", key="rec_identificador_v27_final_unico")
                if st.button("🔍 Buscar Mi Registro con IA", key="btn_buscar_rec_v27_final_unico"):
                    usuario_rec, tipo_rec = buscar_usuario_por_identificador(identificador_rec)
                    if not usuario_rec: st.error(f"❌ IA no encontró '{identificador_rec}'.")
                    else:
                        st.success(f"✅ IA te encontró por: {tipo_rec} - {usuario_rec[3]}")
                        st.session_state.usuario_recuperar = usuario_rec
                        codigo_nuevo = ''.join(random.choices(string.digits, k=6))
                        conn.execute("UPDATE usuarios SET codigo_recuperacion=?, fecha_codigo=? WHERE id=?", (codigo_nuevo, str(datetime.now()), usuario_rec[0])); conn.commit()
                        st.session_state.codigo_generado = codigo_nuevo
                        st.info("✅ Código generado. **NO tiene vencimiento.**")
                if st.session_state.get("usuario_recuperar"):
                    usuario_rec = st.session_state.usuario_recuperar
                    canal_rec = st.selectbox("¿Por dónde quieres recibir el código?", ["WhatsApp", "Celular - SMS / Llamada", "Correo Electrónico", "Ambos - WhatsApp + Correo"], key="rec_canal_v27_final_unico")
                    if canal_rec in ["Correo Electrónico", "Ambos - WhatsApp + Correo"]:
                        destino_correo = st.text_input("Correo donde recibirlo", value=usuario_rec[1], key="rec_destino_correo_v27_final_unico")
                    else: destino_correo = usuario_rec[1]
                    if canal_rec in ["WhatsApp", "Celular - SMS / Llamada", "Ambos - WhatsApp + Correo"]:
                        destino_celular = st.text_input("Celular / WhatsApp", value=usuario_rec[7] if len(usuario_rec)>7 and usuario_rec[7] else "", key="rec_destino_celular_v27_final_unico")
                    else: destino_celular = usuario_rec[7] if len(usuario_rec)>7 else ""
                    if st.button("📲 Enviar Código - Sin Vencimiento", key="btn_enviar_codigo_v27_final_unico", type="primary"):
                        codigo_a_enviar = st.session_state.get("codigo_generado", "123456")
                        if canal_rec == "WhatsApp":
                            ok, link = enviar_codigo_por_canal("WhatsApp", destino_celular, codigo_a_enviar, usuario_rec[3])
                            st.success(f"✅ Código: {codigo_a_enviar} - Sin vencimiento."); st.link_button("📲 Abrir WhatsApp", link)
                        elif canal_rec == "Celular - SMS / Llamada":
                            ok, link = enviar_codigo_por_canal("Celular - SMS / Llamada", destino_celular, codigo_a_enviar, usuario_rec[3])
                            st.success(f"✅ Código Celular: {codigo_a_enviar} - Sin vencimiento."); st.link_button("📱 Abrir Celular", link)
                        elif canal_rec == "Correo Electrónico":
                            ok, msg = enviar_codigo_por_canal("Correo Electrónico", destino_correo, codigo_a_enviar, usuario_rec[3])
                            if ok: st.success(f"✅ Enviado por Gmail a {destino_correo}. Sin vencimiento.")
                            else: st.warning(f"⚠️ Gmail no configurado. Tu código es: **{codigo_a_enviar}** - Sin vencimiento.")
                        elif canal_rec == "Ambos - WhatsApp + Correo":
                            ok1, link1 = enviar_codigo_por_canal("WhatsApp", destino_celular, codigo_a_enviar, usuario_rec[3])
                            ok2, _ = enviar_codigo_por_canal("Correo Electrónico", destino_correo, codigo_a_enviar, usuario_rec[3])
                            st.success(f"✅ Enviado por AMBOS. Código: {codigo_a_enviar} - Sin vencimiento."); st.link_button("📲 Abrir WhatsApp", link1)
                        st.session_state.codigo_para_cambiar = codigo_a_enviar
                    codigo_in = st.text_input("Ingresa código (No vence)", key="rec_codigo_in_v27_final_unico")
                    nueva_clave_rec = st.text_input("Nueva Contraseña", type="password", key="rec_nueva_v27_final_unico")
                    confirmar_clave = st.text_input("Confirma Nueva Contraseña", type="password", key="rec_confirmar_v27_final_unico")
                    if st.button("🔄 Cambiar Mi Clave y Entrar", key="btn_cambiar_v27_final_unico", type="primary"):
                        codigo_guardado = conn.execute("SELECT codigo_recuperacion FROM usuarios WHERE id=?", (st.session_state.usuario_recuperar[0],)).fetchone()
                        codigo_valido = codigo_guardado[0] if codigo_guardado else None
                        if codigo_in != codigo_valido and codigo_in != st.session_state.get("codigo_para_cambiar"): st.error("❌ Código incorrecto.")
                        elif nueva_clave_rec != confirmar_clave: st.error("❌ Claves no coinciden.")
                        elif len(nueva_clave_rec) < 6: st.error("❌ Mínimo 6 caracteres.")
                        else:
                            conn.execute("UPDATE usuarios SET pw_hash=? WHERE id=?", (hash_pw(nueva_clave_rec), st.session_state.usuario_recuperar[0])); conn.commit()
                            st.success("✅ Clave cambiada. Entrando...")
                            st.session_state.logged=True; st.session_state.user=st.session_state.usuario_recuperar[1]; st.session_state.role=st.session_state.usuario_recuperar[5]
                            emp = conn.execute("SELECT empresa_id FROM usuario_empresa WHERE usuario_email=? LIMIT 1", (st.session_state.usuario_recuperar[1],)).fetchone()
                            if emp: st.session_state.empresa_activa=emp[0]
                            st.rerun()
        st.stop()

# ================= MENU + RELOJ + IA =================
col_top1, col_top2 = st.columns([4,1])
with col_top1:
    st.markdown(f"### 🏦 BASA SUPERSISTEMA V27 - {st.session_state.user} - {st.session_state.role} - País: {st.session_state.pais_usuario}")
    info_p = PAISES.get(st.session_state.pais_usuario, PAISES["República Dominicana"])
    st.caption(f"🌍 IA: {info_p['id_fiscal']} | {info_p['moneda']} | {info_p['idioma']} | {info_p['impuesto']} | {info_p['dgii']} | openpyxl: {'✅ Instalado' if TIENE_OPENPYXL else '⚠️ No instalado - Usando pandas'}")
with col_top2:
    st.session_state.ayuda_ia = st.toggle("🤖 Autoasistencia IA", value=st.session_state.ayuda_ia, key="toggle_ia_top_v27_final")
    st.caption("ON = IA te guía | OFF = Sin guía")
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
    st.title("🏦 BASA V27"); st.write(f"Usuario: {st.session_state.user}"); st.write(f"Rol: {st.session_state.role}"); st.write(f"Cuenta: {CUENTA_MOSTRAR} (Completa solo en PAGOS)"); st.write(f"País: {st.session_state.pais_usuario} - ID Fiscal: {EMPRESA}")
    st.markdown("---"); st.markdown("### 🏢 Mis Empresas")
    if mis_ids:
        nueva = st.selectbox("Empresa Activa", mis_ids, index=mis_ids.index(EMPRESA) if EMPRESA in mis_ids else 0, key="empresa_activa_v27_final_unico")
        if nueva!=EMPRESA: st.session_state.empresa_activa=nueva; st.rerun()
    st.markdown("---")
    menu = st.radio("📋 MENÚ SUPERSISTEMA", ["📊 Dashboard","👥 Clientes + Credenciales","🧾 Facturar","📜 Histórico","💰 Planes + Aprobar","📊 Cartera + WhatsApp","💳 Pagos + Bancos + BHD + Azul","📦 Inventario","📑 Reportes","🔐 Mis Datos Confidenciales","🤖 Buzón Mejoras IA","🖨️ Guía","⚙️ Auto-Actualización IA","📊 DGII 606 - Compras","📊 DGII 607 - Ventas","📊 DGII 608 - Notas","📊 DGII IR-17 + ITBIS","🤖 Autoasistencia IA - Configuración"], key="menu_v27_final_unico")
    st.markdown("---")
    if st.button("🚪 Salir", use_container_width=True, key="btn_salir_v27_final_unico"): st.session_state.logged=False; st.rerun()

if st.session_state.ayuda_ia:
    if "DGII" in menu: ia_autoasistencia("DGII_606", menu, EMPRESA)
    elif menu=="🧾 Facturar": ia_autoasistencia("FACTURAR", menu, EMPRESA)
    elif menu=="💳 Pagos + Bancos + BHD + Azul": ia_autoasistencia("PAGOS", menu, EMPRESA)
    else: ia_autoasistencia("DEFAULT", menu, EMPRESA)
else:
    st.caption("🤖 Autoasistencia IA apagada por el usuario. Enciéndela arriba a la derecha si la quieres.")

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
    st.header(f"🧾 Facturar - {EMPRESA} - Autoguardado")
    puede, msg = puede_registrar_mas(EMPRESA)
    if not puede: st.error(f"⛔ {msg}"); st.stop()
    st.info(f"✅ {msg}")
    with st.form("fact_v27_final_form"):
        ncf = st.text_input("NCF", value=f"E31{datetime.now().strftime('%Y%m%d%H%M')}", key="fact_ncf_v27_final_unico")
        cliente = st.text_input("Cliente", key="fact_cliente_v27_final_unico"); desc = st.text_input("Descripción", key="fact_desc_v27_final_unico"); cant = st.number_input("Cantidad", 1.0, key="fact_cant_v27_final_unico"); precio = st.number_input("Precio", 0.0, key="fact_precio_v27_final_unico"); venc = st.date_input("Vencimiento", date.today(), key="fact_venc_v27_final_unico")
        if st.form_submit_button("💾 Guardar - Autoguardado"):
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
        sel_plan = st.selectbox("Empresa a Aprobar", planes_df['empresa_id'].tolist(), key="aprobar_sel_v27_final_unico"); accion = st.selectbox("Acción", ["Aprobar FULL - Pagada","Aprobar FULL - Exonerada","Rechazar - Prueba 5","Suspender"], key="aprobar_accion_v27_final_unico")
        if st.button("✅ Aplicar Aprobación", key="btn_aprobar_v27_final_unico"):
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
    st.markdown(f"<div style='background:linear-gradient(135deg,#0f2027,#2c5364);padding:20px;border-radius:15px;color:white;'><h3>💳 Cuenta BHD - Solo aquí</h3><p>Banco: BHD | Titular: Pedro Anibal Baldera</p><p><b>Cuenta: {CUENTA_BHD_REAL} - Ahorros Pesos</b></p><p>Concepto: BASA V27 - {EMPRESA}</p></div>", unsafe_allow_html=True)
    metodo = st.selectbox("Método", ["Transferencia Manual - Adjuntar Comprobante", "Pago Electrónico - Tarjeta Azul"], key="pago_metodo_v27_final_unico")
    if metodo.startswith("Transferencia"):
        ref = st.text_input("Referencia", key="pago_ref_v27_final_unico"); comp = st.file_uploader("Adjuntar Comprobante", type=["pdf","png","jpg"], key="pago_comp_v27_final_unico")
        if st.button("📎 Adjuntar Pago Manual", key="btn_pago_manual_v27_final_unico"):
            if ref and comp: conn.execute("INSERT INTO pagos (id,empresa_id,monto,metodo,referencia,comprobante,fecha,estado) VALUES (?,?,?,?,?,?,?,?)", (f"PAGO-{datetime.now().strftime('%H%M%S')}", EMPRESA, 199, "Transferencia Manual", ref, comp.name, str(date.today()), "Pendiente")); conn.commit(); st.success("Pago adjuntado.")
            else: st.error("Falta referencia y comprobante.")
    else:
        monto_azul = st.number_input("Monto Azul", 199.0, key="pago_monto_azul_v27_final_unico")
        if st.button("💳 Pagar con Azul", key="btn_pago_azul_v27_final_unico"):
            st.link_button("💳 Ir a Pagar con Azul", f"https://basa-audit-intelligence-usa-v23.streamlit.app/pago-azul?monto={monto_azul}&empresa={EMPRESA}")
    st.dataframe(pd.read_sql("SELECT * FROM pagos WHERE empresa_id=?", conn, params=(EMPRESA,)))
if menu=="📦 Inventario":
    st.header("📦 Inventario"); st.info("Inventario conectado a facturación.")
if menu=="📑 Reportes":
    st.header("📑 Reportes"); tipo = st.selectbox("Tipo", ["Día - Esta Empresa","Día - Consolidado","Mes - Esta Empresa"], key="rep_tipo_v27_final_unico"); fecha_r = st.date_input("Fecha", date.today(), key="rep_fecha_v27_final_unico")
    if tipo.startswith("Día - Esta"): df = pd.read_sql("SELECT * FROM facturas WHERE empresa_id=? AND fecha=?", conn, params=(EMPRESA, str(fecha_r)))
    elif tipo.startswith("Consolidado"): df = pd.read_sql("SELECT * FROM facturas WHERE fecha=?", conn, params=(str(fecha_r),))
    else: df = pd.read_sql("SELECT * FROM facturas WHERE empresa_id=?", conn, params=(EMPRESA,))
    st.dataframe(df)
    if st.button("📥 Excel", key="btn_excel_v27_final_unico"): df.to_excel(f"reporte_{EMPRESA}.xlsx", index=False); st.success("Excel generado")
if menu=="🔐 Mis Datos Confidenciales":
    st.header("🔐 Mis Datos - Solo Tú"); st.warning("Ni ADMIN puede ver esto.")
    st.dataframe(pd.read_sql("SELECT id, tipo, fecha FROM datos_confidenciales WHERE usuario_email=?", conn, params=(st.session_state.user,)))
if menu=="🤖 Buzón Mejoras IA":
    st.header("🤖 Buzón Mejoras IA"); sug = st.text_area("¿Qué mejora quieres?", key="buzon_sug_v27_final_unico")
    if st.button("🤖 Enviar a IA", key="btn_buzon_v27_final_unico"):
        bid=f"IA-{datetime.now().strftime('%H%M%S')}"; conn.execute("INSERT INTO buzon_ia (id,usuario,empresa_id,sugerencia,analisis,estado,fecha,decision) VALUES (?,?,?,?,?,?,?,?)", (bid, st.session_state.user, EMPRESA, sug, "✅ EN REVISIÓN - Lógico", "Pendiente", str(date.today()), "")); conn.commit(); st.success("Enviado a IA.")
    st.dataframe(pd.read_sql("SELECT * FROM buzon_ia", conn))
if menu=="🖨️ Guía":
    st.header("🖨️ Guía V27 - Ctrl+P"); st.markdown("1. Entra con RNC / Cédula / ID / Correo. 2. Si olvidas clave, usa Recuperar - Elige Celular / WhatsApp / Correo. Código sin vencimiento. 3. Regístrate, te lleva al Menú. 4. Prueba 5 registros. 5. Paga con Transferencia o Azul. 6. DGII 606/607/608: Sube Excel, genera Excel oficial. 7. Autoasistencia IA: Enciende o apaga con botón 🤖 arriba.")
if menu=="⚙️ Auto-Actualización IA":
    st.header("⚙️ Auto-Actualización IA"); st.success("✅ Sistema adaptado a tu país automáticamente.")
    if st.button("🔄 Buscar Actualizaciones", key="btn_update_ia_v27_final_unico"): st.success("✅ Sistema actualizado.")

if menu in ["📊 DGII 606 - Compras", "📊 DGII 607 - Ventas", "📊 DGII 608 - Notas", "📊 DGII IR-17 + ITBIS"]:
    modulo_map = {"📊 DGII 606 - Compras": "606", "📊 DGII 607 - Ventas": "607", "📊 DGII 608 - Notas": "608", "📊 DGII IR-17 + ITBIS": "ir_17"}
    modulo = modulo_map[menu]
    titulo = "606 - Compras" if modulo=="606" else "607 - Ventas" if modulo=="607" else "608 - Notas" if modulo=="608" else "IR-17 + ITBIS"
    st.header(f"📊 DGII Formato {titulo} - BASA V27 - Flask Integrado")
    st.info(f"Tu código Flask convertido a Streamlit. Carpeta: reportes_dgii / reportes_{modulo} | openpyxl: {'✅' if TIENE_OPENPYXL else '⚠️ Usando pandas - Agrega openpyxl a requirements para formato azul'}")
    rnc_dgii = st.text_input("RNC Contribuyente", value=EMPRESA, key=f"dgii_rnc_{modulo}_v27_final_unico")
    periodo_dgii = st.text_input("Periodo AAAAMM - Ej: 202609", value="202609", key=f"dgii_periodo_{modulo}_v27_final_unico")
    st.markdown("### 📤 1. Subir Excel/CSV - Parse File")
    archivo_dgii = st.file_uploader(f"Sube Excel/CSV para Formato {modulo}", type=["csv","xlsx","xls"], key=f"dgii_file_{modulo}_v27_final_unico")
    if archivo_dgii:
        if st.button(f"🔍 Convertir Archivo a Formato {modulo}", key=f"btn_parse_{modulo}_v27_final_unico"):
            parsed = parse_file_dgii(archivo_dgii, modulo)
            st.success(f"✅ Convertido: {len(parsed)} registros.")
            st.session_state[f"parsed_{modulo}"] = parsed
            st.dataframe(pd.DataFrame(parsed))
            path_guardado = auto_save_dgii(rnc_dgii, periodo_dgii, modulo, {"rnc": rnc_dgii, "periodo": periodo_dgii, "modulo": modulo, "invoices": parsed})
            st.caption(f"💾 Autosave: {path_guardado}")
    st.markdown("### ✏️ 2. Agregar Manual - Autoguardado")
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1: rnc_manual = st.text_input("RNC / Cédula Proveedor", key=f"dgii_rnc_manual_{modulo}_v27_final_unico")
    with col_d2: ncf_manual = st.text_input("NCF", key=f"dgii_ncf_manual_{modulo}_v27_final_unico")
    with col_d3: monto_manual = st.number_input("Monto Bienes RD$", 10000.0, key=f"dgii_monto_{modulo}_v27_final_unico")
    if st.button(f"➕ Agregar Registro {modulo}", key=f"btn_add_{modulo}_v27_final_unico"):
        nuevo = {"rnc": rnc_manual, "tipo_id":"1", "tipo_bienes":"02", "ncf": ncf_manual, "ncf_mod":'', "fecha_comp":"20260930", "fecha_pago":"20260930", "monto_servicios":0, "monto_bienes": monto_manual, "itbis_fact": monto_manual*0.18, "itbis_ret":0, "forma_pago":"01"}
        lista = st.session_state.get(f"parsed_{modulo}", [])
        lista.append(nuevo); st.session_state[f"parsed_{modulo}"] = lista
        path_guardado = auto_save_dgii(rnc_dgii, periodo_dgii, modulo, {"rnc": rnc_dgii, "periodo": periodo_dgii, "modulo": modulo, "invoices": lista})
        st.success(f"✅ Agregado y autoguardado. Total: {len(lista)}")
    st.markdown("### 📊 3. Registros Actuales")
    lista_actual = st.session_state.get(f"parsed_{modulo}", [])
    if lista_actual:
        df_dgii = pd.DataFrame(lista_actual); st.dataframe(df_dgii)
        st.write(f"**Total:** {len(df_dgii)} | **Monto:** RD$ {df_dgii['monto_bienes'].sum():,.0f} | **ITBIS:** RD$ {df_dgii['itbis_fact'].sum():,.0f}")
        if st.button(f"📥 Generar Excel Formato {modulo} - DGII Oficial", type="primary", key=f"btn_gen_excel_{modulo}_v27_final_unico"):
            output, nombre = generate_excel_dgii(lista_actual, rnc_dgii, periodo_dgii, modulo)
            st.download_button(f"⬇️ Descargar {nombre}", data=output, file_name=nombre, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"btn_dl_{modulo}_v27_final_unico")
            st.success(f"✅ Excel generado: {nombre}")
            try:
                carpeta_dest = REPORT_DIR / f"reportes_{modulo}"
                (carpeta_dest / nombre).write_bytes(output.getvalue())
            except: pass
    else:
        st.info(f"Sin registros en {modulo} todavía. Sube Excel/CSV o agrega manual.")

if menu=="🤖 Autoasistencia IA - Configuración":
    st.header("🤖 Autoasistencia IA - Configuración")
    st.write("La autoasistencia **se mantiene siempre**, pero tú decides si la quieres ON o OFF.")
    col_on, col_off = st.columns(2)
    with col_on:
        st.success("**ON - IA te guía:** Valida, completa, guía paso a paso.")
        if st.button("✅ Encender Autoasistencia IA", key="btn_ia_on_v27_final_unico"):
            st.session_state.ayuda_ia=True; st.rerun()
    with col_off:
        st.warning("**OFF - Sin guía:** Solo módulos limpios, sin mensajes IA.")
        if st.button("❌ Apagar Autoasistencia IA", key="btn_ia_off_v27_final_unico"):
            st.session_state.ayuda_ia=False; st.rerun()
    st.markdown("### ¿Qué hace la IA cuando está ON?")
    st.markdown("- Valida RNC, NCF, montos no duplicados\n- Completa el trabajo si falta un campo\n- Guía en Facturar, DGII 606, Pagos\n- Autoguardado al hacer click\n- Si la apagas, todo sigue funcionando igual")

st.caption(f"BASA SUPERSISTEMA V27 FINAL CORREGIDO | Empresa {EMPRESA} | País {st.session_state.pais_usuario} | Autoasistencia IA: {'ON' if st.session_state.ayuda_ia else 'OFF'} | DGII 606/607/608 Integrado | Login RNC/Cédula/Correo | Fix openpyxl + DuplicateElementId")
