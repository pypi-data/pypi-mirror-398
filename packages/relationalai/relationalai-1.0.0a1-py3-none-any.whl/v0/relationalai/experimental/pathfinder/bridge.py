from typing import Callable


from v0.relationalai.dsl import Type, Symbol, create_vars, create_var, next_id, global_ns
from v0.relationalai.std import rel
from v0.relationalai.debugging import logger

from v0.relationalai.experimental.pathfinder.rpq import RPQ
from v0.relationalai.experimental.pathfinder.utils import get_model
from v0.relationalai.experimental.pathfinder.datalog import install_program
from v0.relationalai.experimental.pathfinder.compiler import (
    compile_conn, compile_product_graph
)
from v0.relationalai.experimental.pathfinder.api import (
    make_config_relation, make_input_relation
)

import importlib.resources as pkg_resources

# Dictionary to keep track of models with Pathfinder already installed
PATHFINDER_INSTALLED = {}

# -----------------------------------------------------------------------------------------
# Installing the Pathfinder source code
# -----------------------------------------------------------------------------------------
# Whilst the Package manager is not yet available, the Pathfinder is installed from manually
# prepared single source file (present in the current directory). Ideally, we want to use a
# single version but for comparative benchmarking and potential bug fixes we ensure that
# multiple versions can be installed and used.
# ----------------------------------------------------------------------------------------
def ensure_pathfinder_installed(model, options) -> str:

    pathfinder_lib_version = options['pathfinder_lib_version']

    key = (model.name, pathfinder_lib_version)

    if not PATHFINDER_INSTALLED.get(key, False):
        source = get_pathfinder_source_code(pathfinder_lib_version)

        logger.info(f'Installing Pathfinder source version {pathfinder_lib_version}')

        module_name = f"pathfinder_v{pathfinder_lib_version.replace('.', '_')}"

        # replace `pathfinder` with versioned module name in Rel source:
        import re
        source = re.sub(r'\bpathfinder\b', module_name, source)

        model.install_raw(source, name=module_name, overwrite=True)
        PATHFINDER_INSTALLED[key] = module_name

    return PATHFINDER_INSTALLED[key]

def get_pathfinder_source_code(version):
    try:
        resource_name = f"pathfinder-v{version}.rel"
        with pkg_resources.open_text('relationalai.experimental.pathfinder', resource_name) as file:
            return file.read()
    except FileNotFoundError:
        raise Exception("Pathfinder source file not found.")

# -----------------------------------------------------------------------------------------
# Pathfinder invocation
# -----------------------------------------------------------------------------------------
# The invocation of pathfinder consists of installing the logic and calling the appropriate
# method of the `pathfinder` module. The invocation is parameterized by various input
# options.
# -----------------------------------------------------------------------------------------
# The main entry point for invoking the pathfinder i.e., installing the logic for
# constructing the paths (if not does already). Returns the dedicated Path type containing
# all paths matching the input compiled pattern, as controlled by the options.
# ----------------------------------------------------------------------------------------
def invoke_pathfinder(pattern: RPQ, options):
    logger.info("Invoking pathfinder with options:")
    for option in options:
        logger.info(f" * {option}: {options[option]}")

    model = get_model(options)
    # make sure pathfinder is installed
    pathfinder_module = ensure_pathfinder_installed(model, options)
    pathfinder = getattr(global_ns, pathfinder_module)

    # use a unique identifier for all compiled types and relations
    pq_id = next_id()
    # source and target relations
    source_rel = f"pq_source_{pq_id}"
    source = getattr(rel, source_rel)
    target_rel = f"pq_target_{pq_id}"
    target = getattr(rel, target_rel)

    # use the connectivity relation to find the source or target nodes unless specified
    conn = None
    if options['source'] is None or options['target'] is None:
        conn_program = compile_conn(pattern, options)
        conn_rel = conn_program.root_rel['conn_rel']
        # connectivity relation
        conn = getattr(rel, conn_rel)
        # installing connectivity pattern rules
        install_program(model, conn_program, {**options, 'suppress_groundedness_test': True})

    define_endpoint_relations(source, target, model, conn, options)

    pg_program = compile_product_graph(pattern, source_rel, target_rel, options)
    pg_graph_rel = pg_program.root_rel['pg_graph_rel']
    pg_source_rel = pg_program.root_rel['pg_source_rel']
    pg_target_rel = pg_program.root_rel['pg_target_rel']
    edge_label_map = pg_program.edge_label_map
    pg_graph = getattr(rel, pg_graph_rel)
    pg_source = getattr(rel, pg_source_rel)
    pg_target = getattr(rel, pg_target_rel)
    install_program(model, pg_program, options)

    # output types
    Path = model.Type(f"Path{pq_id}")
    PathPosition = model.Type(f"PathPosition{pq_id}")
    PathEdge = model.Type(f"PathEdge{pq_id}")
    PathEdgeLabelMap = model.Type(f"PathEdgeLabelMap{pq_id}")

    # creating edge label map
    define_edge_label_mapping(model, edge_label_map, PathEdgeLabelMap, options)

    input_relation = make_input_relation(model, pg_graph, pg_source, pg_target)
    config_relation = make_config_relation(model, options)
    with model.rule(dynamic=True):
        path_id, kind, index, value = create_vars(4)
        pathfinder.find_paths(
            input_relation,
            config_relation,
            path_id,
            kind,
            index,
            value
        )

        path = Path.add(path_id=path_id)

        map_path_positions(PathPosition, path, kind, index, value)

        map_edge_labels(PathEdgeLabelMap, PathEdge, path, edge_label_map, kind, index, value)

    connect_edge_positions(model, Path, PathEdge, PathPosition)

    return Path()

def map_path_positions(PathPosition, path, kind, index, value):
    with kind == Symbol("node"):
        pos = PathPosition.add(path=path, index=index)
        pos.set(node=value)
        path.position.add(pos)

def map_edge_labels(PathEdgeLabelMap, PathEdge, path, edge_label_map, kind, index, value):
    if len(edge_label_map) != 0:
        with kind == Symbol("edge_label"):
            lab = PathEdgeLabelMap(pq_edge_label=value)
            edge = PathEdge.add(path=path, index=index)
            edge.set(label=lab.label, direction=lab.direction, property=lab.property)
            path.edge.add(edge)

def connect_edge_positions(model, Path, PathEdge, PathPosition):
    with model.rule():
        path = Path()
        e = PathEdge(path=path)
        from_pos = PathPosition(path=path, index=e.index-1)
        to_pos = PathPosition(path=path, index=e.index)
        e.set(from_node=from_pos.node, to_node=to_pos.node)

def define_endpoint_relations(source, target, model, conn, options):
    if options['source'] is None and options['target'] is None:
        assert conn is not None
        with model.rule():
            x, y = create_vars(2)
            conn(x, y)
            source.add(x)
            target.add(y)
        return

    assert options['source'] is not None or options['target'] is not None

    if options['source'] is not None:
         define_relation_from_spec(source, options['source'], model)

    if options['target'] is not None:
        define_relation_from_spec(target, options['target'], model)

    if options['source'] is None:
        define_relation_with_conn(source, 'backward', conn, target, model)

    if options['target'] is None:
        define_relation_with_conn(target, 'forward', conn, source, model)


def define_relation_from_spec(relation, relation_spec, model):
    if isinstance(relation_spec, Type):
        with model.rule():
            x = relation_spec()
            relation.add(x)
    else:
        assert isinstance(relation_spec, Callable)
        with model.rule():
            x = create_var()
            relation_spec(x)
            relation.add(x)

def define_relation_with_conn(relation, direction, conn, opposite_relation, model):
    assert conn is not None

    with model.rule(dynamic=True):
        x, y = create_vars(2)
        conn(x, y)
        if direction == 'forward':
            opposite_relation(x)
            relation.add(y)
        else:
            opposite_relation(y)
            relation.add(x)

def define_edge_label_mapping(model, edge_label_map, PathEdgeLabelMap, options):
    if len(edge_label_map) == 0:
        return
    with model.rule(dynamic=True):
        for pq_edge_label in edge_label_map:
            edge_label = edge_label_map[pq_edge_label]
            label = str(edge_label)
            property = edge_label.label
            direction = edge_label.direction
            label_map = PathEdgeLabelMap.add(pq_edge_label=pq_edge_label)
            label_map.set(label=label, direction=direction, property=property)
