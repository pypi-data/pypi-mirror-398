#!/usr/bin/env python3
# aetos.py

import sys
import subprocess
import os

# 🔧 SERVIDOR DE PAQUETES PERSONALIZADO (definido en código)
INDEX_URL = "https://nexus.uclv.edu.cu/repository/pypi.org/"  # Mirror de Tsinghua (China)
# INDEX_URL = "https://pypi.org/simple/"                  # PyPI oficial
# INDEX_URL = "https://pypi.miprivate.com/simple/"       # Tu registry privado

def main():
    if len(sys.argv) < 2:
        print("❌ Uso: aetos <comando> [paquetes]")
        print("Ej: aetos install requests")
        sys.exit(1)

    # Comando de pip (ej: install, list, uninstall)
    command = sys.argv[1]

    # Argumentos restantes
    args = sys.argv[2:]

    # Construir el comando de pip
    pip_cmd = [
        sys.executable, "-m", "pip", command,
        "--index-url", INDEX_URL,
        "--trusted-host", INDEX_URL.split("//")[-1].split("/")[0],  # Host sin https://
    ] + args

    # Si el usuario ya pasó --index-url, ignoramos el nuestro (opcional)
    # Pero en este caso, forzamos el nuestro.

    print(f"🦅 Aetos: usando índice {INDEX_URL}")
    print(f"🚀 Ejecutando: {' '.join(pip_cmd)}")

    # Ejecutar el comando
    try:
        result = subprocess.run(pip_cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar pip: {e}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("❌ No se encontró pip. Asegúrate de tener Python instalado correctamente.")
        sys.exit(1)

if __name__ == "__main__":
    main()