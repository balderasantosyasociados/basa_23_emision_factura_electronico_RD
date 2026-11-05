# ==============================================================================
# BASA AUTONOMIA - VERIFICADOR DE DEPENDENCIAS
# ==============================================================================

import sys
import subprocess
import importlib.util

DEPENDENCIAS = {
    "streamlit": "streamlit>=1.40.0",
    "numpy": "numpy>=2.0.0",
    "pandas": "pandas>=2.2.0",
    "openpyxl": "openpyxl>=3.1.5",
    "xlsxwriter": "xlsxwriter>=3.2.0",
    "sqlalchemy": "SQLAlchemy>=2.0.0",
    "fastapi": "fastapi>=0.115.0",
    "uvicorn": "uvicorn[standard]>=0.30.0",
    "multipart": "python-multipart>=0.0.9",
    "pydantic": "pydantic>=2.8.0",
    "requests": "requests>=2.32.0",
    "dotenv": "python-dotenv>=1.0.0",
    "cryptography": "cryptography>=43.0.0",
    "lxml": "lxml>=5.3.0",
    "signxml": "signxml>=4.0.0",
    "PIL": "Pillow>=10.0.0",
    "dateutil": "python-dateutil>=2.8.2",
}


def paquete_instalado(modulo):
    return importlib.util.find_spec(modulo) is not None


def instalar_paquete(paquete):
    print(f"📦 Instalando: {paquete}")

    resultado = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            paquete,
        ],
        capture_output=True,
        text=True,
    )

    if resultado.returncode == 0:
        print(f"✅ Instalado correctamente: {paquete}")
        return True

    print(f"❌ Error instalando: {paquete}")
    print(resultado.stderr)
    return False


def verificar_dependencias():
    faltantes = []

    print("=" * 70)
    print("🏦 BASA SUPERSISTEMA V27 - AUTODIAGNÓSTICO")
    print("=" * 70)

    for modulo, paquete in DEPENDENCIAS.items():

        if paquete_instalado(modulo):
            print(f"✅ {modulo}")
        else:
            print(f"⚠️ FALTA: {modulo}")
            faltantes.append(paquete)

    return faltantes


def reparar_dependencias():

    faltantes = verificar_dependencias()

    if not faltantes:
        print("\n🎯 TODAS LAS DEPENDENCIAS BASA ESTÁN INSTALADAS.")
        return True

    print("\n🔧 INICIANDO REPARACIÓN AUTOMÁTICA...")

    errores = []

    for paquete in faltantes:
        if not instalar_paquete(paquete):
            errores.append(paquete)

    print("\n" + "=" * 70)

    if not errores:
        print("✅ REPARACIÓN COMPLETADA")
        print("🔄 Reinicie BASA para cargar las nuevas dependencias.")
        return True

    print("❌ NO SE PUDIERON INSTALAR:")
    for error in errores:
        print(f"   - {error}")

    return False


if __name__ == "__main__":
    reparar_dependencias()
