import streamlit as st
import json
import os
import hashlib
import datetime
import sqlite3
import uuid
import base64
import random
import string
import shutil
from pathlib import Path
import pandas as pd

st.set_page_config(page_title="BASA e-CF PRO v71 PROFESIONAL - BASA_eCF_PRO_v71_PROFESIONAL", layout="wide", page_icon="💰")

BASE_DIR_NEW = Path("BASA_eCF_PRO_v71_PROFESIONAL")
CLIENTES_DB_NEW = BASE_DIR_NEW / "clientes_db"
BASE_DIR_NEW.mkdir(exist_ok=True)
CLIENTES_DB_NEW.mkdir(exist_ok=True)

BACKUP_DIR = BASE_DIR_NEW / "backup_migracion_2026"
BACKUP_DIR.mkdir(exist_ok=True)

CASOS_DIR = CLIENTES_DB_NEW
BASES_VIEJAS = ["BASA_eCF_PRO_v7_0_AFILIACION", "BASA_eCF_PRO_v6_3_ENVIO_DGII_CERT", "BASA_eCF_PRO_v6_DGII_CERTIFICADO", "BASA_eCF_PRO_v6_DGII", "BASA_eCF_PRO_v5", "clientes_db"]

MASTER_USER = {"email": "Licpedrobaldera@gmail.com", "password_hash": hashlib.sha256("Basa2026!".encode()).hexdigest(), "rnc": "133378711"}
CRED = {"nombre": "Lic. Pedro A. Baldera R.", "empresa": "Baldera Santos & Asociados SRL", "rnc": "133378711", "telefono": "829-771-7390", "whatsapp": "829-771-7390", "email": "licpedrobaldera@gmail.com", "direccion": "Calle Orlando Martinez No.49, Brisas del Este, Santo Domingo Este"}

DGII_PORTAL = "https://fg.dgii.gov.do/ecf/PortalFG/login?redirectUrl=%2Fecf%2Fportalfg"
DGII_HOME = "https://fg.dgii.gov.do/ecf/PortalFG/home"

def migrar_sin_perdidas():
    log_mig = []
    for base_vieja in BASES_VIEJAS:
        p_vieja = Path(base_vieja)
        if p_vieja.exists():
            if (p_vieja / "clientes_db").exists():
                origen = p_vieja / "clientes_db"
            else:
                origen = p_vieja
            for cli_dir in origen.iterdir():
                if cli_dir.is_dir() and cli_dir.name.startswith("CLI-"):
                    destino = CASOS_DIR / cli_dir.name
                    if not destino.exists():
                        shutil.copytree(str(cli_dir), str(destino), dirs_exist_ok=True)
                        backup_dest = BACKUP_DIR / cli_dir.name
                        if not backup_dest.exists():
                            shutil.copytree(str(cli_dir), str(backup_dest), dirs_exist_ok=True)
                        log_mig.append(f"MIGRADO {cli_dir.name} de {base_vieja} a v71 PROFESIONAL - Full sin perdidas")
                    else:
                        for archivo in ["info.json", "logo.png"]:
                            src_file = cli_dir / archivo
                            dst_file = destino / archivo
                            if src_file.exists() and not dst_file.exists():
                                shutil.copy2(str(src_file), str(dst_file))
                                log_mig.append(f"SALVAGUARDADO {archivo} de {cli_dir.name}")
                        src_cert_dir = cli_dir / "certificados"
                        dst_cert_dir = destino / "certificados"
                        dst_cert_dir.mkdir(exist_ok=True)
                        if src_cert_dir.exists():
                            for cert_file in src_cert_dir.iterdir():
                                if cert_file.is_file() and cert_file.name not in [f.name for f in dst_cert_dir.iterdir()]:
                                    shutil.copy2(str(cert_file), str(dst_cert_dir / cert_file.name))
                                    log_mig.append(f"SALVAGUARDADO cert {cert_file.name}")
    return log_mig

def get_db_path(cid):
    cf = CASOS_DIR / cid
    cf.mkdir(exist_ok=True, parents=True)
    (cf / "certificados").mkdir(exist_ok=True, parents=True)
    return cf / f"BASA_{cid}_eCF.db"

def init_db_v71(cid):
    dbp = get_db_path(cid)
    conn = sqlite3.connect(str(dbp))
    c = conn.cursor()
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
    conn.commit()
    conn.close()
    return dbp

def get_next_ncf(cid, tipo="E31"):
    dbp = get_db_path(cid)
    if not dbp.exists(): 
        init_db_v71(cid)
    conn = sqlite3.connect(str(dbp))
    c = conn.cursor()
    try:
        c.execute("SELECT ncf FROM facturas WHERE tipo=? ORDER BY id DESC LIMIT 1", (tipo,))
        row = c.fetchone()
        nxt = int(row[0][3:]) + 1 if row and len(row[0]) > 3 and row[0][3:].isdigit() else 1
    except: 
        nxt = 1
    conn.close()
    return f"{tipo}{nxt:010d}"

def add_historico(cid, accion, ncf, detalle, usuario):
    dbp = get_db_path(cid)
    conn = sqlite3.connect(str(dbp))
    c = conn.cursor()
    c.execute("INSERT INTO historico (cliente_id, accion, ncf, detalle, usuario, fecha) VALUES (?,?,?,?,?,?)",
              (cid, accion, ncf, detalle, usuario, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")))
    conn.commit()
    conn.close()

def save_logo(cid, uploaded_file):
    cf = CASOS_DIR / cid
    logo_path = cf / "logo.png"
    with open(logo_path, "wb") as f: 
        f.write(uploaded_file.getbuffer())
    return str(logo_path)

def save_cert(cid, uploaded_file, proveedor):
    cf = CASOS_DIR / cid / "certificados"
    cert_name = f"cert_{proveedor}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.p12"
    cert_path = cf / cert_name
    with open(cert_path, "wb") as f: 
        f.write(uploaded_file.getbuffer())
    return str(cert_path)

def save_comprobante_bhd(cid, uploaded_file):
    cf = CASOS_DIR / cid
    comp_name = f"comprobante_pago_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    comp_path = cf / comp_name
    with open(comp_path, "wb") as f: 
        f.write(uploaded_file.getbuffer())
    return str(comp_path)

def autoguardar_producto(cid, descripcion, precio, unidad="CAJ"):
    dbp = get_db_path(cid)
    conn = sqlite3.connect(str(dbp))
    c = conn.cursor()
    c.execute("SELECT id FROM productos_servicios WHERE cliente_id=? AND descripcion=?", (cid, descripcion))
    row = c.fetchone()
    
    ahora = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    if row:
        c.execute("UPDATE productos_servicios SET veces_usado=veces_usado+1, ultimo_uso=?, precio=? WHERE id=?", 
                  (ahora, precio, row[0]))
    else:
        pid = f"PROD-{str(uuid.uuid4())[:6].upper()}"
        c.execute("INSERT INTO productos_servicios (id, cliente_id, descripcion, precio, unidad, veces_usado, ultimo_uso) VALUES (?,?,?,?,?,?,?)", 
                  (pid, cid, descripcion, precio, unidad, 1, ahora))
    conn.commit()
    conn.close()
