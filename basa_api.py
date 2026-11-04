
import os
import sqlite3
import secrets

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="BASA e-CF PRO API",
    version="72.0"
)

API_KEY = os.environ.get("BASA_API_KEY")

if not API_KEY:
    raise RuntimeError("Configura BASA_API_KEY")


def verificar_api(x_api_key):
    if not x_api_key or not secrets.compare_digest(
        x_api_key, API_KEY
    ):
        raise HTTPException(
            status_code=401,
            detail="API Key inválida"
        )


class Factura(BaseModel):
    cliente: str
    rnc_cliente: str = ""
    descripcion: str
    cantidad: float = Field(gt=0)
    precio: float = Field(ge=0)
    itbis: float = Field(default=18, ge=0)
    descuento: float = Field(default=0, ge=0)
    tipo: str = "E31"


@app.get("/health")
def health():
    return {"status": "ok", "version": "72.0"}


@app.post("/clientes/{cid}/facturas")
def crear_factura(
    cid: str,
    factura: Factura,
    x_api_key: str = Header()
):
    verificar_api(x_api_key)

    if not cid.startswith("CLI-"):
        raise HTTPException(400, "Cliente inválido")

    total_bruto = factura.cantidad * factura.precio

    if factura.descuento > total_bruto:
        raise HTTPException(400, "Descuento inválido")

    base = total_bruto - factura.descuento
    impuesto = base * factura.itbis / 100
    total = base + impuesto

    return {
        "cliente_id": cid,
        "cliente": factura.cliente,
        "tipo": factura.tipo,
        "base": round(base, 2),
        "itbis": round(impuesto, 2),
        "total": round(total, 2),
        "estado": "PENDIENTE_DE_GENERACION_XML"
    }
