"""Almacenamiento temporal de demostración con SQLite y fotos en disco local."""
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import calculos

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.environ.get("SQLITE_PATH", BASE_DIR / "data" / "inventario.sqlite3"))
PHOTO_DIR = Path(os.environ.get("LOCAL_PHOTO_DIR", BASE_DIR / "storage" / "fotos"))
LOCAL_TOKEN = "local-demo-token"
LOCAL_USER_ID = "usuario-demo-local"
LOCAL_EMAIL = os.environ.get("DEMO_EMAIL", "demo@arboles.local")
LOCAL_PASSWORD = os.environ.get("DEMO_PASSWORD", "demo123")

ESPECIES = [
    (1, "Mango", "Mangifera indica"),
    (2, "Guayacán", "Handroanthus chrysanthus"),
    (3, "Ceiba", "Ceiba pentandra"),
    (4, "Roble", "Tabebuia rosea"),
]
INSTITUCIONES = [
    ("sj", "Institución Educativa San José", "San José", "IE001", 10.4638, -73.254),
]
OBSERVACIONES = [
    ("f_manchas", "follaje", "Manchas en las hojas", 1),
    ("f_amarillamiento", "follaje", "Amarillamiento", 2),
    ("t_grietas", "tronco", "Grietas en el tronco", 3),
    ("r_expuesta", "raiz", "Raíces expuestas", 4),
    ("p_insectos", "plagas", "Presencia de insectos", 5),
]

@contextmanager
def session() -> Iterator[sqlite3.Connection]:
    connection = connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def enabled() -> bool:
    mode = os.environ.get("DATABASE_MODE")
    if mode:
        normalized = mode.strip().lower()
        if normalized not in {"sqlite", "supabase"}:
            raise RuntimeError("DATABASE_MODE debe ser 'sqlite' o 'supabase'.")
        return normalized == "sqlite"
    return not os.environ.get("SUPABASE_URL")


def connect() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize() -> None:
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    with session() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS instituciones (
                id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                nombre_corto TEXT NOT NULL,
                prefijo TEXT NOT NULL UNIQUE,
                lat REAL NOT NULL,
                lng REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS especies (
                id INTEGER PRIMARY KEY,
                nombre_comun TEXT NOT NULL,
                nombre_cientifico TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS observaciones_catalogo (
                codigo TEXT PRIMARY KEY,
                grupo TEXT NOT NULL,
                etiqueta TEXT NOT NULL,
                orden INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS arboles (
                id TEXT PRIMARY KEY,
                codigo TEXT NOT NULL UNIQUE,
                institucion_id TEXT NOT NULL REFERENCES instituciones(id),
                zona TEXT NOT NULL,
                zona_otra TEXT,
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                especie_id INTEGER NOT NULL REFERENCES especies(id),
                dap_cm REAL NOT NULL CHECK(dap_cm > 0),
                altura_m REAL NOT NULL CHECK(altura_m > 0 AND altura_m <= 25),
                copa_m REAL NOT NULL CHECK(copa_m > 0),
                etapa TEXT NOT NULL,
                interferencia TEXT NOT NULL,
                interferencia_otra TEXT,
                registrado_en TEXT NOT NULL,
                registrado_por TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS arbol_observaciones (
                arbol_id TEXT NOT NULL REFERENCES arboles(id) ON DELETE CASCADE,
                observacion_codigo TEXT NOT NULL REFERENCES observaciones_catalogo(codigo),
                PRIMARY KEY(arbol_id, observacion_codigo)
            );
            CREATE TABLE IF NOT EXISTS arbol_fotos (
                id TEXT PRIMARY KEY,
                arbol_id TEXT NOT NULL REFERENCES arboles(id) ON DELETE CASCADE,
                tipo TEXT NOT NULL CHECK(tipo IN ('completo', 'detalle', 'adicional')),
                storage_path TEXT NOT NULL UNIQUE,
                creado_en TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS foto_unica_completa
                ON arbol_fotos(arbol_id) WHERE tipo = 'completo';
            CREATE UNIQUE INDEX IF NOT EXISTS foto_unica_detalle
                ON arbol_fotos(arbol_id) WHERE tipo = 'detalle';
            """
        )
        connection.executemany(
            "INSERT OR IGNORE INTO instituciones VALUES (?, ?, ?, ?, ?, ?)", INSTITUCIONES
        )
        connection.executemany(
            "INSERT OR IGNORE INTO especies VALUES (?, ?, ?)", ESPECIES
        )
        connection.executemany(
            "INSERT OR IGNORE INTO observaciones_catalogo VALUES (?, ?, ?, ?)", OBSERVACIONES
        )


def authenticate(email: str, password: str) -> bool:
    return email.strip().casefold() == LOCAL_EMAIL.casefold() and password == LOCAL_PASSWORD


def catalogs() -> dict:
    initialize()
    with session() as connection:
        return {
            "especies": [dict(row) for row in connection.execute(
                "SELECT id, nombre_comun, nombre_cientifico FROM especies ORDER BY nombre_comun"
            )],
            "instituciones": [dict(row) for row in connection.execute(
                "SELECT id, nombre, nombre_corto, prefijo, lat, lng FROM instituciones ORDER BY prefijo"
            )],
            "observaciones": [dict(row) for row in connection.execute(
                "SELECT codigo, grupo, etiqueta, orden FROM observaciones_catalogo ORDER BY grupo, orden"
            )],
        }


def _summary(connection: sqlite3.Connection, tree_id: str) -> dict | None:
    row = connection.execute(
        """
        SELECT a.*, i.prefijo, i.nombre_corto, e.nombre_comun, e.nombre_cientifico,
               COUNT(ao.observacion_codigo) AS n_observaciones
        FROM arboles a
        JOIN instituciones i ON i.id = a.institucion_id
        JOIN especies e ON e.id = a.especie_id
        LEFT JOIN arbol_observaciones ao ON ao.arbol_id = a.id
        WHERE a.id = ?
        GROUP BY a.id
        """,
        (tree_id,),
    ).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["estado"] = calculos.estado_por_observaciones(result["n_observaciones"])
    return result


def create_tree(data: dict, user_id: str) -> dict:
    initialize()
    tree_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    with session() as connection:
        institution = connection.execute(
            "SELECT prefijo FROM instituciones WHERE id = ?", (data["institucion_id"],)
        ).fetchone()
        if institution is None:
            raise ValueError("La institución seleccionada no existe en el catálogo local.")
        if connection.execute("SELECT 1 FROM especies WHERE id = ?", (data["especie_id"],)).fetchone() is None:
            raise ValueError("La especie seleccionada no existe en el catálogo local.")
        codes = sorted(set(data.get("observaciones", [])))
        if codes:
            placeholders = ",".join("?" for _ in codes)
            found = {
                row["codigo"] for row in connection.execute(
                    f"SELECT codigo FROM observaciones_catalogo WHERE codigo IN ({placeholders})", codes
                )
            }
            invalid = sorted(set(codes) - found)
            if invalid:
                raise ValueError(f"Observaciones no válidas: {invalid}")
        last = connection.execute(
            "SELECT codigo FROM arboles WHERE institucion_id = ? ORDER BY codigo DESC LIMIT 1",
            (data["institucion_id"],),
        ).fetchone()
        number = int(last["codigo"].rsplit("-", 1)[1]) + 1 if last else 1
        codigo = f"{institution['prefijo']}-{number:04d}"
        connection.execute(
            """
            INSERT INTO arboles (
                id, codigo, institucion_id, zona, zona_otra, lat, lng, especie_id,
                dap_cm, altura_m, copa_m, etapa, interferencia, interferencia_otra,
                registrado_en, registrado_por
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tree_id, codigo, data["institucion_id"], data["zona"], data.get("zona_otra"),
                data["lat"], data["lng"], data["especie_id"], data["dap_cm"], data["altura_m"],
                data["copa_m"], data["etapa"], data["interferencia"],
                data.get("interferencia_otra"), timestamp, user_id,
            ),
        )
        connection.executemany(
            "INSERT INTO arbol_observaciones (arbol_id, observacion_codigo) VALUES (?, ?)",
            [(tree_id, code) for code in codes],
        )
        result = _summary(connection, tree_id)
    if result is None:
        raise RuntimeError("No fue posible leer el árbol recién registrado.")
    return result


def list_trees(
    institucion_id: str | None = None,
    estado: str | None = None,
    especie: str | None = None,
    zona: str | None = None,
    limite: int = 50,
    desplazamiento: int = 0,
) -> list[dict]:
    initialize()
    query = """
        SELECT a.id FROM arboles a
        JOIN especies e ON e.id = a.especie_id
        WHERE 1 = 1
    """
    params: list = []
    if institucion_id:
        query += " AND a.institucion_id = ?"
        params.append(institucion_id)
    if especie:
        query += " AND e.nombre_comun LIKE ?"
        params.append(f"%{especie}%")
    if zona:
        query += " AND a.zona = ?"
        params.append(zona)
    if estado:
        observation_count = "(SELECT COUNT(*) FROM arbol_observaciones ao WHERE ao.arbol_id = a.id)"
        if estado == "sano":
            query += f" AND {observation_count} = 0"
        elif estado == "riesgo":
            query += f" AND {observation_count} BETWEEN 1 AND 3"
        else:
            query += f" AND {observation_count} >= 4"
    query += " ORDER BY a.registrado_en DESC LIMIT ? OFFSET ?"
    params.extend([limite, desplazamiento])
    with session() as connection:
        trees = [_summary(connection, row["id"]) for row in connection.execute(query, params)]
    return [tree for tree in trees if tree is not None]


def tree_detail(tree_id: str) -> dict | None:
    initialize()
    with session() as connection:
        result = _summary(connection, tree_id)
        if result is None:
            return None
        result["observaciones"] = [
            dict(row) for row in connection.execute(
                """
                SELECT c.codigo, c.grupo, c.etiqueta
                FROM arbol_observaciones ao
                JOIN observaciones_catalogo c ON c.codigo = ao.observacion_codigo
                WHERE ao.arbol_id = ? ORDER BY c.orden
                """,
                (tree_id,),
            )
        ]
        result["fotos"] = [
            dict(row) for row in connection.execute(
                "SELECT id, tipo, storage_path FROM arbol_fotos WHERE arbol_id = ? ORDER BY creado_en",
                (tree_id,),
            )
        ]
        return result


def add_photo(tree_id: str, user_id: str, tipo: str, filename: str, content: bytes) -> dict:
    initialize()
    with session() as connection:
        tree = connection.execute(
            "SELECT registrado_por FROM arboles WHERE id = ?", (tree_id,)
        ).fetchone()
        if tree is None:
            raise LookupError("Árbol no encontrado")
        if tree["registrado_por"] != user_id:
            raise PermissionError("Solo quien registró el árbol puede agregar fotos")
        count = connection.execute(
            "SELECT COUNT(*) AS total FROM arbol_fotos WHERE arbol_id = ? AND tipo = ?",
            (tree_id, tipo),
        ).fetchone()["total"]
        if tipo == "adicional" and count >= 3:
            raise FileExistsError("Ya hay 3 fotos adicionales")
        if tipo != "adicional" and count:
            raise FileExistsError(f"Ya existe una foto de tipo {tipo}")
        photo_id = str(uuid.uuid4())
        relative_path = f"{tree_id}/{filename}"
        target = PHOTO_DIR / tree_id / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        try:
            connection.execute(
                "INSERT INTO arbol_fotos (id, arbol_id, tipo, storage_path, creado_en) VALUES (?, ?, ?, ?, ?)",
                (photo_id, tree_id, tipo, relative_path, datetime.now(timezone.utc).isoformat()),
            )
        except Exception:
            target.unlink(missing_ok=True)
            raise
    return {"id": photo_id, "tipo": tipo, "storage_path": relative_path}


def statistics() -> dict:
    trees = list_trees(limite=100000)
    total = len(trees)
    by_status = {"sano": 0, "riesgo": 0, "critico": 0}
    by_institution: dict[tuple[str, str], int] = {}
    by_stage: dict[str, int] = {}
    by_species: dict[str, int] = {}
    sums = {"dap_cm": 0.0, "altura_m": 0.0, "copa_m": 0.0}
    environmental = {"biomasa_total_kg": 0.0, "carbono_kg": 0.0, "co2_kg": 0.0, "o2_kg": 0.0}
    for tree in trees:
        by_status[tree["estado"]] += 1
        institution_key = (tree["prefijo"], tree["nombre_corto"])
        by_institution[institution_key] = by_institution.get(institution_key, 0) + 1
        by_stage[tree["etapa"]] = by_stage.get(tree["etapa"], 0) + 1
        by_species[tree["nombre_comun"]] = by_species.get(tree["nombre_comun"], 0) + 1
        for key in sums:
            sums[key] += tree[key]
        values = calculos.calcular(tree["dap_cm"], tree["altura_m"], tree["nombre_comun"])
        for key in environmental:
            environmental[key] += values[key]
    return {
        "total": total,
        "por_estado": by_status,
        "por_institucion": [
            {"prefijo": key[0], "nombre_corto": key[1], "total": amount}
            for key, amount in sorted(by_institution.items())
        ],
        "por_etapa": by_stage,
        "especies_frecuentes": [
            {"nombre_comun": name, "total": amount}
            for name, amount in sorted(by_species.items(), key=lambda item: (-item[1], item[0]))[:5]
        ],
        "promedios": {
            key: round(value / total, 2) if total else None for key, value in sums.items()
        },
        "totales_ambientales": {
            key: round(value, 2) for key, value in environmental.items()
        },
    }
