from contextlib import AbstractContextManager

import sqlalchemy.orm as sa_orm
from fastapi import HTTPException

__all__ = [
    "managed_db_session",
]


class DBSessionExceptionManager(AbstractContextManager):
    def __init__(self, db: sa_orm.Session, commit_on_exit: bool):
        self.db = db
        self.commit_on_exit = commit_on_exit

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if isinstance(exc_type, HTTPException):
            return False  # Propagate HTTPException
        if exc_type is not None:
            self.db.rollback()  # Raise a new HTTPException (or any other exception type)
            raise HTTPException(status_code=500, detail=str(exc_value)) from exc_value
        if self.commit_on_exit:
            self.db.commit()
        return True


def managed_db_session(db: sa_orm.Session, commit_on_exit: bool = True) -> DBSessionExceptionManager:
    return DBSessionExceptionManager(db, commit_on_exit)
