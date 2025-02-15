from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash

from submission.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    active: Mapped[bool] = mapped_column(nullable=False, default=False)
    password_hash: Mapped[str] = mapped_column(nullable=False)

    roles: Mapped[list["Role"]] = db.relationship(
        "Role", secondary="auth.rel_user_roles", back_populates="users", lazy="selectin"
    )

    info: Mapped["UserInfo"] = db.relationship("UserInfo")

    @hybrid_property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password) -> bool:
        return check_password_hash(self.password, password)

    def has_role(self, role) -> bool:
        return bool(
            Role.query.join(Role.users)
            .filter(User.user_id == self.user_id)
            .filter(Role.name == role)
            .count()
            == 1
        )
    def get_id(self):
        return self.user_id


class Role(db.Model):
    __tablename__ = "roles"
    __table_args__ = {"schema": "auth"}

    role_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False, unique=True)

    users: Mapped[list["User"]] = db.relationship(
        "User", secondary="auth.rel_user_roles", back_populates="roles", lazy="selectin"
    )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Role('{self.name}', '{self.description}')"


class UserRole(db.Model):
    __tablename__ = "rel_user_roles"
    __table_args__ = {"schema": "auth"}

    user_id: Mapped[int] = mapped_column(db.ForeignKey("auth.users.user_id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(db.ForeignKey("auth.roles.role_id"), primary_key=True)


class UserInfo(db.Model):
    __tablename__ = "user_info"
    __table_args__ = {"schema": "auth"}

    user_id: Mapped[int] = mapped_column(db.ForeignKey("auth.users.user_id"), primary_key=True)
    alias: Mapped[str] = mapped_column(nullable=False, unique=True)
    name: Mapped[str] = mapped_column(nullable=False)
    call_name: Mapped[str] = mapped_column(nullable=False)
    organisation_1: Mapped[str] = mapped_column(nullable=False)
    organisation_2: Mapped[str] = mapped_column(nullable=True)
    organisation_3: Mapped[str] = mapped_column(nullable=True)
    orcid: Mapped[str] = mapped_column(nullable=True, unique=True)
    public: Mapped[bool] = mapped_column(nullable=False, default=False)

    @staticmethod
    def generate_alias(length: int = 15) -> str:
        import base64
        from random import randbytes
        token_bytes = randbytes(length)

        return base64.b32encode(token_bytes).decode("utf-8")

    @staticmethod
    def guess_call_name(name: str) -> str:
        return name.split(" ")[0]
