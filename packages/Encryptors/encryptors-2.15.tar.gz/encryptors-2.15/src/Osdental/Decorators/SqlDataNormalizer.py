import uuid
import re
from functools import wraps
from sqlalchemy.engine.row import RowMapping, Row
from sqlalchemy.engine import Result
from typing import Any, Callable, Awaitable

UUID_REGEX = re.compile(
    r"^[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}$"
)

def is_uuid_string(value: str) -> bool:
    """Verifica si un string tiene formato UUID."""
    if not isinstance(value, str):
        return False
    return bool(UUID_REGEX.match(value))


def dictify_sql_result(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """
    Decorador que convierte automáticamente los resultados devueltos por funciones asíncronas
    que usan SQLAlchemy (ORM o Core), transformando RowMapping o Row en dicts puros.
    
    Maneja correctamente:
    - None
    - Escalares (int, str, etc.)
    - RowMapping / Row únicos o listas
    - Result devuelto sin procesar
    """

    def normalize_value(value: Any) -> Any:
         # --- Caso 1: UUID real ---
        if isinstance(value, uuid.UUID):
            return str(value).lower()

        # --- Caso 2: Varchar que es UUID ---
        if isinstance(value, str) and is_uuid_string(value):
            return value.lower()

        # --- Caso 3: Diccionarios ---
        if isinstance(value, dict):
            return {k: normalize_value(v) for k, v in value.items()}

        # --- Caso 4: Listas o tuplas ---
        if isinstance(value, (list, tuple)):
            return [normalize_value(v) for v in value]

        return value
    
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)

        if result is None:
            return None

        if isinstance(result, Result):
            try:
                rows = result.mappings().all()
                return [normalize_value(dict(r)) for r in rows]
            except Exception:
                rows = result.all()
                return [normalize_value(dict(r._mapping)) for r in rows]

        if isinstance(result, list) and result:
            first_item = result[0]
            if isinstance(first_item, RowMapping):
                return [normalize_value(dict(r)) for r in result]
            if isinstance(first_item, Row):
                return [normalize_value(dict(r._mapping)) for r in result]
            
            return [normalize_value(r) for r in result]

        if isinstance(result, RowMapping):
            return normalize_value(dict(result))
        if isinstance(result, Row):
            return normalize_value(dict(result._mapping))

        return normalize_value(result)

    return wrapper
