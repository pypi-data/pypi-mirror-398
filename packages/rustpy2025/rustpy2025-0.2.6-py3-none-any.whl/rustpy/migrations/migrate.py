# from rustpy.db import get_backend
# import os, importlib.util


# def migrate(db=None):
#     if db is None:
#         db = get_backend()

#     # 1️⃣ MIGRATION HISTORY TABLE
#     db.execute("""
#     CREATE TABLE IF NOT EXISTS _rustpy_migrations (
#         name TEXT PRIMARY KEY
#     )
#     """)

#     migrations_dir = "apps/models/migrations"
#     if not os.path.exists(migrations_dir):
#         print("No migrations to apply.")
#         return

#     # 2️⃣ APPLIED MIGRATIONS
#     applied = {
#         row[0]
#         for row in db.fetch_all("SELECT name FROM _rustpy_migrations")
#     }


#     # 3️⃣ APPLY NEW MIGRATIONS
#     for fn in sorted(os.listdir(migrations_dir)):
#         if not fn.endswith(".py") or fn.startswith("_"):
#             continue

#         if fn in applied:
#             continue

#         path = f"{migrations_dir}/{fn}"
#         name = fn[:-3]

#         print(f"Applying migration: {fn}")

#         spec = importlib.util.spec_from_file_location(name, path)
#         module = importlib.util.module_from_spec(spec)
#         spec.loader.exec_module(module)

#         if hasattr(module, "forwards"):
#             module.forwards(db)

#         db.execute(
#     f"INSERT INTO _rustpy_migrations (name) VALUES ('{fn}')"
# )


#     print("Migrations applied successfully.")
