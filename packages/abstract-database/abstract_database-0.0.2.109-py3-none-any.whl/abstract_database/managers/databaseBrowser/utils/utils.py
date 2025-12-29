from ..imports import Column
def get_all_key_values(data, parent_key='', sep='_'):
    items = {}
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(get_all_key_values(value, new_key, sep=sep))
        else:
            items[new_key] = value
    return items

def get_type_change_list():
    return ["String", "Integer", "Float", "JSON"]

def create_class_from_dict(class_name, class_dict, base):
    attributes = {
        '__tablename__': class_name.lower(),
        'id': Column(Integer, primary_key=True, autoincrement=True)
    }
    unique_keys = class_dict.get('unique_keys', [])

    def handle_nested(col_name, col_type):
        if isinstance(col_type, dict):
            return Column(JSON)
        elif isinstance(col_type, list):
            return Column(JSON)
        else:
            raise ValueError(f"Unsupported column type: {col_type}")

    for col_name, col_type in class_dict['valueKeys'].items():
        if col_type == "TEXT":
            col = Column(String)
        elif col_type == "INTEGER":
            col = Column(Integer)
        elif col_type == "FLOAT" or col_type == "REAL":
            col = Column(Float)
        elif col_type == "JSON" or col_type == "ARRAY":
            col = Column(JSON)
        elif col_type == "BOOL":
            col = Column(Boolean)
        elif isinstance(col_type, dict) or isinstance(col_type, list):
            col = handle_nested(col_name, col_type)
        else:
            raise ValueError(f"Unsupported column type: {col_type}")

        attributes[col_name] = col

        if col_name in unique_keys:
            attributes[f'ix_{col_name}'] = Index(f'ix_{class_name.lower()}_{col_name}', col, unique=True)

    return type(class_name, (base,), attributes)

# Generic function to check if a record exists
def record_exists(session, model, **kwargs):
    query = session.query(model)
    for key, value in kwargs.items():
        query = query.filter(getattr(model, key) == value)
    return query.first() is not None
