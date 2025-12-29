# rustpy/models/queryset_async.py
from rustpy.atomic_async import atomic
from rustpy.tx_state import in_transaction


class AsyncQuerySet:
    DEFAULT_LIMIT = 100

    def __init__(self, model, backend):
        self.model = model
        self.backend = backend
        self._filters = {}

    # ---------- FILTER ----------
    def afilter(self, **kwargs):
        self._validate_fields(kwargs)
        qs = AsyncQuerySet(self.model, self.backend)
        qs._filters = {**self._filters, **kwargs}
        return qs

    # ---------- READ ----------
    async def aall(self, limit=None):
        return await self._execute(limit or self.DEFAULT_LIMIT)

    async def aget(self, **kwargs):
        qs = self.afilter(**kwargs)
        res = await qs._execute(limit=2)
        if not res:
            raise ValueError("Object does not exist")
        if len(res) > 1:
            raise ValueError("Multiple objects returned")
        return res[0]

    # ---------- CREATE ----------
    async def acreate(self, **kwargs):
        self._validate_fields(kwargs)

        async def _create():
            fields = list(kwargs.keys())
            values = list(kwargs.values())
            placeholders = ", ".join(["?"] * len(values))
            sql = f"""
            INSERT INTO {self._table()}
            ({", ".join(fields)})
            VALUES ({placeholders});
            """
            await self.backend.execute(sql, values)

        if in_transaction():
            await _create()
        else:
            async with atomic():
                await _create()
        await self.backend.close()
        return self.model(**kwargs)

    # ---------- UPDATE ----------
    async def aupdate(self, **kwargs):
        if not self._filters:
            raise RuntimeError("Refusing UPDATE without filters")

        self._validate_fields(kwargs)

        async def _update():
            set_sql = ", ".join(f"{k}=?" for k in kwargs)
            where_sql, params = self._where()

            sql = f"""
            UPDATE {self._table()}
            SET {set_sql}
            WHERE {where_sql};
            """
            await self.backend.execute(
                sql,
                list(kwargs.values()) + params
            )

        # 🔐 auto-atomic (Django-like)
        if in_transaction():
            await _update()
        else:
            async with atomic():
                await _update()

        # 🔄 UPDATED NATIJANI QAYTARAMIZ
        results = await self.aall()

        # Django kabi:
        if len(results) == 1:
            return results[0]
        return "Update successful"


    # ---------- DELETE ----------
    async def adelete(self):
        if not self._filters:
            raise RuntimeError("Refusing DELETE without filters")

        from rustpy.models.registry import ModelRegistry

        async def _delete():
            objs = await self.aall()
            if not objs:
                return

            visited = set()

            for obj in objs:
                obj_id = getattr(obj, "id", None)
                if obj_id is None or (self.model, obj_id) in visited:
                    continue

                visited.add((self.model, obj_id))

                for model in ModelRegistry.get_models():
                    for field in model._meta["fields"].values():
                        if not hasattr(field, "to") or field.to != self.model:
                            continue

                        qs = model.aobjects.afilter(
                            **{field.column_name: obj_id}
                        )

                        if field.on_delete == field.RESTRICT:
                            if await qs.aall():
                                raise RuntimeError(
                                    f"Cannot delete {self.model.__name__}({obj_id})"
                                )

                        elif field.on_delete == field.SET_NULL:
                            await qs.aupdate(**{field.column_name: None})

                        elif field.on_delete == field.CASCADE:
                            await qs.adelete()

            where_sql, params = self._where()
            sql = f"DELETE FROM {self._table()} WHERE {where_sql};"
            await self.backend.execute(sql, params)
            

        if in_transaction():
            await _delete()
        else:
            async with atomic():
                await _delete()
        await self.backend.close()
        return "Delete successful"

    # ---------- INTERNAL ----------
    async def _execute(self, limit):
        where_sql, params = self._where(optional=True)
        sql = f"""
        SELECT * FROM {self._table()}
        {f"WHERE {where_sql}" if where_sql else ""}
        LIMIT {limit};
        """
        rows = await self.backend.fetch_all(sql, params)
        await self.backend.close()
        return [self.model(**dict(r)) for r in rows]

    def _where(self, optional=False):
        if not self._filters:
            return ("", []) if optional else ("1=1", [])
        clauses, params = [], []
        for k, v in self._filters.items():
            clauses.append(f"{k}=?")
            params.append(v)
        return " AND ".join(clauses), params

    def _validate_fields(self, data):
        allowed = self.model._meta["fields"]
        for key in data:
            if key not in allowed:
                raise ValueError(f"Invalid field: {key}")

    def _table(self):
        table = self.model._meta["table"]
        if not table.replace("_", "").isalnum():
            raise RuntimeError("Invalid table name")
        return table
