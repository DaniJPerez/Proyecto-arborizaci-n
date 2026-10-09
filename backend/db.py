"""Conexión a Supabase.

Hay tres formas de conectarse y cada una tiene un propósito distinto:

- get_admin():            clave secret (service_role). Salta el RLS.
                          Solo para catálogos públicos y tareas internas.
- cliente_de_usuario():   clave publishable + TOKEN DEL USUARIO.
                          El RLS aplica: cada usuario ve y edita lo que le toca.
- nuevo_cliente_anon():   clave publishable sin sesión. Solo para iniciar sesión.
"""
import os
from functools import lru_cache

from dotenv import load_dotenv
from supabase import Client, ClientOptions, create_client

load_dotenv()


def _env(nombre: str) -> str:
    valor = os.environ.get(nombre)
    if not valor:
        raise RuntimeError(f"Falta la variable {nombre} en el archivo .env")
    return valor


@lru_cache
def get_admin() -> Client:
    """Cliente con la clave secret. Nunca iniciar sesión de usuarios con este cliente."""
    return create_client(_env("SUPABASE_URL"), _env("SUPABASE_SERVICE_KEY"))


def nuevo_cliente_anon() -> Client:
    """Cliente nuevo en cada llamada, para que una sesión no se comparta entre usuarios."""
    return create_client(_env("SUPABASE_URL"), _env("SUPABASE_ANON_KEY"))


def cliente_de_usuario(token: str) -> Client:
    """Cliente que actúa en nombre del usuario dueño del token (el RLS aplica)."""
    return create_client(
        _env("SUPABASE_URL"),
        _env("SUPABASE_ANON_KEY"),
        options=ClientOptions(headers={"Authorization": f"Bearer {token}"}),
    )
