# rustpy/models/queryset.py
from rustpy.atomic import atomic


class QuerySet:
    def __init__(self, model, backend):
        
        self.model = model
        self.backend = backend
        self._filters = {}

    # =========================
    # INTERNAL
    # =========================
    def _build_where(self):
        if not self._filters:
            return "", []

        clauses = []
        params = []

        for k, v in self._filters.items():
            clauses.append(f"{k} = ?")
            params.append(v)

        return " WHERE " + " AND ".join(clauses), params

    # =========================
    # READ (atomic kerak emas)
    # =========================
    def all(self):
        return self._execute()

    def filter(self, **kwargs):
        qs = QuerySet(self.model, self.backend)
        qs._filters = {**self._filters, **kwargs}
        return qs

    def get(self, **kwargs):
        qs = self.filter(**kwargs)
        rows = qs._execute(limit=2)

        if not rows:
            raise ValueError("Object does not exist")
        if len(rows) > 1:
            raise ValueError("Multiple objects returned")

        return rows[0]

    # =========================
    # WRITE (AUTO-ATOMIC 🔥)
    # =========================
    def create(self, **kwargs):
        fields = list(kwargs.keys())
        values = list(kwargs.values())

        placeholders = ", ".join(["?"] * len(values))
        fields_sql = ", ".join(fields)

        sql = f"""
        INSERT INTO {self.model._meta['table']}
        ({fields_sql})
        VALUES ({placeholders})
        """

        with atomic():
            self.backend.execute(sql, values)

        return kwargs  # dict

    def update(self, **kwargs):
        if not self._filters:
            raise ValueError("Update requires filter")

        set_sql = ", ".join(f"{k} = ?" for k in kwargs)
        set_values = list(kwargs.values())
        where_sql, where_values = self._build_where()

        sql = f"""
        UPDATE {self.model._meta['table']}
        SET {set_sql}
        {where_sql}
        """

        with atomic():
            self.backend.execute(sql, set_values + where_values)

    def delete(self):
        if not self._filters:
            raise ValueError("Delete requires filter")

        from rustpy.models.registry import ModelRegistry

        with atomic():
            # 1️⃣ O‘chiriladigan obyektlar
            objs = self.all()
            if not objs:
                return

            for obj in objs:
                # 2️⃣ FK chain
                for model in ModelRegistry.get_models():
                    for field in model._meta["fields"].values():
                        if not hasattr(field, "to"):
                            continue

                        if field.to != self.model:
                            continue

                        qs = model.objects.filter(
                            **{field.column_name: obj["id"]}
                        )

                        if field.on_delete == field.RESTRICT:
                            if qs.all():
                                raise RuntimeError(
                                    f"Cannot delete: protected by {model.__name__}"
                                )

                        elif field.on_delete == field.SET_NULL:
                            qs.update(**{field.column_name: None})

                        elif field.on_delete == field.CASCADE:
                            qs.delete()

            # 3️⃣ Asosiy DELETE
            where_sql, params = self._build_where()
            sql = f"""
            DELETE FROM {self.model._meta['table']}
            {where_sql}
            """
            self.backend.execute(sql, params)

    # =========================
    # INTERNAL EXEC
    # =========================
    def _execute(self, limit=None):
        where_sql, params = self._build_where()
        sql = f"SELECT * FROM {self.model._meta['table']}{where_sql}"
        if limit:
            sql += f" LIMIT {limit}"

        rows = self.backend.fetch_all(sql, params)
        return [self.model(**dict(r)) for r in rows]
