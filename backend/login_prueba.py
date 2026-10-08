import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])

# 1) Iniciar sesión
res = sb.auth.sign_in_with_password({
    "email": os.environ["TEST_EMAIL"],
    "password": os.environ["TEST_PASSWORD"],
})
print("Usuario  ->", res.user.id)
print("Token    ->", res.session.access_token[:20] + "...")   # solo el inicio

# 2) Ahora el RLS te deja leer
print("especies ->", len(sb.table("especies").select("*").execute().data), "filas")

nuevo = {
    "institucion_id": "sj", "zona": "Patio central",
    "lat": 10.4638, "lng": -73.254, "especie_id": 1,
    "dap_cm": 30.0, "altura_m": 7.5, "copa_m": 4.0,
    "etapa": "Adulto", "interferencia": "Ninguna",
}
r = sb.table("arboles").insert(nuevo).execute()
print("Árbol    ->", r.data[0]["codigo"], "| registrado_por:", r.data[0]["registrado_por"])