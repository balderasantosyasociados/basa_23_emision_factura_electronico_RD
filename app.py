
import streamlit as st
import os

from dgii_client import DGIIClient, DGIIError

def modulo_integracion_dgii():

    st.subheader("Conexión DGII - BASA e-CF PRO")

    ambiente = st.selectbox(
        "Ambiente de facturación",
        [
            "precertificacion",
            "certificacion",
            "produccion"
        ]
    )

    st.warning(
        "Producción tiene validez fiscal. "
        "Utiliza únicamente un RNC autorizado "
        "y secuencias asignadas."
    )

    cert_path = st.text_input(
        "Ruta del certificado digital P12"
    )

    clave = st.text_input(
        "Contraseña del certificado",
        type="password"
    )

    if st.button("Verificar conexión DGII"):
        try:
            client = DGIIClient(ambiente)

            semilla = client.obtener_semilla()

            st.session_state["dgii_ambiente"] = ambiente
            st.session_state["dgii_semilla"] = semilla

            st.success(
                "Conexión DGII establecida. "
                "Semilla recibida correctamente."
            )

        except DGIIError as e:
            st.error(str(e))

    st.caption(
        "La semilla recibida todavía debe firmarse "
        "con el certificado digital para autenticarse."
    )
