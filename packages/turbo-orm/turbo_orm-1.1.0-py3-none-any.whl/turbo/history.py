from .model import Model
from .fields import IntegerField, TextField
import datetime
import json


class HistoryModel(Model):
    @classmethod
    def create_table(cls, db):
        super().create_table(db)

        # Create history table
        history_table = f"{cls._table_name}_history"
        fields_sql = [
            "history_id INTEGER PRIMARY KEY AUTOINCREMENT",
            "original_id INTEGER",
            "timestamp TEXT",
            "action TEXT",
        ]

        # Only include actual table columns (not M2M fields)
        for name, field in cls._fields.items():
            if field.__class__.__name__ != "ManyToManyField":
                sql_type = field.get_sql_type()
                fields_sql.append(f'"{name}" {sql_type}')

        sql = f"CREATE TABLE IF NOT EXISTS {history_table} ({', '.join(fields_sql)})"
        db.execute(sql)

    def save(self, db):
        is_new = self.id is None
        super().save(db)

        # Record history (excluding M2M fields)
        history_table = f"{self._table_name}_history"
        real_fields = [
            name
            for name, field in self._fields.items()
            if field.__class__.__name__ != "ManyToManyField"
        ]

        fields = ["original_id", "timestamp", "action"] + real_fields

        values = [
            self.id,
            datetime.datetime.now().isoformat(),
            "INSERT" if is_new else "UPDATE",
        ]

        for f in real_fields:
            val = getattr(self, f)
            # Handle serialization same as Model.save
            field = self._fields[f]
            if isinstance(val, datetime.datetime):
                val = val.isoformat()
            elif field.__class__.__name__ == "JSONField" and not isinstance(val, str):
                val = json.dumps(val)
            values.append(val)

        placeholders = ", ".join(["?"] * len(fields))
        columns = ", ".join([f'"{f}"' for f in fields])

        sql = f"INSERT INTO {history_table} ({columns}) VALUES ({placeholders})"
        db.execute(sql, values)

    @classmethod
    def history(cls, db, id):
        history_table = f"{cls._table_name}_history"
        sql = f"SELECT * FROM {history_table} WHERE original_id = ? ORDER BY history_id DESC"
        cursor = db.execute(sql, (id,))
        return [dict(row) for row in cursor.fetchall()]

    def revert(self, db, history_id):
        history_table = f"{self._table_name}_history"
        sql = f"SELECT * FROM {history_table} WHERE history_id = ?"
        cursor = db.execute(sql, (history_id,))
        row = cursor.fetchone()

        if not row:
            raise ValueError("History entry not found")

        data = dict(row)
        # Restore fields (exclude M2M)
        for name in self._fields:
            if (
                self._fields[name].__class__.__name__ != "ManyToManyField"
                and name in data
            ):
                setattr(self, name, data[name])

        # Save to update main table (will create a new history entry for the revert)
        self.save(db)
