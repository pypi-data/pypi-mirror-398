from ..imports import os,yaml,safe_read_from_json
def get_abs_path():
    return os.path.abspath(__file__)
def get_abs_dir():
    abs_path = get_abs_path()
    abs_dir = os.path.dirname(abs_path)
    return abs_dir
def get_abs_parent_dir():
    abs_dir = get_abs_dir()
    abs_parent_dir = os.path.dirname(abs_dir)
    return abs_parent_dir
def get_query_utils_dir():
    abs_parent_dir = get_abs_parent_dir()
    query_utils_dir = os.path.dirname(abs_parent_dir)
    return query_utils_dir
def get_queries_dir():
    query_utils_dir = get_query_utils_dir()
    queries_dir = os.path.join(query_utils_dir,'queries')
    return queries_dir
def get_yaml_queries_path():
    queries_dir = get_queries_dir()
    yaml_queries_path = os.path.join(queries_dir,'queries.yaml')
    return yaml_queries_path
def get_queries_json_dir():
    queries_dir = get_queries_dir()
    json_queries_dir = os.path.join(queries_dir,'json_queries')
    return json_queries_dir
def get_json_queries_path(basename):
    queries_json_dir = get_queries_json_dir()
    json_queries_path = os.path.join(queries_json_dir,basename)
    return json_queries_path
def get_json_queries_data(basename):
    json_queries_path = get_json_queries_path(basename)
    data = safe_read_from_json(user_queries_path)
    return data
def get_yaml_queries_data(data_type):
    """Load blacklist queries from the YAML file."""
    yaml_path =get_yaml_queries_path()
    try:
        with open(yaml_path, 'r') as file:
            data = yaml.safe_load(file)
            return data.get(data_type, data)
    except Exception as e:
        print(f"Error loading YAML file {yaml_path}: {e}")
        return {}
