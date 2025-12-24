from typing import Dict, Any

class QueryGenerator:
    
    @staticmethod
    def generate(schema_name: str, table_name: str, data: Dict[str, Any] = None) -> str:
        query = f"EXEC {schema_name}.{table_name}"
 
        if data is not None:
            for key in data.keys():
                query += f"\n@i_{key} = :{key},"
            query = query[:-1]
 
        return query