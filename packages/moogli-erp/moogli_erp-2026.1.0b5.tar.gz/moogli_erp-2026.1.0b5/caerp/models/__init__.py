"""
    Regouping all models imports is necessary
    to allow the metadata.create_all function to work well
"""
from caerp.models.base import DBBASE  # noqa: F401


def adjust_for_engine(engine):
    """
    Ajust the models definitions to fit the current database engine
    :param obj engine: The current engine to be used
    """
    from caerp.models.user import login

    if engine.dialect.name == "mysql":
        # Mysql does case unsensitive comparison by default
        login.Login.__table__.c.login.type.collation = "utf8mb4_bin"
