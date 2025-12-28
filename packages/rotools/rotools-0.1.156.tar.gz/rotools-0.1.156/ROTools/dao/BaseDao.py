
_base = None

def get_rotools_base():
    global _base

    if _base:
        return _base

    from sqlalchemy.orm import declarative_base
    _base = declarative_base()
    return _base

class BaseDao(get_rotools_base()):
     __abstract__ = True