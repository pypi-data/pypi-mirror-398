from typing import Optional
from pydantic import BaseModel, Field

class Legacy(BaseModel):
    id_legacy: str = Field(alias="IdLegacy")
    legacy_name: Optional[str] = Field(default=None, alias="LegacyName")
    id_enterprise: str = Field(alias="IdEnterprise")
    auth_token_exp_min: int = Field(alias="AuthTokenExpMin")
    public_key2: str = Field(alias="PublicKey2")
    private_key1: str = Field(alias="SecretKey1")
    private_key2: str = Field(alias="SecretKey2")
    aes_key_user: str = Field(alias="AesUser")
    aes_key_auth: str = Field(alias="AesAuth")

    class ConfigDict:
        populate_by_name = True