from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, registry

from gt.auth import Auth
from gt.organizations import Organizations


def _make_base():
    class Base(DeclarativeBase):
        registry = registry()

    return Base


def _build(prefix):
    base = _make_base()
    auth = Auth(base=base, session_factory=async_sessionmaker[AsyncSession]())
    organizations = Organizations(
        base=base,
        session_factory=async_sessionmaker[AsyncSession](),
        user_model=auth.user_model,
    )

    app = FastAPI()
    auth.init_app(app, prefix=prefix)
    organizations.init_app(app, prefix=prefix)
    return app


class TestInitAppPrefix:
    def test_default_routes(self):
        paths = set(_build(prefix=None).openapi()["paths"])

        assert "/auth/login" in paths
        assert "/auth/register" in paths
        assert "/organizations/" in paths

    def test_prefixed_routes(self):
        paths = set(_build(prefix="/api/v1").openapi()["paths"])

        assert "/api/v1/auth/login" in paths
        assert "/api/v1/auth/register" in paths
        assert "/api/v1/organizations/" in paths
        assert all(p.startswith("/api/v1/") for p in paths if "auth" in p)
