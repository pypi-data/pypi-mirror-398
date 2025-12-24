from __future__ import annotations
from contextlib import contextmanager
import difflib
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import cast, Type

from v0.relationalai.clients.types import ImportSource, ImportSourceFile
from v0.relationalai.clients.client import ResourcesBase
from v0.relationalai.dsl import Context, Graph, Instance, RelationRef, Vars, create_var
from v0.relationalai.loaders.types import LoadType, UnsupportedTypeError
from v0.relationalai.metamodel import Builtins
from v0.relationalai.rel_emitter import sanitize
from v0.relationalai.rel_utils import assert_no_problems, process_gnf_results
from v0.relationalai.std import rel

#-------------------------------------------------------------------------------
# Schema Mapping
#-------------------------------------------------------------------------------

TYPE_TO_REL_SCHEMA = {
    Builtins.String: "string",
    Builtins.Int: "int",
    Builtins.Number: "float",
    Builtins.Bool: "boolean",
    Builtins.Decimal: "decimal" # @TODO: See if this works or requires manually specifying size
}

# @NOTE: This only works so long as the mapping is bidirectionally unambiguous
REL_SCHEMA_TO_TYPE = {v: k for k, v in TYPE_TO_REL_SCHEMA.items()}

def rel_schema_to_type(rel_type: str):
    try:
        return REL_SCHEMA_TO_TYPE[rel_type]
    except KeyError:
        raise Exception(f"Invalid schema field type '{rel_type}'. Available options are ({', '.join(REL_SCHEMA_TO_TYPE.keys())})")

#-------------------------------------------------------------------------------
# Hashing
#-------------------------------------------------------------------------------

def compute_file_hash(file_path:str|Path, chunk_size=16384):
    """Digest the given file to a content-addressable hash."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()

def compute_str_hash(content: str):
    """Digest the given string to a hash."""
    return hashlib.sha256(content.encode()).hexdigest()

#-------------------------------------------------------------------------------
# Resource Proxy
#-------------------------------------------------------------------------------

class ResourceProxy:
    """Represents a (optimistically-assumed to be present) resource relation, such as a CSV."""
    def __init__(self, graph: Graph, name: str, id: Instance|None = None):
        if id is None:
            id = create_var()

        self._graph = graph
        self._rel = getattr(rel, sanitize(name)) # @FIXME: This isn't necessarily the same as the relation name, gota do something about that.
        self._refs: dict[str, RelationRef] = {}
        self._id = cast(Instance, id)

    def __getattr__(self, attr: str):
        ref = self._refs.get(attr, None)
        if ref is not None:
            return ref

        rel = getattr(self._rel, attr)
        attr_var = Vars(1)
        rel(self._id, attr_var)
        return attr_var

# This could instead be a subclass of Context, it behaves exactly as if it was
# but doing so happened to be larger and (seemingly?) more brittle due to all the
# kwargs.
@contextmanager
def read_resource_context(graph: Graph, name: str, **kwargs):
    ctx = Context(graph, **kwargs)
    with ctx:
        yield ResourceProxy(graph, name)


#-------------------------------------------------------------------------------
# Loader
#-------------------------------------------------------------------------------

class Loader(ABC):
    """Base class for objects that handle the particulars of mapping an import source to a resource relation."""
    type: str = "untyped"

    @abstractmethod
    def load(self, provider: ResourcesBase, model: str, source: ImportSource):
        """Load a snapshot of the given source data into the given model."""
        ...

    @classmethod
    def register(cls):
        assert cls.type != "untyped", f"{cls.__name__} does not provide a type property."
        assert cls.type not in Loader.type_to_loader or Loader.type_to_loader[cls.type] == cls, f"{cls.__name__} has the same type '{cls.type}' as another loader ({Loader.type_to_loader[cls.type].__name__})."
        Loader.type_to_loader[cls.type] = cls

    @classmethod
    def register_for_extensions(cls, *exts: str):
        cls.register()
        for ext in exts:
            assert ext not in Loader.ext_to_type or Loader.ext_to_type[ext] == cls.type, f"{cls.__name__} registered to handle '{ext}' but another loader ({Loader.type_to_loader[cls.type].__name__}) already does."
            Loader.ext_to_type[ext] = cls.type

    ext_to_type: dict[str, LoadType] = {}

    @classmethod
    def get_type_for(cls, source: ImportSourceFile):
        try:
            return Loader.ext_to_type[source.extension]
        except KeyError:
            raise UnsupportedTypeError(f"No loader type provided for extension: '{source.extension}'. You can manually specify the loader to use via the `type` kwarg", source.extension)

    type_to_loader: dict[LoadType, 'Type[Loader]'] = {}
    @classmethod
    def get_loader_for_type(cls, type: LoadType):
       try:
           return Loader.type_to_loader[type]
       except KeyError:
           raise UnsupportedTypeError(f"No loader provided for type: '{type}'", type)

#-------------------------------------------------------------------------------
# Import Utilities
#-------------------------------------------------------------------------------

def import_file(provider: ResourcesBase, model: str, source: ImportSourceFile, type: LoadType = "auto", **metadata):
    """Automatically load `source` into `model` using the most appropriate loader."""
    if type == "auto":
        type = Loader.get_type_for(source)

    return Loader.get_loader_for_type(type)().load(provider, model, source, **metadata)

def emit_delete_import(name: str) -> str:
    """Utility fn for emitting the rel to delete the specified import relation and all its metadata."""
    relation = sanitize(name)
    return f"""
    declare {relation}
    def delete[:{relation}]: {relation}
    def delete[:__resource, k]: ("{name}", __resource[k, "{name}"])
    """

#-------------------------------------------------------------------------------
# Resource Management
#-------------------------------------------------------------------------------

available_resources:dict[str, dict] = {}

def list_available_resources(provider: ResourcesBase, database: str, engine: str):
    res = provider.exec_raw(database, engine, """
    declare __resource
    def output {{__resource}}
    """)
    assert_no_problems(res)

    available_resources = process_gnf_results(res.results, "name")
    return available_resources

class MissingResourceError(Exception):
    def __init__(self, name: str):
        similar_names = difflib.get_close_matches(name, available_resources.keys(), n=3)
        message = f"No available resource named '{name}'"
        if similar_names:
            message += ". Maybe you want one of these?"
            for name in similar_names:
                message += f"\n- {name}"
        super().__init__(message)
