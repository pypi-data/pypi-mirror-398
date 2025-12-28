from typing import Optional, Any
import base64


class Field:
    __slots__ = ("required", "default", "name", "table_name")

    def __init__(self, required: bool = False, default: Any = None) -> None:
        self.required = required
        self.default = default
        self.name: Optional[str] = None  # Set by the metaclass
        self.table_name: Optional[str] = None  # Only for ForeignKey/ManyToMany

    def get_sql_type(self) -> str:
        raise NotImplementedError

    def to_sql(self, value: Any) -> Any:
        """Convert Python value to SQL representation. Override in subclasses."""
        return value

    def encrypt(self, text: Optional[str]) -> Optional[str]:
        """Encrypt text. Only implemented in EncryptedField."""
        return text

    def decrypt(self, encrypted_text: Optional[str]) -> Optional[str]:
        """Decrypt text. Only implemented in EncryptedField."""
        return encrypted_text


class IntegerField(Field):
    __slots__ = ()

    def get_sql_type(self) -> str:
        return "INTEGER"


class TextField(Field):
    __slots__ = ()

    def get_sql_type(self) -> str:
        return "TEXT"


class FloatField(Field):
    def get_sql_type(self) -> str:
        return "REAL"


class BooleanField(Field):
    def get_sql_type(self) -> str:
        return "INTEGER"


class DateTimeField(Field):
    def get_sql_type(self) -> str:
        return "TEXT"


class JSONField(Field):
    def get_sql_type(self) -> str:
        return "TEXT"


class ForeignKey(Field):
    __slots__ = ()

    def __init__(self, table_name: str, required: bool = False, default: Any = None) -> None:
        super().__init__(required, default)
        self.table_name = table_name

    def get_sql_type(self) -> str:
        return "INTEGER"


class ManyToManyField(Field):
    __slots__ = ()

    def __init__(self, table_name: str) -> None:
        super().__init__(required=False, default=None)
        self.table_name = table_name

    def get_sql_type(self) -> Optional[str]:
        return None  # Not a real column


class EncryptedField(Field):
    __slots__ = ("key",)

    def __init__(self, key: Optional[str] = None, required: bool = False, default: Any = None) -> None:
        super().__init__(required, default)
        self.key = key or "default_key_12345"  # Simple default key

    def get_sql_type(self) -> str:
        return "TEXT"

    def encrypt(self, text: Optional[str]) -> Optional[str]:
        if text is None:
            return None
        # Simple XOR cipher
        key_bytes = self.key.encode()
        text_bytes = str(text).encode()
        encrypted = bytearray()
        for i, byte in enumerate(text_bytes):
            encrypted.append(byte ^ key_bytes[i % len(key_bytes)])
        return base64.b64encode(encrypted).decode()

    def decrypt(self, encrypted_text: Optional[str]) -> Optional[str]:
        if encrypted_text is None:
            return None
        encrypted = base64.b64decode(encrypted_text.encode())
        key_bytes = self.key.encode()
        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            decrypted.append(byte ^ key_bytes[i % len(key_bytes)])
        return decrypted.decode()
