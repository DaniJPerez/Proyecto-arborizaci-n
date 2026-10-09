# Mi Proyecto — Backend (FastAPI) + Frontend (React)

Repositorio único que contiene el backend y el frontend del proyecto, cada uno en su propia carpeta.

```
mi-proyecto/
├── backend/        # API en FastAPI (Python)
├── frontend/        # Interfaz en React
├── .gitignore
└── README.md
```

## Requisitos previos

- Python 3.10+ instalado
- Node.js y npm instalados

## Cómo levantar el backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
uvicorn main:app --reload
```

El backend queda disponible en `http://127.0.0.1:8000` (documentación interactiva en `/docs`).
Sin `SUPABASE_URL`, inicia automáticamente en modo SQLite temporal para demos:
árboles en `backend/data/inventario.sqlite3`, fotos en `backend/storage/fotos/`,
correo `demo@arboles.local` y contraseña `demo123`. Los catálogos son datos de
ejemplo; no uses este modo con datos reales. Los archivos locales no se suben a Git.
Consulta [backend/README_backend.md](backend/README_backend.md) para configurar SQLite
o volver a Supabase.

## Cómo levantar el frontend

```bash
cd frontend
npm install
npm start
```

El frontend queda disponible normalmente en `http://localhost:3000`.

## Flujo de trabajo del equipo

- Cada tarea se trabaja en su propia rama: `feature/backend-...` o `feature/frontend-...`.
- Nadie sube `venv/` ni `node_modules/` — cada persona los genera localmente a partir de `requirements.txt` y `package.json`.
- Los cambios se integran a `main` mediante Pull Request, revisados por al menos un compañero.
- Si el backend cambia la forma de los datos que devuelve (modelos Pydantic), avisar al equipo de frontend antes de mergear.

## Variables de entorno

Cada carpeta (`backend/` y `frontend/`) maneja su propio archivo `.env` (no se sube a Git). Ejemplo típico en `frontend/.env`:

```
REACT_APP_API_URL=http://127.0.0.1:8000
```
