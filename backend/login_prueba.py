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