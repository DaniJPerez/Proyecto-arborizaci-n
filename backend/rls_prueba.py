import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
sb.auth.sign_in_with_password({"email": os.environ["TEST_EMAIL2"], "password": os.environ["TEST_PASSWORD2"]})

# Prueba A: ¿puede ver los árboles de otro usuario?
print("A) ve árboles ->", len(sb.table("arboles").select("*").execute().data))

# Prueba B: ¿puede editar el árbol de otro usuario?
r = sb.table("arboles").update({"altura_m": 20}).eq("codigo", "IE001-0001").execute()
print("B) filas editadas ->", len(r.data))

# Prueba C: ¿puede registrar un árbol a nombre de otro usuario?
falso = {
    "institucion_id": "sj", "zona": "Patio central", "lat": 10.46, "lng": -73.25,
    "especie_id": 1, "dap_cm": 20, "altura_m": 5, "copa_m": 3,
    "etapa": "Juvenil", "interferencia": "Ninguna",
    "registrado_por": "00000000-0000-0000-0000-000000000000",
}
try:
    sb.table("arboles").insert(falso).execute()
except Exception as e:
    print("C) rechazado ->", e)