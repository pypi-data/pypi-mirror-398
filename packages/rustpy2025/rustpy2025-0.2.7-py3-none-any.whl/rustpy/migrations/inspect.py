# def inspect_models(models):
#     schema = {}

#     for m in models:
#         table = m._meta["table"]
#         cols = {}

#         for name, field in m._meta["fields"].items():
#             cols[name] = field.get_sql()
#         print("🧾 Inspecting model:", table, cols)
#         schema[table] = cols

#     print("🧾 SCHEMA:", schema)

#     return schema



def get_tables(db):
    rows = db.fetch_all(
        "SELECT name FROM sqlite_master WHERE type='table';"
    )
    
    return {row["name"] for row in rows}


def get_columns(db, table):
    rows = db.fetch_all(f"PRAGMA table_info({table});")
    return {row["name"] for row in rows}
