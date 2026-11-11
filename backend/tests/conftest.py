import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from argon2 import PasswordHasher
from app.db import Base, get_db
from app.models import User
from app.main import app

TEST_PASSWORD='senha-de-teste-nao-e-da-conta-real'

@pytest.fixture()
def client(tmp_path):
    engine=create_engine(f'sqlite:///{tmp_path / "test.db"}',connect_args={'check_same_thread':False})
    @event.listens_for(engine,'connect')
    def enable_foreign_keys(dbapi_connection,connection_record):
        cursor=dbapi_connection.cursor();cursor.execute('PRAGMA foreign_keys=ON');cursor.close()
    Base.metadata.create_all(engine)
    sessions=sessionmaker(bind=engine,expire_on_commit=False)
    with sessions() as db:
        db.add(User(username='alicefoufa',password_hash=PasswordHasher().hash(TEST_PASSWORD)))
        db.commit()
    def override_db():
        with sessions() as db:yield db
    app.dependency_overrides[get_db]=override_db
    with TestClient(app) as c:yield c
    app.dependency_overrides.clear()
    engine.dispose()

@pytest.fixture()
def logged(client):
    r=client.post('/api/auth/login',json={'username':'alicefoufa','password':TEST_PASSWORD})
    assert r.status_code==200,r.text
    return (client,{'X-CSRF-Token':r.json()['csrf_token']})
