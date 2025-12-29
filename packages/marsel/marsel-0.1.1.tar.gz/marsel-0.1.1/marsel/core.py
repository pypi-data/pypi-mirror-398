import secrets
from passlib.context import CryptContext


class Marsel:
    """
    Common security helpers:
    - bcrypt password hashing and verification
    - numeric OTP generation
    """

    @property
    def get_crypt_context(self) -> CryptContext:
        return CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self.get_crypt_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.get_crypt_context.verify(plain_password, hashed_password)

    @staticmethod
    def generate_random_otp(length: int = 6) -> str:
        digits = "0123456789"
        return "".join(secrets.choice(digits) for _ in range(length))
