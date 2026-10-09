"""API del Inventario Arbóreo Escolar (FastAPI + Supabase).

Arquitectura:
    React  →  FastAPI (este archivo)  →  Supabase (PostgreSQL + RLS + Storage)

- Los datos del usuario se leen y escriben con SU token, así el RLS de Supabase
  decide qué puede ver y editar (ver db.py y auth.py).
- La lógica (validaciones, biomasa, CO2, O2, estadísticas) vive aquí, en Python.

Ejecutar:  uvicorn main:app --reload
Docs:      http://127.0.0.1:8000/docs
"""
import os
import uuid
from collections import Counter
from uuid import UUID

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from postgrest.exceptions import APIError
from supabase_auth.errors import AuthApiError

import calculos
import db
import local_db
from auth import Sesion, usuario_actual
from schemas import (
    ArbolCrear,
    ArbolDetalle,
    ArbolResumen,
    Calculos,
    Catalogos,
    ConteoEspecie,
    ConteoInstitucion,
    Estadisticas,
    Estado,
    FotoOut,
    LoginIn,
    ObservacionOut,
    Promedios,
    SesionOut,
    TipoFoto,
    TotalesAmbientales,
)

app = FastAPI(
    title="Inventario Arbóreo Escolar API",
    version="1.0.0",
    description="Backend del inventario arbóreo: registro de árboles, fotos, cálculos y estadísticas.",
)
app.mount(
    "/archivos/fotos",
    StaticFiles(directory=str(local_db.PHOTO_DIR), check_dir=False),
    name="fotos-locales-temporales",
)

# CORS: qué direcciones del frontend pueden llamar a esta API (separadas por coma en .env)
origenes = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origenes if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BUCKET_FOTOS = "fotos-arboles"
MAX_FOTO_BYTES = 5 * 1024 * 1024
MAX_FOTOS_ADICIONALES = 3
EXTENSIONES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


# =============================== Manejo de errores ===============================
# Traduce los códigos de error de PostgreSQL a respuestas HTTP entendibles para React.
ERRORES_DB = {
    "23514": (422, "Un valor no cumple las reglas de validación de la base de datos"),
    "23502": (422, "Falta un campo obligatorio"),
    "23503": (422, "Referencia a un dato que no existe (institución, especie u observación)"),
    "23505": (409, "Ese registro ya existe (por ejemplo, ya hay una foto de ese tipo)"),
    "42501": (403, "No tienes permiso para esta operación"),
}


@app.exception_handler(APIError)
async def manejar_error_db(request, exc: APIError):
    codigo = str(getattr(exc, "code", "") or "")
    estado, mensaje = ERRORES_DB.get(codigo, (500, "Error en la base de datos"))
    return JSONResponse(
        status_code=estado,
        content={"detail": mensaje, "codigo_db": codigo, "tecnico": getattr(exc, "message", None)},
    )


# ================================== Utilidades ===================================
def _resumen_por_id(cliente, arbol_id: str) -> dict:
    filas = cliente.table("arboles_resumen").select("*").eq("id", arbol_id).execute().data
    if not filas:
        raise HTTPException(status_code=404, detail="Árbol no encontrado")
    return filas[0]


def _traer_todo(cliente, tabla: str, columnas: str, tam: int = 1000) -> list[dict]:
    """PostgREST devuelve máximo 1000 filas por petición: se pide por páginas."""
    filas: list[dict] = []
    inicio = 0
    while True:
        lote = cliente.table(tabla).select(columnas).range(inicio, inicio + tam - 1).execute().data
        filas.extend(lote)
        if len(lote) < tam:
            return filas
        inicio += tam


def _url_firmada(cliente, ruta: str, segundos: int = 3600) -> str | None:
    try:
        r = cliente.storage.from_(BUCKET_FOTOS).create_signed_url(ruta, segundos)
        return r.get("signedURL") or r.get("signedUrl")
    except Exception:
        return None


# ===================================== Salud =====================================
@app.get("/salud", tags=["General"])
def salud():
    return {
        "estado": "ok",
        "almacenamiento": "sqlite" if local_db.enabled() else "supabase",
        "temporal": local_db.enabled(),
    }


# ================================ Autenticación ==================================
@app.post("/auth/login", response_model=SesionOut, tags=["Autenticación"])
def login(datos: LoginIn):
    """Inicia sesión y devuelve el token. El frontend lo envía luego como
    `Authorization: Bearer <access_token>`."""
    if local_db.enabled():
        if not local_db.authenticate(datos.email, datos.password):
            raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
        return SesionOut(
            access_token=local_db.LOCAL_TOKEN,
            user_id=local_db.LOCAL_USER_ID,
            email=local_db.LOCAL_EMAIL,
        )

    try:
        res = db.nuevo_cliente_anon().auth.sign_in_with_password(
            {"email": datos.email, "password": datos.password}
        )
    except AuthApiError:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    if res.session is None or res.user is None:
        raise HTTPException(status_code=401, detail="No se pudo iniciar sesión")

    return SesionOut(
        access_token=res.session.access_token,
        refresh_token=res.session.refresh_token,
        expires_in=res.session.expires_in,
        user_id=str(res.user.id),
        email=res.user.email,
    )


# ================================== Catálogos ====================================
@app.get("/catalogos", response_model=Catalogos, tags=["Catálogos"])
def catalogos():
    """Especies, instituciones y casillas fitosanitarias para llenar el formulario.
    Son datos públicos, por eso no piden token."""
    if local_db.enabled():
        return Catalogos(**local_db.catalogs())

    admin = db.get_admin()
    return Catalogos(
        especies=admin.table("especies").select("*").order("nombre_comun").execute().data,
        instituciones=admin.table("instituciones")
        .select("id, nombre, nombre_corto, prefijo, lat, lng")
        .order("prefijo")
        .execute()
        .data,
        observaciones=admin.table("observaciones_catalogo").select("*").order("grupo").order("orden").execute().data,
    )


# ==================================== Árboles ====================================
@app.post("/arboles", response_model=ArbolResumen, status_code=201, tags=["Árboles"])
def crear_arbol(datos: ArbolCrear, sesion: Sesion = Depends(usuario_actual)):
    """Registra un árbol con sus observaciones. El código (IE001-0001) y el
    usuario que lo registra los asigna la base de datos."""
    if local_db.enabled():
        try:
            return local_db.create_tree(datos.model_dump(), sesion.user_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    cliente = db.cliente_de_usuario(sesion.token)

    # 1) Validar que las casillas marcadas existan en el catálogo
    codigos = sorted(set(datos.observaciones))
    if codigos:
        validos = {f["codigo"] for f in cliente.table("observaciones_catalogo").select("codigo").execute().data}
        invalidos = [c for c in codigos if c not in validos]
        if invalidos:
            raise HTTPException(status_code=422, detail=f"Observaciones no válidas: {invalidos}")

    # 2) Guardar el árbol
    fila = datos.model_dump(exclude={"observaciones"})
    creado = cliente.table("arboles").insert(fila).execute().data[0]

    # 3) Guardar las observaciones; si falla, se borra el árbol para no dejarlo a medias
    if codigos:
        try:
            cliente.table("arbol_observaciones").insert(
                [{"arbol_id": creado["id"], "observacion_codigo": c} for c in codigos]
            ).execute()
        except Exception:
            db.get_admin().table("arboles").delete().eq("id", creado["id"]).execute()
            raise

    return _resumen_por_id(cliente, creado["id"])


@app.get("/arboles", response_model=list[ArbolResumen], tags=["Árboles"])
def listar_arboles(
    institucion_id: str | None = None,
    estado: Estado | None = None,
    especie: str | None = Query(None, description="Texto contenido en el nombre común"),
    zona: str | None = None,
    limite: int = Query(50, ge=1, le=200),
    desplazamiento: int = Query(0, ge=0),
    sesion: Sesion = Depends(usuario_actual),
):
    """Lista de árboles (pantalla de lista del prototipo) con filtros y paginación."""
    if local_db.enabled():
        return local_db.list_trees(
            institucion_id=institucion_id,
            estado=estado,
            especie=especie,
            zona=zona,
            limite=limite,
            desplazamiento=desplazamiento,
        )

    cliente = db.cliente_de_usuario(sesion.token)
    q = cliente.table("arboles_resumen").select("*")
    if institucion_id:
        q = q.eq("institucion_id", institucion_id)
    if estado:
        q = q.eq("estado", estado)
    if zona:
        q = q.eq("zona", zona)
    if especie:
        q = q.ilike("nombre_comun", f"%{especie}%")
    return q.order("registrado_en", desc=True).range(desplazamiento, desplazamiento + limite - 1).execute().data


@app.get("/arboles/{arbol_id}", response_model=ArbolDetalle, tags=["Árboles"])
def detalle_arbol(arbol_id: UUID, request: Request, sesion: Sesion = Depends(usuario_actual)):
    """Un árbol con sus observaciones y sus fotos (URLs temporales)."""
    if local_db.enabled():
        detalle = local_db.tree_detail(str(arbol_id))
        if detalle is None:
            raise HTTPException(status_code=404, detail="Árbol no encontrado")
        detalle["fotos"] = [
            {
                "id": foto["id"],
                "tipo": foto["tipo"],
                "url": str(request.base_url) + "archivos/fotos/" + foto["storage_path"],
            }
            for foto in detalle["fotos"]
        ]
        return detalle

    cliente = db.cliente_de_usuario(sesion.token)
    resumen = _resumen_por_id(cliente, str(arbol_id))

    filas_obs = (
        cliente.table("arbol_observaciones")
        .select("observacion_codigo, observaciones_catalogo(grupo, etiqueta)")
        .eq("arbol_id", str(arbol_id))
        .execute()
        .data
    )
    observaciones = [
        ObservacionOut(
            codigo=f["observacion_codigo"],
            grupo=f["observaciones_catalogo"]["grupo"],
            etiqueta=f["observaciones_catalogo"]["etiqueta"],
        )
        for f in filas_obs
    ]

    filas_fotos = cliente.table("arbol_fotos").select("id, tipo, storage_path").eq("arbol_id", str(arbol_id)).execute().data
    fotos = [FotoOut(id=f["id"], tipo=f["tipo"], url=_url_firmada(cliente, f["storage_path"])) for f in filas_fotos]

    return ArbolDetalle(**resumen, observaciones=observaciones, fotos=fotos)


@app.get("/arboles/{arbol_id}/calculos", response_model=Calculos, tags=["Árboles"])
def calculos_arbol(arbol_id: UUID, sesion: Sesion = Depends(usuario_actual)):
    """Biomasa, carbono, CO2 y O2 estimados para un árbol."""
    if local_db.enabled():
        arbol = local_db.tree_detail(str(arbol_id))
        if arbol is None:
            raise HTTPException(status_code=404, detail="Árbol no encontrado")
        return Calculos(
            codigo=arbol["codigo"],
            nombre_comun=arbol["nombre_comun"],
            dap_cm=arbol["dap_cm"],
            altura_m=arbol["altura_m"],
            metodo=calculos.METODO,
            advertencia=calculos.ADVERTENCIA,
            **calculos.calcular(arbol["dap_cm"], arbol["altura_m"], arbol["nombre_comun"]),
        )

    cliente = db.cliente_de_usuario(sesion.token)
    a = _resumen_por_id(cliente, str(arbol_id))
    valores = calculos.calcular(a["dap_cm"], a["altura_m"], a["nombre_comun"])
    return Calculos(
        codigo=a["codigo"],
        nombre_comun=a["nombre_comun"],
        dap_cm=a["dap_cm"],
        altura_m=a["altura_m"],
        metodo=calculos.METODO,
        advertencia=calculos.ADVERTENCIA,
        **valores,
    )


# ==================================== Fotos ======================================
@app.post("/arboles/{arbol_id}/fotos", status_code=201, tags=["Fotos"])
def subir_foto(
    arbol_id: UUID,
    tipo: TipoFoto = Query(..., description="completo, detalle o adicional"),
    archivo: UploadFile = File(...),
    sesion: Sesion = Depends(usuario_actual),
):
    """Sube una foto a Storage y registra su ruta. Solo quien registró el árbol puede hacerlo.
    Reglas: una foto 'completo', una 'detalle' y hasta 3 'adicional'. JPG, PNG o WebP, máx. 5 MB."""
    extension = EXTENSIONES.get(archivo.content_type or "")
    if extension is None:
        raise HTTPException(status_code=422, detail="Formato no permitido. Usa JPG, PNG o WebP.")

    contenido = archivo.file.read(MAX_FOTO_BYTES + 1)
    if not contenido:
        raise HTTPException(status_code=422, detail="El archivo está vacío")
    if len(contenido) > MAX_FOTO_BYTES:
        raise HTTPException(status_code=413, detail="La foto supera el máximo de 5 MB")

    if local_db.enabled():
        extension = EXTENSIONES[archivo.content_type or ""]
        nombre = f"{uuid.uuid4().hex}.{extension}"
        try:
            return local_db.add_photo(
                str(arbol_id), sesion.user_id, tipo, nombre, contenido
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except FileExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    cliente = db.cliente_de_usuario(sesion.token)

    arbol = cliente.table("arboles").select("id, registrado_por").eq("id", str(arbol_id)).execute().data
    if not arbol:
        raise HTTPException(status_code=404, detail="Árbol no encontrado")
    if arbol[0]["registrado_por"] != sesion.user_id:
        raise HTTPException(status_code=403, detail="Solo quien registró el árbol puede agregar fotos")

    if tipo == "adicional":
        existentes = (
            cliente.table("arbol_fotos").select("id").eq("arbol_id", str(arbol_id)).eq("tipo", "adicional").execute().data
        )
        if len(existentes) >= MAX_FOTOS_ADICIONALES:
            raise HTTPException(status_code=409, detail="Ya hay 3 fotos adicionales")

    ruta = f"{arbol_id}/{uuid.uuid4().hex}.{extension}"
    cliente.storage.from_(BUCKET_FOTOS).upload(ruta, contenido, {"content-type": archivo.content_type})

    try:
        fila = cliente.table("arbol_fotos").insert({"arbol_id": str(arbol_id), "tipo": tipo, "storage_path": ruta}).execute().data[0]
    except Exception:
        try:  # no dejar el archivo huérfano en Storage
            db.get_admin().storage.from_(BUCKET_FOTOS).remove([ruta])
        except Exception:
            pass
        raise

    return {"id": fila["id"], "tipo": tipo, "storage_path": ruta}


# ================================= Estadísticas ==================================
@app.get("/estadisticas", response_model=Estadisticas, tags=["Estadísticas"])
def estadisticas(sesion: Sesion = Depends(usuario_actual)):
    """Datos para las pantallas de inicio y estadísticas."""
    if local_db.enabled():
        return Estadisticas(**local_db.statistics())

    cliente = db.cliente_de_usuario(sesion.token)
    filas = _traer_todo(
        cliente,
        "arboles_resumen",
        "prefijo, nombre_corto, nombre_comun, dap_cm, altura_m, copa_m, etapa, estado",
    )

    total = len(filas)
    por_estado = {"sano": 0, "riesgo": 0, "critico": 0}
    por_estado.update(Counter(f["estado"] for f in filas))

    por_inst = Counter((f["prefijo"], f["nombre_corto"]) for f in filas)
    por_institucion = [
        ConteoInstitucion(prefijo=p, nombre_corto=n, total=t) for (p, n), t in sorted(por_inst.items())
    ]

    especies = Counter(f["nombre_comun"] for f in filas).most_common(5)

    def promedio(campo: str) -> float | None:
        return round(sum(f[campo] for f in filas) / total, 2) if total else None

    totales = {"biomasa_total_kg": 0.0, "carbono_kg": 0.0, "co2_kg": 0.0, "o2_kg": 0.0}
    for f in filas:
        c = calculos.calcular(f["dap_cm"], f["altura_m"], f["nombre_comun"])
        for clave in totales:
            totales[clave] += c[clave]

    return Estadisticas(
        total=total,
        por_estado=por_estado,
        por_institucion=por_institucion,
        por_etapa=dict(Counter(f["etapa"] for f in filas)),
        especies_frecuentes=[ConteoEspecie(nombre_comun=n, total=t) for n, t in especies],
        promedios=Promedios(dap_cm=promedio("dap_cm"), altura_m=promedio("altura_m"), copa_m=promedio("copa_m")),
        totales_ambientales=TotalesAmbientales(**{k: round(v, 2) for k, v in totales.items()}),
    )
