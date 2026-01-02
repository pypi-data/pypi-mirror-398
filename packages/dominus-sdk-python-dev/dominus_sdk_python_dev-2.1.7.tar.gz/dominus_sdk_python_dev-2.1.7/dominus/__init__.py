"""
CB Dominus SDK - Ultra-flat async SDK for CareBridge Services

Ultra-Flat API:
    from dominus import dominus

    # Secrets (root level)
    value = await dominus.get("DB_URL")
    await dominus.upsert("KEY", "value")

    # Auth (root level)
    await dominus.add_user(username="john", password="secret", role_id="...")
    await dominus.add_scope(slug="read", display_name="Read", tenant_category_id=1)
    result = await dominus.verify_user_password(username="john", password="secret")

    # SQL data - app schema (root level)
    tables = await dominus.list_tables()
    rows = await dominus.query_table("users")
    await dominus.insert_row("users", {"name": "John"})

    # SQL data - secure schema (secure namespace)
    rows = await dominus.secure.query_table("patients")
    await dominus.secure.insert_row("patients", {"mrn": "12345"})

    # Schema DDL - app schema (root level)
    await dominus.add_table("users", [{"name": "id", "type": "UUID"}])

    # Schema DDL - secure schema (secure namespace)
    await dominus.secure.add_table("patients", [...])

    # Open DSN
    dsn = await dominus.open.dsn()

    # Health
    status = await dominus.health.check()

Backward Compatible String API:
    result = await dominus("secrets.get", key="DB_URL")
"""
from .start import dominus
from .helpers.core import DominusResponse

__version__ = "0.3.0"
__all__ = [
    "dominus",
    "DominusResponse",
]
