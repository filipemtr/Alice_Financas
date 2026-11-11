"""Ferramenta administrativa: altera a senha única sem armazená-la no terminal/histórico."""
import getpass
from sqlalchemy import select
from argon2 import PasswordHasher
from .db import SessionLocal
from .models import User, Session as LoginSession

def main():
    print('Alteração local de senha da conta alicefoufa')
    first=getpass.getpass('Nova senha (mínimo 12 caracteres): ')
    second=getpass.getpass('Confirme: ')
    if len(first)<12 or first!=second:raise SystemExit('Senhas diferentes ou com menos de 12 caracteres.')
    with SessionLocal() as db:
        account=db.scalar(select(User).where(User.username=='alicefoufa'))
        if account is None:raise SystemExit('Conta não encontrada; inicialize primeiro.')
        account.password_hash=PasswordHasher().hash(first)
        db.query(LoginSession).filter(LoginSession.user_id==account.id).delete(synchronize_session=False)
        db.commit()
    print('Senha substituída e sessões revogadas. Atualize também INITIAL_PASSWORD no ambiente ou remova-o após o seed.')
if __name__=='__main__':main()
