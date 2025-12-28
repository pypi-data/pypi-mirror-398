
def select_insert_check_many(session, obj_list, dao_class, filter_column_name, validate=False):
    if not isinstance(obj_list, list):
        raise Exception("obj_list must be a list")

    return [select_insert_check(session, a, dao_class, filter_column_name, validate) for a in obj_list]

def select_insert_check(session, new_obj, dao_class, filter_column_name=None, validate=False):
    _obj, was_inserted = _select_insert_check_impl(session, new_obj, dao_class, filter_column_name)

    if validate:
        session.flush()

    if validate and not was_inserted:
        new_obj.validate_compare(_obj)

    return _obj, was_inserted

def _select_insert_check_impl(session, obj, dao_class, filter_column_name):
    from sqlalchemy import select
    existing = False
    if filter_column_name:
        filter_value = getattr(obj, filter_column_name)
        dynamic_column = getattr(dao_class, filter_column_name)
        smt = select(dao_class).filter(dynamic_column == filter_value)
        existing = session.scalars(smt).one_or_none()

    if existing:
        return existing, False

    session.add(obj)
    return obj, True
