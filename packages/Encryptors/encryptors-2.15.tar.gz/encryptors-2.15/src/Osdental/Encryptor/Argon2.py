from argon2 import PasswordHasher, exceptions

class Argon2:
    
    def __init__(
        self, 
        time_cost: int = 3, 
        memory_cost: int = 65536, 
        parallelism: int = 4,
        salt_len: int = 32,
        hash_len: int = 32
    ):
        """
        Initializes the password manager with Argon2id.
        
        :param time_cost: Number of iterations (CPU cost)
        :param memory_cost: Memory used in KB (64MB by default)
        :param parallelism: Parallel threads
        """
        self.ph = PasswordHasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
            salt_len=salt_len,
            hash_len=hash_len
        )

    def encrypt(self, password: str) -> str:
        """
        Hash the password using Argon2id.
        :param password: plain text password
        :return: generated hash
        """
        return self.ph.hash(password)

    def verify(self, hashed_password: str, plain_password: str) -> bool:
        """
        Checks if a plaintext password matches the hash.
        :param hashed_password: saved hash
        :param plain_password: password to validate
        :return: True if matched, False if not
        """
        if not hashed_password or not isinstance(hashed_password, str):
            return False

        try:
            return self.ph.verify(hashed_password, plain_password)

        except (
            exceptions.VerifyMismatchError,
            exceptions.InvalidHashError,
            exceptions.VerificationError,
        ):
            return False

    def needs_rehash(self, hashed_password: str) -> bool:
        """
        Determines whether a hash should be regenerated (for example if you changed parameters).
        :param hashed_password: saved hash
        :return: True if it needs to be regenerated
        """
        return self.ph.check_needs_rehash(hashed_password)
