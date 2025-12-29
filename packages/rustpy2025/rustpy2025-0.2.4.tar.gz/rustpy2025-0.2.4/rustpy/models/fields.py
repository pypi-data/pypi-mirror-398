# rustpy/models/fields.py

class Field:
    sql_type = None  # har bir field o‘zi belgilaydi

    def __init__(
        self,
        *,
        null=False,
        default=None,
        unique=False,
        primary_key=False,
    ):
        self.null = null
        self.default = default
        self.unique = unique
        self.primary_key = primary_key
        self.name = None

    def contribute_to_class(self, name):
        self.name = name

    # SQL bo‘lagi (compiler shu yerdan oladi)
    def get_sql(self):
        if not self.sql_type:
            raise NotImplementedError("sql_type belgilanmagan")

        parts = [self.name, self.sql_type]

        if self.primary_key:
            parts.append("PRIMARY KEY")

        if self.unique:
            parts.append("UNIQUE")

        if not self.null and not self.primary_key:
            parts.append("NOT NULL")

        if self.default is not None:
            parts.append(f"DEFAULT {self.format_default(self.default)}")

        return " ".join(parts)

    def format_default(self, value):
        if isinstance(value, str):
            return f"'{value}'"
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        return str(value)

class IntegerField(Field):
    sql_type = "INTEGER"

class BigIntegerField(Field):
    sql_type = "BIGINT"

class BooleanField(Field):
    sql_type = "BOOLEAN"

class CharField(Field):
    def __init__(self, max_length=255, **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length
        self.sql_type = f"VARCHAR({self.max_length})"

class ForeignKey(Field):
    CASCADE = "CASCADE"
    SET_NULL = "SET NULL"
    RESTRICT = "RESTRICT"

    def __init__(self, to, on_delete=CASCADE, **kwargs):
        super().__init__(**kwargs)
        self.to = to
        self.on_delete = on_delete

        # SET NULL bo‘lsa majburiy null
        if self.on_delete == self.SET_NULL:
            self.null = True

    def contribute_to_class(self, name):
        self.name = name
        # 🔥 ORM standarti
        self.column_name = f"{name}_id"
        self.sql_type = "INTEGER"

    def __get__(self, instance, owner):
        if instance is None:
            return self

        fk_id = getattr(instance, self.column_name, None)
        if fk_id is None:
            return None

        return self.to.objects.get(id=fk_id)

    def get_sql(self):
        table = self.to._meta["table"]

        sql = f"{self.column_name} {self.sql_type}"

        if not self.null:
            sql += " NOT NULL"

        # 🔥 ASOSIY FARQ SHU YERDA
        sql += f" REFERENCES {table}(id) ON DELETE {self.on_delete}"

        if self.unique:
            sql += " UNIQUE"

        return sql

