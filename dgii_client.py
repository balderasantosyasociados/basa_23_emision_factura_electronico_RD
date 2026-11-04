
import os
import requests
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


class DGIIError(Exception):
    pass


AMBIENTES = {
    "precertificacion": "testecf",
    "certificacion": "certecf",
    "produccion": "ecf",
}


class DGIIClient:

    def __init__(
        self,
        ambiente: str,
        timeout: int = 30
    ):
        if ambiente not in AMBIENTES:
            raise ValueError("Ambiente DGII no válido")

        self.ambiente = AMBIENTES[ambiente]
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json"
        })

        self.base = (
            f"https://ecf.dgii.gov.do/"
            f"{self.ambiente}"
        )

        self.token = None
        self.expiracion = None

    def _request(self, method, url, **kwargs):
        try:
            response = self.session.request(
                method,
                url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response

        except requests.RequestException as exc:
            raise DGIIError(
                f"Error de comunicación DGII: {exc}"
            ) from exc

    def obtener_semilla(self) -> bytes:
        url = (
            f"{self.base}/autenticacion/"
            "api/autenticacion/semilla"
        )

        response = self._request("GET", url)

        if not response.content:
            raise DGIIError("DGII devolvió semilla vacía")

        return response.content

    def autenticar(self, xml_firmado: bytes):
        if not xml_firmado:
            raise DGIIError("XML firmado requerido")

        url = (
            f"{self.base}/autenticacion/"
            "api/autenticacion/validarsemilla"
        )

        response = self.session.post(
            url,
            files={
                "xml": (
                    "semilla_firmada.xml",
                    xml_firmado,
                    "text/xml"
                )
            },
            headers={"Accept": "application/json"},
            timeout=self.timeout
        )

        if not response.ok:
            raise DGIIError(
                f"Autenticación rechazada: "
                f"{response.status_code} "
                f"{response.text[:500]}"
            )

        data = response.json()

        self.token = data.get("token")
        self.expiracion = data.get("expira")

        if not self.token:
            raise DGIIError(
                "DGII no devolvió token"
            )

        return data

    def _auth_headers(self):
        if not self.token:
            raise DGIIError(
                "Primero debe autenticarse"
            )

        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }

    def enviar_ecf(self, xml_firmado: bytes):
        if not xml_firmado:
            raise DGIIError("XML e-CF vacío")

        url = (
            f"{self.base}/recepcion/"
            "api/facturaselectronicas"
        )

        response = self._request(
            "POST",
            url,
            files={
                "xml": (
                    "ecf.xml",
                    xml_firmado,
                    "text/xml"
                )
            },
            headers=self._auth_headers()
        )

        data = response.json()

        track_id = (
            data.get("trackId")
            or data.get("TrackId")
        )

        if not track_id:
            raise DGIIError(
                f"Respuesta sin TrackId: {data}"
            )

        return data

    def consultar_trackid(
        self,
        track_id: str,
        consulta_base: Optional[str] = None
    ):
        if not track_id:
            raise DGIIError("TrackID requerido")

        # La URL del servicio se puede configurar
        # según el directorio oficial DGII.
        base = consulta_base or (
            f"{self.base}/consultarresultado"
        )

        url = (
            f"{base.rstrip('/')}/api/consultas/estado"
        )

        response = self._request(
            "GET",
            url,
            params={"trackId": track_id},
            headers=self._auth_headers()
        )

        return response.json()
