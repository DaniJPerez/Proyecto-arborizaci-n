"""
API de Gestión de Tareas — Proyecto de aprendizaje FastAPI
------------------------------------------------------------
Este proyecto demuestra los conceptos fundamentales de FastAPI:
- Modelos de datos con Pydantic (validación automática)
- Operaciones CRUD (Crear, Leer, Actualizar, Eliminar)
- Códigos de estado HTTP correctos
- Manejo de errores con HTTPException
- Documentación automática (Swagger UI)

Para ejecutar:
    uvicorn main:app --reload

Luego abre: http://127.0.0.1:8000/docs
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from supabase import create_client

load_dotenv()

app = FastAPI(title="Inventario Arbóreo Escolar API", version="0.1.0")

# Provisional: este cliente salta el RLS. Solo lo usamos para catálogos.
# En el Módulo 5 lo reemplazamos por el token del usuario.
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


# ---------- Modelos (la forma de los datos que devuelve la API) ----------
class Especie(BaseModel):
    id: int
    nombre_comun: str
    nombre_cientifico: str


# ---------- Endpoints ----------
@app.get("/salud")
def salud():
    return {"estado": "ok"}


@app.get("/especies", response_model=list[Especie])
def listar_especies(
    buscar: str | None = None,
    limite: int = Query(50, ge=1, le=100),
):
    q = (
        supabase.table("especies")
        .select("id, nombre_comun, nombre_cientifico")
        .order("nombre_comun")
        .limit(limite)
    )
    if buscar:
        q = q.ilike("nombre_comun", f"%{buscar}%")
    return q.execute().data


@app.get("/especies/{especie_id}", response_model=Especie)
def obtener_especie(especie_id: int):
    r = (
        supabase.table("especies")
        .select("id, nombre_comun, nombre_cientifico")
        .eq("id", especie_id)
        .execute()
    )
    if not r.data:
        raise HTTPException(status_code=404, detail="Especie no encontrada")
    return r.data[0]