import jwt
from typing import Dict
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


class JWT:

    @staticmethod
    def generate_token(payload: Dict, jwt_secret_key: str, algorithm: str = "HS256") -> str:
        token = jwt.encode(payload, jwt_secret_key, algorithm=algorithm)
        return token


    @staticmethod
    def extract_payload(jwt_token: str, jwt_secret_key: str) -> Dict[str, str]:
        payload = jwt.decode(jwt_token, jwt_secret_key, algorithms=["HS256"])
        return payload


    @staticmethod
    def generate_private_key(private_rsa: str):
        private_key = serialization.load_pem_private_key(
            private_rsa.encode(), password=None, backend=default_backend()
        )
        return private_key
