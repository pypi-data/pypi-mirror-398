from pydantic import BaseModel, Field
from typing import Optional
from Osdental.Models.Encryptor import Encryptor

class AuthToken(BaseModel):
    id_token: str = Field(alias="idToken")
    id_user: str = Field(alias="idUser")
    id_external_enterprise: str = Field(alias="idExternalEnterprise")
    id_tenant: str = Field(alias="idTenant")
    id_profile: str = Field(alias="idProfile")
    id_legacy: str = Field(alias="idLegacy")
    id_item_report: str = Field(alias="idItemReport")
    id_enterprise: str = Field(alias="idEnterprise")
    id_authorization: str = Field(alias="idAuthorization")
    user_full_name: str = Field(alias="userFullName")
    abbreviation: str = Field(alias="abbreviation")
    aes_key_auth: str = Field(alias="aesKeyAuth")
    access_token: Optional[str] = None
    base_id_external_enterprise: Optional[str] = None
    mk_id_external_enterprise: Optional[str] = None
    jwt_user_key: Optional[str] = None
    encryptor: Optional[Encryptor] = None

    class ConfigDict:
        populate_by_name = True