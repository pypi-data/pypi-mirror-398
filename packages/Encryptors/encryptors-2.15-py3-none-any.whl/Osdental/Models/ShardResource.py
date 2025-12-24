from typing import Optional, List
from pydantic import BaseModel, Field

class DatabaseData(BaseModel):
    id_tenant: str = Field(alias="IdTenant")
    id_shard: str = Field(alias="IdShard")
    shard_name: str = Field(alias="ShardName")
    conn_string: str = Field(alias="ConnectionString")
    is_read_only: bool = Field(default=False, alias="IsReadOnly")

    class ConfigDict:
        populate_by_name = True


class RedisData(BaseModel):
    id_tenant: str = Field(alias="IdTenant")
    id_shard: str = Field(alias="IdShard")
    shard_name: str = Field(alias="ShardName")
    conn_string: str = Field(alias="ConnectionString")
    is_read_only: bool = Field(default=False, alias="IsReadOnly")

    class ConfigDict:
        populate_by_name = True

class ShardResource(BaseModel):
    database: List[DatabaseData] = Field(alias="DataBase")
    redis: Optional[List[RedisData]] = Field(default=None, alias="Redis")
    microservices: Optional[List] = Field(default=None, alias="MicroServices")

    class ConfigDict:
        populate_by_name = True
