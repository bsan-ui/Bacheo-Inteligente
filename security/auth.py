import os

def verificar_admin(usuario, clave):
    clave_correcta = os.getenv("BACHES_ADMIN_PASSWORD", "Demo-2026!")
    return usuario == "admin" and clave == clave_correcta
