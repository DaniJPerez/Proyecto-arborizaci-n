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

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

# ---------------------------------------------------------------
# 1. Instancia de la aplicación
# ---------------------------------------------------------------
app = FastAPI(
    title="API de Gestión de Tareas",
    description="Proyecto de aprendizaje para dominar los fundamentos de FastAPI",
    version="1.0.0",
)


# ---------------------------------------------------------------
# 2. Modelos de datos (Pydantic)
#    Pydantic valida automáticamente los datos que entran y salen.
# ---------------------------------------------------------------
class EstadoTarea(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"


class TareaBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=100, examples=["Estudiar FastAPI"])
    descripcion: Optional[str] = Field(None, max_length=500)
    estado: EstadoTarea = EstadoTarea.pendiente


class TareaCrear(TareaBase):
    """Datos requeridos para crear una tarea (el cliente no envía id)."""
    pass


class TareaActualizar(BaseModel):
    """Todos los campos opcionales: permite actualizar solo lo que se envíe."""
    titulo: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    estado: Optional[EstadoTarea] = None


class Tarea(TareaBase):
    """Modelo completo que se devuelve al cliente, incluye el id."""
    id: int


# ---------------------------------------------------------------
# 3. "Base de datos" en memoria
#    En un proyecto real esto sería una base de datos (SQLite, Postgres, etc.)
# ---------------------------------------------------------------
tareas_db: dict[int, Tarea] = {}
contador_id = 0


# ---------------------------------------------------------------
# 4. Endpoints CRUD
# ---------------------------------------------------------------

@app.get("/", tags=["Raíz"])
def inicio():
    """Endpoint de bienvenida — confirma que la API está corriendo."""
    return {"mensaje": "API de Gestión de Tareas funcionando correctamente"}


@app.post("/Arboles", response_model=Tarea, status_code=status.HTTP_201_CREATED, tags=["Tareas"])
def crear_tarea(tarea: TareaCrear):
    """Crea una nueva tarea. FastAPI valida el cuerpo automáticamente contra TareaCrear."""
    global contador_id
    contador_id += 1
    nueva_tarea = Tarea(id=contador_id, **tarea.model_dump())
    tareas_db[contador_id] = nueva_tarea
    return nueva_tarea


@app.get("/tareas", response_model=list[Tarea], tags=["Tareas"])
def listar_tareas(estado: Optional[EstadoTarea] = None):
    """Lista todas las tareas. Permite filtrar opcionalmente por estado (?estado=pendiente)."""
    if estado is None:
        return list(tareas_db.values())
    return [t for t in tareas_db.values() if t.estado == estado]


@app.get("/tareas/{tarea_id}", response_model=Tarea, tags=["Tareas"])
def obtener_tarea(tarea_id: int):
    """Obtiene una tarea específica por su id."""
    tarea = tareas_db.get(tarea_id)
    if tarea is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    return tarea


@app.put("/tareas/{tarea_id}", response_model=Tarea, tags=["Tareas"])
def actualizar_tarea(tarea_id: int, cambios: TareaActualizar):
    """Actualiza parcialmente una tarea existente (solo los campos enviados)."""
    tarea = tareas_db.get(tarea_id)
    if tarea is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

    datos_actualizados = cambios.model_dump(exclude_unset=True)
    tarea_actualizada = tarea.model_copy(update=datos_actualizados)
    tareas_db[tarea_id] = tarea_actualizada
    return tarea_actualizada


@app.delete("/tareas/{tarea_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tareas"])
def eliminar_tarea(tarea_id: int):
    """Elimina una tarea por su id."""
    if tarea_id not in tareas_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    del tareas_db[tarea_id]
    return None
