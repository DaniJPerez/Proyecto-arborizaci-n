# Backend — Inventario Arbóreo Escolar

API en **FastAPI** conectada a **Supabase** (PostgreSQL + RLS + Storage).

```
React  →  FastAPI (este proyecto)  →  Supabase
```

> **Modo temporal para presentaciones:** si no hay `SUPABASE_URL`, el backend usa
> SQLite automáticamente. También se puede seleccionar con `DATABASE_MODE=sqlite`.
> Los registros quedan en `backend/data/inventario.sqlite3` y las fotos en
> `backend/storage/fotos/`. Son archivos locales de demostración, no una base de
> datos definitiva ni un almacenamiento compartido: no sincronizan entre equipos,
> pueden perderse si se elimina la carpeta y no deben usarse para datos reales.
> Las carpetas de datos y fotos están excluidas de Git para evitar publicar
> información personal. El catálogo SQLite incluido es de ejemplo y debe
> reemplazarse por el catálogo aprobado antes de producción.

- Los datos del usuario se leen y escriben **con su propio token**, así el RLS de Supabase decide qué puede ver y editar.
- La lógica (validaciones, biomasa, CO₂, O₂, estadísticas) vive en Python.

## Estructura

```
backend/
├── main.py            ← endpoints
├── db.py              ← conexiones a Supabase (admin, de usuario, anónima)
├── auth.py            ← lee y valida el token del encabezado Authorization
├── schemas.py         ← modelos Pydantic (validaciones de entrada y salida)
├── calculos.py        ← biomasa, carbono, CO2, O2 y semáforo
├── tests/             ← pruebas automáticas (no necesitan Supabase)
├── pytest.ini
├── requerimientos.txt
├── .env               ← claves (NO se sube a Git)
└── .env.example       ← plantilla sin valores (sí se sube)
```

## Instalación

```powershell
cd backend
venv\Scripts\activate
pip install python-multipart pytest        # solo estas dos son nuevas
pip freeze > requerimientos.txt
```

Variables del `.env`:

```
DATABASE_MODE=sqlite
SQLITE_PATH=data/inventario.sqlite3
LOCAL_PHOTO_DIR=storage/fotos
DEMO_EMAIL=demo@arboles.local
DEMO_PASSWORD=demo123

# Solo se necesitan al cambiar a Supabase:
SUPABASE_URL=https://TU_ID.supabase.co
SUPABASE_ANON_KEY=sb_publishable_...
SUPABASE_SERVICE_KEY=sb_secret_...
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

`CORS_ORIGINS` son las direcciones del frontend que pueden llamar a la API.

En modo SQLite no se requiere configurar Supabase. El usuario local de demostración
se puede cambiar con `DEMO_EMAIL` y `DEMO_PASSWORD`; no reutilices estas credenciales
temporales para una instalación real. Para volver a Supabase, configura
`DATABASE_MODE=supabase` y completa las variables `SUPABASE_*`.

## Ejecutar

```powershell
uvicorn main:app --reload
```

Documentación interactiva: http://127.0.0.1:8000/docs

## Pruebas

```powershell
python -m pytest -q
```

Usan un cliente de Supabase falso: comprueban las validaciones, los permisos, las fórmulas y las estadísticas sin tocar tu base de datos.

## Endpoints

| Método | Ruta | ¿Token? | Qué hace |
|---|---|---|---|
| GET | `/salud` | No | Comprueba el servidor e informa si el almacenamiento es temporal |
| POST | `/auth/login` | No | Devuelve el token (`access_token`) |
| GET | `/catalogos` | No | Especies, instituciones y casillas fitosanitarias |
| POST | `/arboles` | Sí | Registra un árbol con sus observaciones |
| GET | `/arboles` | Sí | Lista con filtros (`institucion_id`, `estado`, `especie`, `zona`) y paginación |
| GET | `/arboles/{id}` | Sí | Detalle con observaciones y fotos (URLs temporales) |
| GET | `/arboles/{id}/calculos` | Sí | Biomasa, carbono, CO₂ y O₂ estimados |
| POST | `/arboles/{id}/fotos?tipo=...` | Sí | Sube una foto (`completo`, `detalle` o `adicional`) |
| GET | `/estadisticas` | Sí | Totales, semáforo, por institución, especies frecuentes, promedios y totales ambientales |

## Cómo lo usa el frontend (React)

**1. Iniciar sesión y guardar el token**

```js
const r = await fetch("http://127.0.0.1:8000/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password }),
});
const { access_token } = await r.json();
```

**2. Llamar a un endpoint protegido**

```js
const r = await fetch("http://127.0.0.1:8000/arboles", {
  headers: { Authorization: `Bearer ${access_token}` },
});
```

**3. Registrar un árbol**

```js
await fetch("http://127.0.0.1:8000/arboles", {
  method: "POST",
  headers: { "Content-Type": "application/json", Authorization: `Bearer ${access_token}` },
  body: JSON.stringify({
    institucion_id: "sj", zona: "Patio central", lat: 10.4638, lng: -73.254,
    especie_id: 1, dap_cm: 35.5, altura_m: 8.2, copa_m: 4.5,
    etapa: "Adulto", interferencia: "Ninguna",
    observaciones: ["f_manchas", "t_micelio"],
  }),
});
```

**4. Subir una foto**

```js
const form = new FormData();
form.append("archivo", archivoSeleccionado);          // input type="file"
await fetch(`http://127.0.0.1:8000/arboles/${id}/fotos?tipo=completo`, {
  method: "POST",
  headers: { Authorization: `Bearer ${access_token}` },   // sin Content-Type: el navegador lo pone
  body: form,
});
```

## Errores que devuelve la API

| Código | Cuándo |
|---|---|
| 401 | Falta el token, es inválido o expiró |
| 403 | No tienes permiso (por ejemplo, subir foto a un árbol ajeno) |
| 404 | El árbol no existe |
| 409 | Ya existe esa foto o ya hay 3 adicionales |
| 413 | La foto supera 5 MB |
| 422 | Datos inválidos (altura > 25 m, "Otra" sin texto, etapa inexistente, etc.) |

El cuerpo trae `detail` con el mensaje. Los errores que vienen de la base de datos incluyen además `codigo_db` y `tecnico` (útiles para depurar; se pueden quitar en producción).

## Reglas de negocio implementadas

- Altura máxima de 25 m; DAP y copa mayores que 0.
- Si la zona o la interferencia es "Otra", el texto es obligatorio.
- Una foto `completo`, una `detalle` y hasta 3 `adicional`; JPG, PNG o WebP; máximo 5 MB.
- Solo quien registró un árbol puede subirle fotos (el RLS impide además editar árboles ajenos).
- El código `IE001-0001` y el campo `registrado_por` los asigna la base de datos; el frontend nunca los envía.
- Semáforo provisional: 0 observaciones = sano, 1–3 = riesgo, 4 o más = crítico (vive en la vista `arboles_resumen`).

## Fórmulas ambientales (CONFIRMAR con el docente)

Están en `calculos.py`, con constantes ajustables al inicio del archivo:

1. Biomasa aérea (kg) = 0.0673 × (ρ × DAP² × H)^0.976 (Chave et al., 2014; ρ = densidad de la madera).
2. Raíces = aérea × 0.24.
3. Carbono = biomasa total × 0.47.
4. CO₂ = carbono × 44/12.
5. O₂ = CO₂ × 32/44.

La densidad es 0.6 g/cm³ para todas las especies mientras no se complete el diccionario `DENSIDADES`. **Son estimaciones**: si la asignación pide otras fórmulas, solo se cambia `calculos.py`.

## Despliegue (Render, opción gratuita)

1. Sube el repositorio a GitHub.
2. En render.com: **New → Web Service**, elige el repositorio y la carpeta `backend`.
3. Build command: `pip install -r requerimientos.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. En **Environment** agrega las 4 variables del `.env` (`CORS_ORIGINS` con la dirección real del frontend).

## Limitaciones conocidas

- SQLite es un modo temporal de demostración. Su catálogo se inicializa con
  instituciones, especies y observaciones de ejemplo; reemplázalos por los
  catálogos oficiales antes de integrar la base definitiva.
- `backend/data/inventario.sqlite3` y `backend/storage/fotos/` persisten en el
  computador donde se ejecuta el backend, pero están ignorados por Git y no se
  comparten con otros equipos. Haz copias manuales antes de borrar esos archivos
  si necesitas conservar una demostración.
- El acceso local usa una única cuenta de demostración configurable, no ofrece
  administración de usuarios ni debe exponerse a Internet.
- El prototipo no tiene login: React debe iniciar sesión con `/auth/login` (o `supabase-js`) antes de usar los endpoints protegidos. Los usuarios se crean a mano en Supabase.
- Si el registro de observaciones falla, el árbol se borra para no quedar a medias, pero el consecutivo del código ya consumido no se recupera.
- La regla "mínimo 2 fotos (completo + detalle)" no se obliga en la base de datos: el frontend debe subirlas después de crear el árbol.
- El plan gratuito de Supabase pausa el proyecto tras una semana sin actividad; se reactiva desde el panel.
- Si falla el guardado de una foto, se intenta borrar el archivo de Storage; si eso también falla, queda un archivo huérfano (sin efecto en los datos).
