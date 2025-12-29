from rustpy.models.registry import ModelRegistry
from rustpy.migrations.inspect import get_tables, get_columns


# =====================================================
# 🔍 MODELDA PRIMARY KEY BORLIGINI TEKSHIRISH
# =====================================================
def has_primary_key(fields: dict) -> bool:
    for field in fields.values():
        if "PRIMARY KEY" in field.get_sql().upper():
            return True
    return False


# =====================================================
# 🚀 SAFE MIGRATE
# =====================================================
def safe_migrate(db, models=None):

    if models is None:
        models = ModelRegistry.get_models()

    if not models:
        print("❌ No models found")
        return

    existing_tables = set(get_tables(db))

    for model in models:
        table = model._meta["table"]
        fields = model._meta["fields"]  # {name: Field}

        model_cols = set(fields.keys())
        model_has_pk = has_primary_key(fields)

        # =====================================================
        # 1️⃣ TABLE YO‘Q → CREATE
        # =====================================================
        if table not in existing_tables:
            cols_sql = [field.get_sql() for field in fields.values()]
            db.execute(f"CREATE TABLE {table} ({', '.join(cols_sql)});")
            print(f"✅ Created table {table}")
            continue

        # =====================================================
        # 2️⃣ TABLE BOR → TEKSHIRUV
        # =====================================================
        existing_cols = set(get_columns(db, table))

        print("🧾 EXISTING_COLS:", existing_cols)
        print("🧾 MODEL_COLS:", model_cols)

        # =====================================================
        # 3️⃣ PRIMARY KEY YO‘Q → MAJBURIY REBUILD
        # =====================================================
        if model_has_pk and not any(
            "PRIMARY KEY" in fields[name].get_sql().upper()
            and name in existing_cols
            for name in fields
        ):
            print(f"🔥 PRIMARY KEY missing in {table} → rebuilding")
            _rebuild_table(db, table, fields, existing_cols)
            continue

        # =====================================================
        # 4️⃣ YANGI COLUMNLAR
        # =====================================================
        rebuild_required = False

        for name, field in fields.items():
            if name not in existing_cols:
                sql_upper = field.get_sql().upper()

                # ⚠️ SQLite limitation
                if (
                    "PRIMARY KEY" in sql_upper
                    or "UNIQUE" in sql_upper
                    or "NOT NULL" in sql_upper
                ):
                    rebuild_required = True
                    break

                db.execute(f"ALTER TABLE {table} ADD COLUMN {field.get_sql()};")
                print(f"➕ Added column {table}.{name}")

        # =====================================================
        # 5️⃣ ORTIQCHA COLUMNLAR → REBUILD
        # =====================================================
        extra_cols = existing_cols - model_cols
        if extra_cols:
            print(f"🔥 Extra columns detected {extra_cols}")
            rebuild_required = True

        # =====================================================
        # 6️⃣ REBUILD
        # =====================================================
        if rebuild_required:
            print(f"🔁 Rebuilding table {table}")
            _rebuild_table(db, table, fields, existing_cols)

    print("🎉 safe_migrate finished")


# =====================================================
# 🔧 TABLE REBUILD
# =====================================================
def _rebuild_table(db, table, fields, existing_cols):
    tmp_table = f"{table}_old"

    # 🧹 eski backup bo‘lsa o‘chiramiz
    db.execute(f"DROP TABLE IF EXISTS {tmp_table}")

    # 1️⃣ rename
    db.execute(f"ALTER TABLE {table} RENAME TO {tmp_table}")

    # 2️⃣ yangi table
    cols_sql = [field.get_sql() for field in fields.values()]
    db.execute(f"CREATE TABLE {table} ({', '.join(cols_sql)});")

    # 3️⃣ data copy
    insert_cols = []
    select_exprs = []

    for name, field in fields.items():
        sql = field.get_sql().upper()

        insert_cols.append(name)

        if name in existing_cols:
            select_exprs.append(name)
        else:
            if "NOT NULL" in sql:
                if "DEFAULT" in sql:
                    select_exprs.append(name)  # SQLite default ishlaydi
                else:
                    select_exprs.append("''")  # fallback
            else:
                select_exprs.append("NULL")

    insert_sql = ", ".join(insert_cols)
    select_sql = ", ".join(select_exprs)

    db.execute(f"""
        INSERT INTO {table} ({insert_sql})
        SELECT {select_sql} FROM {tmp_table}
    """)

    # 4️⃣ eski table delete
    db.execute(f"DROP TABLE {tmp_table}")

    print(f"✅ Rebuilt table {table}")
