import jwt
from config.settings import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_DAYS
from datetime import datetime, timedelta


def create_jwt_token(user) -> str:
    payload = {
        "id": str(user.id),
        "email": user.email,
        "name": user.get_full_name() or user.email,
        "exp": datetime.now() + timedelta(days=JWT_EXPIRE_DAYS),
        "iat": datetime.now(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
