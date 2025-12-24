from v0.relationalai.dsl import Symbol, InlineRelation
from v0.relationalai.debugging import logger


#
# This is the schema of the `Config` relation required by the Pathfinder Rel library, in
# versions 0.7+.
#
CONFIG_SCHEMA = {
    "graph_type": {
        "type": "symbol",
        "enum": ["labeled"],
        "default": "labeled"
    },
    "semantics": {
        "type": "symbol",
        "enum": ["shortest_paths"],
        "default": "shortest_paths"
    },
    "group": {
        "type": "symbol",
        "enum": ["any_pair"],
        "default": "any_pair"
    },
    "selector": {
        "type": "symbol",
        "enum": ["all", "single", "limit"],
        "default": "all"
    },
    "path_count": {
        "type": int,
        "default": None
    },
    "max_path_length": {
        "type": int,
        "default": None
    },
    "random_seed": {
        "type": int,
        "default": None
    },
    "path_ids": {
        "type": "symbol",
        "enum": ["canonical", "non_canonical"],
        "default": "non_canonical"
    },
    "node_indexing": {
        "type": "symbol",
        "enum": ["zero_based", "one_based"],
        "default": "zero_based"
    },
    "edge_indexing": {
        "type": "symbol",
        "enum": ["zero_based", "one_based"],
        "default": "one_based"
    },
    "product_graph": {
        "type": "symbol",
        "enum": ["materialized", "non_materialized"],
        "default": "non_materialized"
    },
    "search_strategy": {
        "type": "symbol",
        "enum": ["from_both_sides", "from_source", "from_target"],
        "default": "from_both_sides"
    },
    "path_enum_partials": {
        "type": "symbol",
        "enum": ["dynamic", "static"],
        "default": "dynamic"
    },
    "search_start_nodes": {
        "type": "symbol",
        "enum": ["multiple", "unique"],
        "default": "multiple"
    },
    "search_radius": {
        "type": "symbol",
        "enum": ["unbounded", "bounded"],
        "default": "bounded"
    }
}

DEFAULT_CONFIG = {
    "graph_type": "labeled",
    "semantics": "shortest_paths",
    "group": "any_pair",
    "selector": "all",
    "path_ids": "non_canonical",
    "node_indexing": "zero_based",
    "edge_indexing": "one_based",
    "debug": "debug_off",
    "product_graph": "materialized",
    "search_strategy": "from_both_sides",
    "path_enum_partials": "dynamic",
    "search_start_nodes": "multiple",
    "search_radius": "bounded"
}

#
# Creates an inline relation with the content specified by the `contents` dict
# interpreted with the help of the `schema`.
#
def make_inline_relation(model, contents, schema):
    pairs = []
    for k, v in contents.items():
        if k not in schema:
            logger.info(f"Skipping unknown key {k} with value {v}")
            continue
        elif v is None:
            logger.info(f"Skipping key {k} with null value")
            continue
        elif schema[k]['type'] == 'symbol':
            assert isinstance(v, str), f"Expected a string for {k}, got {v} of type {type(v)}"
            pairs.append((Symbol(k), Symbol(v)))
        else:
            pairs.append((Symbol(k), v))


    logger.info(f"Creating inline relation with {len(pairs)} pairs:")
    for k, v in pairs:
        logger.info(f"  {k._var.value}: {v._var.value if isinstance(v, Symbol) else v}")

    return InlineRelation(model, pairs) # TAG: #pyrel

#
# Uses option values to creates an inlined `Config` relation with relevant configuration
# values for a call of `find_paths` in Pathfinder Rel library.
#
def make_config_relation(model, options):
    config = DEFAULT_CONFIG.copy()
    config.update(options)

    return make_inline_relation(model, config, CONFIG_SCHEMA)

INPUT_SCHEMA = {
    'pg_graph' :{
        'type': 'relation'
    },
    'pg_source': {
        'type': 'relation'
    },
    'pg_target': {
        'type': 'relation'
    }
}

#
# Creates an inline relation with `Input` relation specifying the path query in the form of
# a product graph.
#
def make_input_relation(model, pg_graph, pg_source, pg_target):

    d = {
        'pg_graph': pg_graph,
        'pg_source': pg_source,
        'pg_target': pg_target
    }

    return make_inline_relation(model, d, INPUT_SCHEMA)
