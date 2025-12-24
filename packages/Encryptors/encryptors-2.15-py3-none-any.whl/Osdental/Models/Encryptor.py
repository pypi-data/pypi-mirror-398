from pydantic import BaseModel, Field

class Encryptor(BaseModel):
    public_key_1: str = Field(alias="PublicKey1")
    public_key_2: str = Field(alias="PublicKey2")
    private_key_1: str = Field(alias="SecretKey1")
    private_key_2: str = Field(alias="SecretKey1")
    aes_auth: str = Field(alias="AesAuth")
    aes_user: str = Field(alias="AesUser")

    class ConfigDict:
        populate_by_name = True