"""Autenticación: lee el token del encabezado Authorization y comprueba que sea válido."""
from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import db

# auto_error=False para devolver nuestro propio 401 con un mensaje claro
esquema_bearer = HTTPBearer(auto_error=False)


@dataclass
class Sesion:
    token: str
    user_id: str
    email: str | None


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
) -> Sesion:
    """Dependencia de FastAPI: protege un endpoint.

    El frontend debe enviar:  Authorization: Bearer <access_token>
    """
    if credenciales is None:
        raise HTTPException(status_code=401, detail="Falta el token. Inicia sesión.")

    token = credenciales.credentials
    try:
        # Supabase Auth confirma que el token es válido y no ha expirado
        usuario = db.get_admin().auth.get_user(token).user
    except Exception:
        usuario = None

    if usuario is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")

    return Sesion(token=token, user_id=str(usuario.id), email=usuario.email)
