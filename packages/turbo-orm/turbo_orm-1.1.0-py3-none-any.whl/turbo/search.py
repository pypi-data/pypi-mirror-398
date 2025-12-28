from .model import Model


class SearchableModel(Model):
    @classmethod
    def create_table(cls, db):
        super().create_table(db)

        # Create FTS virtual table (exclude M2M fields)
        fts_table = f"{cls._table_name}_fts"

        # Only include actual table columns (not M2M fields)
        real_fields = [
            name
            for name, field in cls._fields.items()
            if field.__class__.__name__ != "ManyToManyField"
        ]

        columns = [f'"{name}"' for name in real_fields]
        columns_str = ", ".join(columns)

        # Using FTS5
        sql = f"CREATE VIRTUAL TABLE IF NOT EXISTS {fts_table} USING fts5({columns_str}, content='{cls._table_name}', content_rowid='id')"
        db.execute(sql)

        # Create Triggers to keep FTS in sync (using only real fields)
        # INSERT Trigger
        db.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS {cls._table_name}_ai AFTER INSERT ON {cls._table_name} BEGIN
                INSERT INTO {fts_table}(rowid, {columns_str}) VALUES (new.id, {", ".join([f"new.{c}" for c in real_fields])});
            END;
        """
        )

        # DELETE Trigger
        db.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS {cls._table_name}_ad AFTER DELETE ON {cls._table_name} BEGIN
                INSERT INTO {fts_table}({fts_table}, rowid, {columns_str}) VALUES('delete', old.id, {", ".join([f"old.{c}" for c in real_fields])});
            END;
        """
        )

        # UPDATE Trigger
        db.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS {cls._table_name}_au AFTER UPDATE ON {cls._table_name} BEGIN
                INSERT INTO {fts_table}({fts_table}, rowid, {columns_str}) VALUES('delete', old.id, {", ".join([f"old.{c}" for c in real_fields])});
                INSERT INTO {fts_table}(rowid, {columns_str}) VALUES (new.id, {", ".join([f"new.{c}" for c in real_fields])});
            END;
        """
        )

    @classmethod
    def search(cls, db, query):
        fts_table = f"{cls._table_name}_fts"
        # We select from the main table using the rowids found in the FTS table
        sql = f"""
            SELECT * FROM {cls._table_name} 
            WHERE id IN (SELECT rowid FROM {fts_table} WHERE {fts_table} MATCH ? ORDER BY rank)
        """
        cursor = db.execute(sql, (query,))

        instances = []
        for row in cursor.fetchall():
            data = dict(row)
            id_val = data.pop("id")
            instance = cls(**data)
            instance.id = id_val
            instances.append(instance)
        return instances
