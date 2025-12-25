from pymilvus import FieldSchema, DataType

default_fields = [
    FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="uid", dtype=DataType.VARCHAR, max_length=36),
    FieldSchema(name="owner_uid", dtype=DataType.VARCHAR, max_length=64),
    FieldSchema(name="vectors", dtype=DataType.FLOAT_VECTOR, dim=1024),
]
default_output_fields = ['pk', 'uid', 'owner_uid']
default_search_field = "vectors"
default_query_fields = ['uid', 'owner_uid']

default_index_params_vector = {
    'metric_type': 'COSINE',  # IP 或 COSINE
    'index_type': 'FLAT',  # FLAT
    "params": {"nlist": 128},
}

default_index_params_auto = {
    'index_type': 'AUTOINDEX'
}

default_search_params = {
    'metric_type': 'COSINE',
    "params": {"nprobe": 10},
}
