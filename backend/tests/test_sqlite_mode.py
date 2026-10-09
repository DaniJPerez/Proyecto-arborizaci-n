from fastapi.testclient import TestClient

import local_db
import main


def test_demo_sqlite_persists_tree_and_photo(monkeypatch, tmp_path):
    monkeypatch.setattr(local_db, "enabled", lambda: True)
    monkeypatch.setattr(local_db, "DATABASE_PATH", tmp_path / "inventario.sqlite3")
    monkeypatch.setattr(local_db, "PHOTO_DIR", tmp_path / "fotos")

    client = TestClient(main.app)
    assert client.get("/salud").json() == {
        "estado": "ok",
        "almacenamiento": "sqlite",
        "temporal": True,
    }

    login = client.post(
        "/auth/login",
        json={"email": local_db.LOCAL_EMAIL, "password": local_db.LOCAL_PASSWORD},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    catalogs = client.get("/catalogos").json()
    assert catalogs["especies"][0]["id"]
    assert catalogs["instituciones"][0]["id"] == "sj"

    tree = client.post(
        "/arboles",
        headers=headers,
        json={
            "institucion_id": "sj",
            "zona": "Patio central",
            "lat": 10.4638,
            "lng": -73.254,
            "especie_id": 1,
            "dap_cm": 35.5,
            "altura_m": 8.2,
            "copa_m": 4.5,
            "etapa": "Adulto",
            "interferencia": "Ninguna",
            "observaciones": ["f_manchas"],
        },
    )
    assert tree.status_code == 201
    assert tree.json()["codigo"] == "IE001-0001"
    assert tree.json()["estado"] == "riesgo"

    photo = client.post(
        f"/arboles/{tree.json()['id']}/fotos?tipo=completo",
        headers=headers,
        files={"archivo": ("arbol.jpg", b"\xff\xd8\xff\xe0demo", "image/jpeg")},
    )
    assert photo.status_code == 201
    assert (tmp_path / "fotos" / photo.json()["storage_path"]).is_file()

    detail = client.get(f"/arboles/{tree.json()['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["fotos"][0]["url"].endswith(photo.json()["storage_path"])
    assert client.get("/estadisticas", headers=headers).json()["total"] == 1


def test_demo_sqlite_rejects_bad_credentials(monkeypatch):
    monkeypatch.setattr(local_db, "enabled", lambda: True)
    response = TestClient(main.app).post(
        "/auth/login",
        json={"email": local_db.LOCAL_EMAIL, "password": "incorrecta"},
    )
    assert response.status_code == 401
