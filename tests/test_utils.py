from app.lib.utils import generate_uuid, create_access_token

def test_create_access_token():
    data = {"user_id": "12345"}
    token = create_access_token(data)
    assert isinstance(token, str)

def test_uuid_generation():
    uuid1 = generate_uuid()
    uuid2 = generate_uuid()
    
    assert isinstance(uuid1, str)
    assert isinstance(uuid2, str)
    assert len(uuid1) == 36
    assert len(uuid2) == 36
    assert uuid1 != uuid2 