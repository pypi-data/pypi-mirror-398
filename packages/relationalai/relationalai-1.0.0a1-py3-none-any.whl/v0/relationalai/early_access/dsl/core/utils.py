import logging
import uuid
import hashlib
import re


def generate_stable_uuid(name: str, salt: str="Ontology") -> str:
    # Create a stable namespace by hashing the salt
    namespace = uuid.UUID(hashlib.md5(salt.encode('utf-8')).hexdigest())
    # Generate the UUID using the namespace and name
    return str(uuid.uuid5(namespace, name))

def is_blank(value):
    # Check for None
    if value is None:
        return True
    # Check for empty strings or strings with only whitespace
    if isinstance(value, str) and value.strip() == "":
        return True
    return False

def get_values_from_keys(data, keys):
    return [data[key] for key in keys if key in data]

def camel_to_snake(name: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

def to_pascal_case(text: str) -> str:
    words = re.split(r'[\s_\-]+', text)  # Split on spaces, underscores, and hyphens
    return ''.join(capitalize_first(word) for word in words)

def capitalize_first(s):
    return s[0].upper() + s[1:] if s else s

def to_rai_way_string(verb_string: str, drop_prefix=True) -> str:
    canonical_name = verb_string.lower().strip()
    if drop_prefix:
        # removing 'has' and 'is' according to rai way
        canonical_name = re.sub(r'^(is|has)\b\s*', '', canonical_name)
        canonical_name = canonical_name.strip()
    # replace ' ' and '-' with '_'
    canonical_name = re.sub(r'[-\s]', '_', canonical_name)
    # drop subsequent '_'
    canonical_name = re.sub(r'_+', '_', canonical_name)
    # replace unsupported symbols with '_'
    new_name = re.sub(r'[^a-zA-Z0-9_-]', '_', canonical_name)
    if new_name != canonical_name:
        logging.warning(f"Verbalization string {verb_string} has unsupported symbols. Replacing them with '_'")
    return new_name