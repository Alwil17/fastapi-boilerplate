"""Create (or promote) an admin account.

    python -m app.jobs.create_admin admin@example.com

The password is read from ADMIN_PASSWORD or prompted; it is never taken from argv.
"""

import argparse
import getpass
import os
import sys

from app.core.roles import Role
from app.db.base import SessionLocal
from app.schemas.user_dto import UserCreateDTO
from app.services.user_service import UserService


def create_admin(email: str, password: str, name: str = "Admin") -> None:
    with SessionLocal() as db:
        service = UserService(db)
        data = UserCreateDTO(name=name, email=email, password=password)
        user = service.get_user_by_email(data.email)
        if user is None:
            user = service.create_user(data)
        user.role = Role.ADMIN
        db.commit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("email")
    parser.add_argument("--name", default="Admin")
    args = parser.parse_args(argv)

    password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Password: ")
    create_admin(args.email, password, args.name)
    print(f"Admin ready: {args.email.strip().lower()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
