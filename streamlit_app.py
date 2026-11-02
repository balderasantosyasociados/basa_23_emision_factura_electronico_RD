# BASA v3.0 FINAL FINAL - 1 SOLO 1 - RNC 133378711 - CLIENT DB
import streamlit as st
import json, os, hashlib, datetime, sqlite3, uuid
from pathlib import Path
import pandas as pd

st.set_page_config(page_title="BASA v3.0 FINAL - 1 SOLO 1", layout="wide", page_icon="💰")

BASE_DIR = Path("data")
CASOS_DIR = BASE_DIR / "casos"
BASE_DIR.mkdir(exist_ok=True)
CASOS_DIR.mkdir(exist_ok=True)

MASTER_USER = {"email": "Licpedrobaldera@gmail.com", "password_hash": hashlib.sha256("Basa2026!".encode()).hexdigest(), "rnc": "133378711"}

def get_db_path(client_id):
    client_folder = CASOS_DIR / client_id
    client_folder.mkdir(exist_ok=True, parents=True)
    return client_folder / f"basa_{client_id}.db"

def init_client_db(client_id):
    db_path = get_db_path(client_id)
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS facturas (id INTEGER PRIMARY KEY, ncf TEXT UNIQUE, tipo TEXT, cliente TEXT, monto REAL, fecha TEXT, estado TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS documentos (id INTEGER PRIMARY KEY, nombre TEXT, tipo TEXT, fecha TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS clientes_info (id TEXT PRIMARY KEY, nombre TEXT, rnc TEXT, email TEXT)")
    conn.commit()
    conn.close()
    return db_path

def get_next_ncf(client_id, tipo="E32"):
    db_path = get_db_path(client_id)
    if not db_path.exists():
        init_client_db(client_id)
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    try:
        c.execute("SELECT ncf FROM facturas WHERE tipo=? ORDER BY id DESC LIMIT 1", (tipo,))
        row = c.fetchone()
        if row:
            last_num = int(row[0][3:])
            next_num = last_num + 1
        else:
            next_num = 1
    except:
        next_num = 1
    conn.close()
    return f"{tipo}{next_num:011d}"

# LOGIN
if "logged" not in st.session_state:
    st.session_state.logged = False

st.markdown("""
<div style='background: linear-gradient(90deg, #FFD700, #B8860B); padding:20px; border-radius:10px; text-align:center;'>
<h1 style='color:black; margin:0;'>BASA v3.0 - 1 SOLO 1 - FINAL - RNC 133378711</h1>
<p style='color:black; margin:0;'>CLIENT DB - SQLite por Cliente - Anti-duplicado NCF</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.logged:
    st.markdown("### Login - 1 SOLO 1")
    email = st.text_input("Correo")
    password = st.text_input("Contraseña", type="password")
    if st.button("Entrar - 1 SOLO 1"):
        phash = hashlib.sha256(password.encode()).hexdigest()
        if email == MASTER_USER["email"] and phash == MASTER_USER["password_hash"]:
            st.session_state.logged = True
            st.session_state.user = email
            st.session_state.role = "ADMIN"
            st.rerun()
        else:
            # Buscar en clientes
            found = False
            for client_folder in CASOS_DIR.iterdir():
                if client_folder.is_dir():
                    info_file = client_folder / "info.json"
                    if info_file.exists():
                        try:
                            info = json.loads(info_file.read_text())
                            if info.get("email") == email and info.get("password_hash") == phash:
                                st.session_state.logged = True
                                st.session_state.user = email
                                st.session_state.role = "CLIENT"
                                st.session_state.client_id = info.get("id")
                                found = True
                                st.rerun()
                        except:
                            pass
            if not found:
                st.error("Credenciales incorrectas")
    st.stop()

# SIDEBAR
with st.sidebar:
    st.write(f"Usuario: {st.session_state.user}")
    st.write(f"Rol: {st.session_state.role}")
    modulos = ["FINAL - CLIENTES MANAGER - Crear Cliente DB", "FINAL - NCF E32/E31 - Facturar", "FINAL - CLIENTE PORTAL - Ver DB Cliente"]
    modulo = st.selectbox("MODULOS - 1 SOLO 1", modulos)
    st.markdown("---")
    client_id_input = st.text_input("ID Cliente DB", value="CLI-001")
    if st.button("Crear DB Cliente"):
        dbp = init_client_db(client_id_input)
        st.success(f"DB Creada: {dbp}")
    if st.button("Salir"):
        st.session_state.logged = False
        st.rerun()

# MODULOS
if modulo == "FINAL - CLIENTES MANAGER - Crear Cliente DB":
    st.header("FINAL - CLIENTES MANAGER - Crear Cliente DB - $199/mes")
    col1, col2 = st.columns(2)
    with col1:
        new_id = st.text_input("ID Nuevo", value=f"CLI-{str(uuid.uuid4())[:4].upper()}")
        nombre = st.text_input("Nombre", value="Ferreteria Ramirez SRL")
        rnc = st.text_input("RNC", value="130000003")
    with col2:
        correo = st.text_input("Correo", value="ramirez@ferreteria.com")
        pwd = st.text_input("Password", value="Cliente2026!")
    
    if st.button("CREAR CLIENTE FINAL - 1 SOLO 1 - $199/mes"):
        db_path = init_client_db(new_id)
        info = {"id": new_id, "nombre": nombre, "rnc": rnc, "email": correo, "password_hash": hashlib.sha256(pwd.encode()).hexdigest(), "precio": 199}
        (CASOS_DIR / new_id / "info.json").write_text(json.dumps(info, indent=2))
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO clientes_info (id, nombre, rnc, email) VALUES (?,?,?,?)", (new_id, nombre, rnc, correo))
        conn.commit()
        conn.close()
        st.success(f"CREADO: {new_id} - {nombre} - DB: {db_path} - Login: {correo} / {pwd} - $199/mes")

    st.markdown("---")
    st.write("Clientes existentes:")
    clientes = []
    for cf in CASOS_DIR.iterdir():
        if cf.is_dir():
            jf = cf / "info.json"
            if jf.exists():
                try:
                    clientes.append(json.loads(jf.read_text()))
                except:
                    pass
    if clientes:
        st.dataframe(pd.DataFrame(clientes))
    else:
        st.info("No hay clientes aún - Crea CLI-002")

elif modulo == "FINAL - NCF E32/E31 - Facturar":
    st.header(f"FINAL - NCF E32/E31 - Facturar - Cliente: {client_id_input}")
    db_path = get_db_path(client_id_input)
    if not db_path.exists():
        st.warning(f"DB no existe para {client_id_input} - Crea primero en sidebar")
        st.stop()
    
    next_ncf = get_next_ncf(client_id_input, "E32")
    st.info(f"Siguiente: {next_ncf} - DB: {client_id_input}")

    last_dgii = st.text_input("Ultimo DGII E32 (para evitar duplicado) - Ej: E320000000049")
    if st.button("Set Manual E32"):
        if last_dgii.startswith("E32"):
            try:
                last_num = int(last_dgii[3:])
                next_manual = f"E32{last_num+1:011d}"
                st.success(f"Siguiente: {next_manual} - Anti-duplicado OK")
                next_ncf = next_manual
            except:
                st.error("Formato E32 inválido")
    
    st.markdown("---")
    tipo = st.selectbox("Tipo NCF", ["E32", "E31"])
    cliente_fac = st.text_input("Cliente", value="Ferreteria Ramirez SRL")
    monto = st.number_input("Monto", value=99.0, step=1.0)

    if st.button(f"FACTURAR {tipo} - Guardar en DB {client_id_input} - 1 SOLO 1"):
        current_next = get_next_ncf(client_id_input, tipo)
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            c.execute("INSERT INTO facturas (ncf, tipo, cliente, monto, fecha, estado) VALUES (?,?,?,?,?,?)", (current_next, tipo, cliente_fac, monto, fecha, "VIGENTE"))
            conn.commit()
            st.success(f"Factura {current_next} - Guardada en DB {client_id_input} - {db_path} - RNC133378711 - FINAL")
            st.download_button(f"Descargar {current_next}", f"Factura {current_next}\nCliente: {cliente_fac}\nMonto: {monto}\nRNC: 133378711\nFecha: {fecha}", file_name=f"{current_next}.txt")
        except sqlite3.IntegrityError:
            st.error(f"NCF {current_next} ya existe - Anti-duplicado activo")
        conn.close()

elif modulo == "FINAL - CLIENTE PORTAL - Ver DB Cliente":
    st.header(f"FINAL - CLIENTE PORTAL - Ver DB Cliente: {client_id_input}")
    db_path = get_db_path(client_id_input)
    if not db_path.exists():
        st.warning(f"DB no existe para {client_id_input}")
        st.stop()
    conn = sqlite3.connect(str(db_path))
    try:
        df = pd.read_sql_query("SELECT * FROM facturas ORDER BY id DESC", conn)
        st.write(f"Facturas en su DB: {len(df)}")
        st.dataframe(df)
    except:
        st.info("Sin facturas aún")
    conn.close()
