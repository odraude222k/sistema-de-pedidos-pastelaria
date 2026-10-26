import argparse
from getpass import getpass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.admin.models import AdminUser
from app.core.security import hash_password
from app.database import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria um usuário administrativo")
    parser.add_argument("username", help="Nome de usuário do administrador")
    args = parser.parse_args()
    username = args.username.strip().lower()
    password = getpass("Senha: ")
    confirmation = getpass("Confirme a senha: ")

    if password != confirmation:
        raise SystemExit("As senhas não coincidem.")

    with SessionLocal() as db:
        if db.scalar(select(AdminUser.id).where(AdminUser.username == username)):
            raise SystemExit("Já existe um administrador com esse nome de usuário.")
        try:
            db.add(AdminUser(username=username, password_hash=hash_password(password)))
            db.commit()
        except (ValueError, IntegrityError) as exc:
            db.rollback()
            raise SystemExit(str(exc)) from exc

    print(f"Administrador '{username}' criado com sucesso.")


if __name__ == "__main__":
    main()
