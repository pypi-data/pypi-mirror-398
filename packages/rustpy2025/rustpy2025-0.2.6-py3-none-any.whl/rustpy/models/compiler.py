# rustpy/models/compiler.py

class SQLCompiler:
    def __init__(self, model_cls):
        self.model = model_cls
        self.meta = model_cls._meta

    def create_table_sql(self):
        table_name = self.meta["table"]
        fields = self.meta["fields"]

        if not fields:
            raise ValueError("Modelda field yo‘q")

        columns_sql = []
        for field in fields.values():
            columns_sql.append(field.get_sql())

        columns_block = ",\n    ".join(columns_sql)

        sql = f"""CREATE TABLE IF NOT EXISTS {table_name} (
    {columns_block}
);"""
        return sql
