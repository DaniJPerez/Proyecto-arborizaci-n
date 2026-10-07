import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.environ["SUPABASE_URL"]

# 1) Con la clave anon (sin sesión): el RLS debe bloquear las filas
anon = create_client(url, os.environ["SUPABASE_ANON_KEY"])
print("anon        ->", len(anon.table("especies").select("*").execute().data), "filas")

# 2) Con la service_role (salta el RLS): solo para verificar
admin = create_client(url, os.environ["SUPABASE_SERVICE_KEY"])
print("service_role ->", len(admin.table("especies").select("*").execute().data), "filas")