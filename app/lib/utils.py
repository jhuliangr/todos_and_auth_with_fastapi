import uuid
from jose import jwt
from config import Settings, get_settings


def generate_uuid():
    return str(uuid.uuid4())

def create_access_token(data: dict):
    settings: Settings = get_settings()
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt