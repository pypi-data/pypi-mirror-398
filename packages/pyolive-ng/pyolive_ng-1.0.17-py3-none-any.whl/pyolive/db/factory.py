from .mysql import MySQLDatabase
from .postgres import PostgreSQLDatabase
from pyolive.config import Config


async def get_database(section: str = "systemdb"):
    config = Config("athena-db.yaml")
    db_cfg = config.get_value(section)

    vendor = db_cfg.get("vendor", "").lower()
    host = db_cfg.get("hosts", ["localhost"])[0]
    port = db_cfg.get("port", 5432 if vendor == "postgresql" else 3306)
    user = db_cfg.get("username")
    password = db_cfg.get("password")
    database = db_cfg.get("database")

    if vendor in ["mysql", "mariadb"]:
        db = MySQLDatabase(
            host=host,
            port=port,
            user=user,
            password=password,
            db=database,
            autocommit=True
        )
    elif vendor == "postgresql":
        db = PostgreSQLDatabase(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
    else:
        raise ValueError(f"Unsupported async DB vendor: {vendor}")

    await db.connect()
    return db