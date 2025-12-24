
TOP_LEVEL_PROFILE_NAME = "__top_level__"
PARTIAL_PROFILE_NAME = "__partial__"
DEFAULT_PROFILE_NAME = "default"

#region Spans

# For a given span_type, the keys that are allowed to be inserted in the span's attrs
SPAN_ATTR_ALLOW_LIST = {
    'transaction': {'txn_id'},
    'wait': {'txn_id'},
    'program': {'pyrel_program_id'},
}

# Don't insert these as attrs since they get their own columns
SPAN_FILTER_ATTRS = {
    "event",
    "span",
    "id",
    "parent_id",
    "start_time",
    "start_timestamp",
    "end_time",
    "end_timestamp",
    "elapsed",
}

# For a given span type, the attribute to use as its key.
SPAN_TYPES_KEYS = {
    'test': 'name',
    'benchmark': 'name',
    'run': 'idx',
    'query': 'tag',
    'test_session': 'platform', # 'platform' is how the cloud_provider is stored in the config
    'get_model': 'name',
    'rule': 'name',
}

#endregion
