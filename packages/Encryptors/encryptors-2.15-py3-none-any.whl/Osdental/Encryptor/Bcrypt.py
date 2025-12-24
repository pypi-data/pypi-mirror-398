import bcrypt
from Osdental.Exception.ControlledException import OSDException
from Osdental.Shared.Constant import Constant

class Bcrypt:
    
    def __init__(self, rounds: int = 12):
        """
        Initialize the password manager with bcrypt.
        
        :param rounds: cost factor (between 12 and 16 recommended).
        The higher the number, the safer but slower.
        """
        if rounds < 12:
            raise OSDException(error='It is recommended to use at least 12 rounds for greater security.')
        self.rounds = rounds

    def encrypt(self, password: str) -> str:
        """
        Hash the password using bcrypt.
        :param password: plain text password
        :return: string hash
        """
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password.encode(Constant.DEFAULT_ENCODING), salt)
        return hashed.decode(Constant.DEFAULT_ENCODING)

    def verify(self, hashed_password: str, plain_password: str) -> bool:
        """
        Checks if a plaintext password matches the hash.
        :param hashed_password: Hash stored in DB
        :param plain_password: Password entered by the user
        :return: True if matched, False if not
        """
        return bcrypt.checkpw(
            plain_password.encode(Constant.DEFAULT_ENCODING), hashed_password.encode(Constant.DEFAULT_ENCODING)
        )

    def needs_rehash(self, hashed_password: str) -> bool:
        """
        Determines whether a hash should be regenerated (e.g., you changed the number of rounds).
        :param hashed_password: Hash stored in DB
        :return: True if it should be regenerated
        """
        # bcrypt doesn't directly expose this as argon2, so we simulate it:
        parts = hashed_password.split('$')
        if len(parts) < 3:
            return True  # invalid hash → force rehash

        try:
            current_rounds = int(parts[2])
        except ValueError:
            return True

        return current_rounds != self.rounds
