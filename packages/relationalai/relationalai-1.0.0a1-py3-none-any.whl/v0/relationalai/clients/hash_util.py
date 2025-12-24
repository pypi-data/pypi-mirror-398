import hashlib

def hash_string(s: str, digits=32):
    return hashlib.md5(s.encode()).hexdigest()[:digits]

def database_name_from_sproc_name(sproc_name: str) -> str:
    # Import here to avoid circular import issues
    from v0.relationalai.clients.util import IdentityParser, ParseError
    from v0.relationalai.rel_utils import sanitize_identifier

    err_text = f"Invalid stored procedure name: {sproc_name}"
    try:
        parser = IdentityParser(sproc_name, require_all_parts=True)
        if not (parser.identity and parser.db and parser.schema and parser.entity):
            raise ValueError(err_text)

        # Remove all special characters from the name and replace with '_'
        sanitized_name = sanitize_identifier(parser.identity)
        hashed_sanitized_name = hash_string(sanitized_name)

        # If the name is less than 32 characters, append the hash of the name
        if len(sanitized_name) < 32:
            return f"{sanitized_name}_{hashed_sanitized_name}"

        # If the name is more than 32 characters, truncate it to 31 characters and sanitize each part
        truncated_database = sanitize_identifier(parser.db[:10])
        truncated_schema = sanitize_identifier(parser.schema[:10])
        truncated_proc = sanitize_identifier(parser.entity[:(31 - len(truncated_database) - len(truncated_schema))])
        return f"{truncated_database}_{truncated_schema}_{truncated_proc}_{hashed_sanitized_name}"
    except ParseError:
        raise ValueError(err_text)
