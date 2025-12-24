from relationalai.semantics.frontend.base import Field, Library

library = Library("lqp")

Symbol = library.Type("Symbol")

export = library.Relation("export", [])
external = library.Relation("external", [])
from_cdc = library.Relation("from_cdc", [])
adhoc = library.Relation("adhoc", [])
track = library.Relation("track", [Field.input("library", Symbol), Field.input("relation", Symbol)])