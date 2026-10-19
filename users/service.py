"""Lógica de negocio del recurso `users`.

Las rutas no acceden al repositorio directamente: pasan por aquí. Esta capa es la
única que conoce `repository.py` y la que decide cuándo algo es un error de
dominio (usando `core.errors`).
"""
from core import errors
from core.pagination import Page
from users import repository
from users.schemas import User, UserCreate


def get_user(user_id: int) -> User:
    user = repository.get(user_id)
    if user is None:
        raise errors.not_found("usuario", user_id)
    return user


def list_users(page: int, size: int) -> Page[User]:
    raise NotImplementedError


def create_user(data: UserCreate) -> User:
    if repository.find_by_email(str(data.email)) is not None:
        raise errors.already_exists("usuario", data.email)
    return repository.add(name=data.name, email=str(data.email))
