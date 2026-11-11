import secrets, hashlib, hmac
from datetime import datetime,timezone,timedelta
from typing import NamedTuple
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from .db import get_db
from .models import User, Session as LoginSession,LoginAttempt
from .config import SESSION_HOURS,COOKIE_SECURE,COOKIE_SAMESITE,ALLOWED_ORIGINS

hasher=PasswordHasher()
# Hash fictício, para uma verificação com custo semelhante se o usuário não existir.
DUMMY_HASH=hasher.hash('senha-invalida-do-usuario-inexistente')

def utcnow(): return datetime.now(timezone.utc)

def as_utc(value:datetime)->datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

def sha(v:str): return hashlib.sha256(v.encode()).hexdigest()

class Auth(NamedTuple):
    user:User
    session:LoginSession

def auth_required(request:Request, db:Session=Depends(get_db))->Auth:
    token=request.cookies.get('alice_session')
    if not token:
        raise HTTPException(401,'Sessão necessária')
    record=db.scalar(select(LoginSession).where(LoginSession.token_hash==sha(token)))
    if not record or as_utc(record.expires_at) <= utcnow():
        raise HTTPException(401,'Sessão expirada')
    user=db.get(User,record.user_id)
    if user is None or user.username != 'alicefoufa':
        raise HTTPException(401,'Sessão inválida')
    return Auth(user,record)

def csrf_required(request:Request, auth:Auth=Depends(auth_required)) -> Auth:
    provided=request.headers.get('X-CSRF-Token','')
    if not provided or not hmac.compare_digest(provided,auth.session.csrf_token):
        raise HTTPException(403,'Token CSRF ausente ou inválido')
    validate_origin(request)
    return auth

def validate_origin(request:Request):
    origin=request.headers.get('origin')
    if origin and origin.rstrip('/') not in ALLOWED_ORIGINS:
        raise HTTPException(403,'Origem não permitida')

def set_session_cookie(response,token):
    response.set_cookie('alice_session',token,max_age=SESSION_HOURS*3600,path='/api',httponly=True,secure=COOKIE_SECURE,samesite=COOKIE_SAMESITE)

def clear_session_cookie(response):
    response.delete_cookie('alice_session',path='/api',httponly=True,secure=COOKIE_SECURE,samesite=COOKIE_SAMESITE)

def client_ip(request:Request):
    return request.client.host if request.client else 'unknown'

def ensure_not_limited(db:Session,ip:str):
    start=utcnow()-timedelta(minutes=15)
    identifier=sha(ip)
    # Banco compartilhado entre instâncias; registros antigos são limpos em login.
    db.query(LoginAttempt).filter(LoginAttempt.created_at < start).delete(synchronize_session=False)
    db.commit()
    failed=db.scalars(select(LoginAttempt).where(LoginAttempt.ip_hash==identifier,LoginAttempt.created_at>=start)).all()
    if len(failed)>=5:
        raise HTTPException(429,'Muitas tentativas. Tente novamente mais tarde.',headers={'Retry-After':'900'})

def add_failed_attempt(db:Session,ip:str):
    db.add(LoginAttempt(ip_hash=sha(ip)))
    db.commit()

def clear_failed_attempts(db:Session,ip:str):
    db.query(LoginAttempt).filter(LoginAttempt.ip_hash==sha(ip)).delete(synchronize_session=False)
    db.commit()
