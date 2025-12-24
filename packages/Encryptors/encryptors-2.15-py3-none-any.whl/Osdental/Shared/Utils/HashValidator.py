import re

class HashValidator:

    @staticmethod
    def is_sha512(value: str) -> bool:
        return bool(re.fullmatch(r'[a-fA-F0-9]{128}', value))

    @staticmethod
    def is_argon2(value: str) -> bool:
        return value.startswith('$argon2')

    @staticmethod
    def is_bcrypt(value: str) -> bool:
        return value.startswith('$2b$') or value.startswith('$2a$')
