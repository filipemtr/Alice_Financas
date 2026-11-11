"""Criação controlada da única conta. Não altera a senha a cada inicialização."""
import os
from sqlalchemy import select
from argon2 import PasswordHasher
from .db import SessionLocal
from .models import User
from .config import USERNAME

def main():
    if os.getenv('INITIAL_USERNAME',USERNAME) != USERNAME:
        raise SystemExit('INITIAL_USERNAME deve ser alicefoufa')
    with SessionLocal() as db:
        user=db.scalar(select(User).where(User.username==USERNAME))
        if user:
            print('Conta já existe; senha não modificada.')
            return
        password=os.getenv('INITIAL_PASSWORD','')
        if len(password)<12: raise SystemExit('Configure INITIAL_PASSWORD com pelo menos 12 caracteres')
        if db.scalar(select(User.id)) is not None: raise SystemExit('Conta não autorizada encontrada; inicialização bloqueada')
        db.add(User(username=USERNAME,password_hash=PasswordHasher().hash(password)))
        db.commit()
        print('Conta única criada com hash Argon2id.')

if __name__=='__main__':main()
