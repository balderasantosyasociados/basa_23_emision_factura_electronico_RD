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
import requests

# 💰 1. Configuración de Entorno y Directorios Locales
BASE_DIR_NEW = Path("BASA_eCF_PRO_v71_PROFESIONAL")
CLIENTES_DB_NEW = BASE_DIR_NEW / "clientes_db"
BACKUP_DIR = BASE_DIR_NEW / "backup_migracion_2026"

BASE_DIR_NEW.mkdir(exist_ok=True)
CLIENTES_DB_NEW.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

CONFIG_PATH = BASE_DIR_NEW / "basa_config.json"
CLIENTS_JSON_PATH = BASE_DIR_NEW / "basa_clientes.json"

GITHUB_REPO = "balderasantosyasociados/BASA_V7"

# Carga inicial de datos de configuración por defecto
DEFAULT_CRED = {
    "nombre": "Lic. Pedro A. Baldera R.",
    "empresa": "Baldera Santos & Asociados SRL",
    "rnc": "133378711",
    "telefono": "829-771-7390",
    "whatsapp": "829-771-7390",
    "email": "licpedrobaldera@gmail.com",
    "direccion": "Calle Orlando Martinez No.49, Brisas del Este, Santo Domingo Este",
    "logo_b64": ""
}

if not CONFIG_PATH.exists():
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CRED, f, indent=4, ensure_ascii=False)

if not CLIENTS_JSON_PATH.exists():
    with open(CLIENTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=4, ensure_ascii=False)

def cargar_config_empresa():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_config_empresa(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def cargar_clientes():
    with open(CLIENTS_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_clientes(data):
    with open(CLIENTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# 🐙 2. Conectividad API Automatizada a GitHub
def crear_github_issue(titulo, descripcion, token_github):
    url = f"https://github.com{GITHUB_REPO}/issues"
    headers = {
        "Authorization": f"token {token_github}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": titulo,
        "body": descripcion,
        "labels": ["audit-intelligence", "automated-sync", "v71-professional"]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            return True, response.json().get("html_url")
        else:
            return False, response.json().get("message", "Error de credenciales o permisos.")
    except Exception as e:
        return False, str(e)

# 🏛️ 3. Inicialización de la Interfaz Estética en Streamlit
def render_basa_ecf_professional():
    empresa_data = cargar_config_empresa()
    clientes_data = cargar_clientes()

    st.markdown("""
        <style>
        .main-header { font-size: 26px; font-weight: 700; color: #ffffff; text-align: center; margin-bottom: 2px; }
        .sub-header { font-size: 13px; color: #8a99ad; text-align: center; margin-bottom: 20px; }
        .card-container { background-color: #1e2630; padding: 18px; border-radius: 8px; border: 1px solid #2d3748; margin-bottom: 15px; }
        .footer-text { font-size: 11px; color: #5c6b73; text-align: center; margin-top: 25px; }
        </style>
    """, unsafe_allow_html=True)

    # Mostrar logotipo corporativo cargado dinámicamente si existe
    if empresa_data.get("logo_b64"):
        try:
            st.image(base64.b64decode(empresa_data["logo_b64"]), width=120)
        except Exception:
            pass

    st.markdown(f'<div class="main-header">🏛️ {empresa_data["empresa"]}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ecosistema e-CF PRO v71 - Integración Global Forense</div>', unsafe_allow_html=True)

    # 📊 Panel Operativo Superior
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    col_logo, col_status = st.columns([3, 1])
    with col_logo:
        st.markdown("### 🌐 Audit Intelligence USA Engine")
        st.caption(f"Sincronizado con repositorio activo: `{GITHUB_REPO}`")
    with col_status:
        st.success("● ONLINE")
    st.markdown('</div>', unsafe_allow_html=True)

    # 📑 Distribución Operativa por Pestañas
    tab1, tab2, tab3, tab4 = st.tabs([
        "💳 Cuenta & Banca (RD)", 
        "👥 Clientes e Historial", 
        "🔧 Personalizar Empresa", 
        "🚀 Entorno GitHub"
    ])

    with tab1:
        st.write("### 🏦 Canales Seguros BHD")
        st.info("Utilice el bloque interactivo inferior para copiar su cuenta bancaria con un solo clic.")
        cuenta_bhd = "08694150021"
        st.code(cuenta_bhd, language="text")
        st.caption(f"Titular: {empresa_data['nombre']} | RNC: {empresa_data['rnc']}")
        
        st.markdown(
            '<a href="https://bhd.com.do" target="_blank">'
            '<button style="width:100%; padding:10px; background-color:#004B87; color:white; '
            'border:none; border-radius:5px; font-weight:bold; cursor:pointer; margin-top:10px;">'
            'Acceder a Internet Banking BHD'
            '</button></a>', 
            unsafe_allow_html=True
        )

    with tab2:
        st.write("### 📂 Gestión de Clientes y Proyectos Históricos")
        subtab_crear, subtab_ver = st.tabs(["🆕 Registrar / Editar Cliente", "📊 Historial Transaccional"])
        
        with subtab_crear:
            with st.form("form_cliente"):
                c_id = st.text_input("ID Cliente (Ej: CLI-001)", value=f"CLI-{uuid.uuid4().hex[:6].upper()}")
                c_nombre = st.text_input("Nombre de la Empresa o Cliente")
                c_rnc = st.text_input("RNC / Cédula")
                c_direccion = st.text_area("Dirección Completa de Facturación")
                
                submit_cli = st.form_submit_button("💾 Guardar Cliente")
                if submit_cli:
                    if c_nombre and c_id:
                        if c_id not in clientes_data:
                            clientes_data[c_id] = {"nombre": c_nombre, "rnc": c_rnc, "direccion": c_direccion, "historico": []}
                        else:
                            clientes_data[c_id]["nombre"] = c_nombre
                            clientes_data[c_id]["rnc"] = c_rnc
                            clientes_data[c_id]["direccion"] = c_direccion
                        guardar_clientes(clientes_data)
                        st.success(f"Cliente {c_nombre} resguardado con éxito.")
                        st.rerun()
                    else:
                        st.error("El campo ID y Nombre son obligatorios.")

        with subtab_ver:
            if not clientes_data:
                st.info("No hay clientes registrados en el maestro local.")
            else:
                cliente_sel = st.selectbox("Seleccione un Cliente para inspección forense:", list(clientes_data.keys()), format_func=lambda x: f"{x} - {clientes_data[x]['nombre']}")
                
                cli_info = clientes_data[cliente_sel]
                st.markdown(f"**🏢 Razón Social:** {cli_info['nombre']} | **🆔 RNC:** {cli_info['rnc']}")
                st.markdown(f"**📍 Dirección:** {cli_info['direccion']}")
                
                st.markdown("---")
                st.write("#### 📜 Historial Forense y de Proyectos")
                
                with st.expander("➕ Registrar Evento o Auditoría en Historial"):
                    with st.form("form_evento"):
                        evt_tipo = st.selectbox("Tipo de Evento", ["Envío e-CF", "Auditoría Forense", "Certificación Fiscal", "Sincronización"])
                        evt_desc = st.text_area("Descripción de los hallazgos o estado")
                        submit_evt = st.form_submit_button("📝 Anexar al Histórico")
                        if submit_evt:
                            nuevo_evento = {
                                "id_log": str(uuid.uuid4())[:8].upper(),
                                "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "tipo": evt_tipo,
                                "descripcion": evt_desc
                            }
                            clientes_data[cliente_sel]["historico"].append(nuevo_evento)
                            guardar_clientes(clientes_data)
                            st.success("Registro forense indexado correctamente.")
                            st.rerun()

                if cli_info["historico"]:
                    df_hist = pd.DataFrame(cli_info["historico"])
                    st.dataframe(df_hist, use_container_width=True)
                else:
                    st.warning("Este cliente no cuenta con trazas históricas registradas.")

    with tab3:
        st.write("### 🔧 Datos Generales de la Empresa")
        with st.form("form_empresa"):
            emp_nombre_t = st.text_input("Nombre de Fantasía o Auditor", value=empresa_data.get("nombre", ""))
            emp_razon_t = st.text_input("Razón Social Corporativa", value=empresa_data.get("empresa", ""))
            emp_rnc_t = st.text_input("RNC Institucional", value=empresa_data.get("rnc", ""))
            emp_tel_t = st.text_input("Teléfono Comercial", value=empresa_data.get("telefono", ""))
            emp_dir_t = st.text_area("Dirección General", value=empresa_data.get("direccion", ""))
            
            uploaded_file = st.file_uploader("Subir Logotipo Corporativo (PNG/JPG)", type=["png", "jpg", "jpeg"])
            
            submit_emp = st.form_submit_button("⚡ Actualizar Parámetros de Interfaz")
            if submit_emp:
                empresa_data["nombre"] = emp_nombre_t
                empresa_data["empresa"] = emp_razon_t
                empresa_data["rnc"] = emp_rnc_t
                empresa_data["telefono"] = emp_tel_t
                empresa_data["direccion"] = emp_dir_t
                
