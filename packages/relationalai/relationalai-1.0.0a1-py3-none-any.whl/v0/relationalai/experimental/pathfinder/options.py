from v0.relationalai.experimental.pathfinder.diagnostics import PathfinderParameterWarning
from v0.relationalai.debugging import warn, logger
from typing import Callable
from v0.relationalai.dsl import Instance, Type, Graph


# ----------------------------------------------------------------------------------------
# Options controlling the execution of the Pathfinder PyRel integration
# ----------------------------------------------------------------------------------------
#
# The options used to control the execution of the Pathfinder PyRel integration are stored
# in a simple dictionary mapping strings to values (typically string, ints, and Booleans).
# For a streamline use, this dictionary will be a total mapping from the set of all
# possible options, with `None` used if the given option is not applicable (e.g., the number
# of paths to compute is only specified when the LIMIT selector is to be used).
#
# The options are:
# ## Pathfinder Rel config values
# * `graph_type` ∈ {'labeled', 'unlabeled'} (currently, only 'labeled' is supported).
# * `semantics` ∈ {'shortest_paths', 'walks'}.
# * `max_path_length`: Optional[int]; the maximum length of the paths when `semantics` is
#   'walks'; otherwise None.
# * `group` ∈ {'for_any' , 'for_each_source'}
# * `selector` ∈ {'all', 'single', 'limit'}
# * `path_count`: Optional[int]; the number of paths to return when `selector` is 'limit';
#   otherwise None
# * `search_strategy` ∈ {'from_source', 'from_target', 'from_both_sides'} graph exploration
#   strategy (default is 'from_both_sides');
# * `search_radius` ∈ {'unbounded', 'bounded'} toggle indicating whether graph exploration
#   should span the whole graph or stop whenever a target node is found (default is
#   'bounded');
# ## Optional input arguments
# * `source`: Optional[Type] or Optional[Callable]; optional specification of the source
#   node relation; by default (projection of) the connectivity relation is used to identify
#   potential sources.
# * `target`: Optional[Type] or Optional[Callable]; optional specification of the target
#   node relation; by default (projection of) the connectivity relation is used to identify
#   potential targets.
# * 'pathfinder_lib_version': str; the version of the Pathfinder library to use.
#    (default "0.7.0")
## Integration control options
# * `force_transition_pruning`: bool; if True, the automaton transition pruning is forced;
#   otherwise, pruning happens only if the size is not too big (<50).
# * `suppress_groundedness_test`: bool; if True, we do not raise an error when the input
#   automaton is ungrounded; default is False.
# * `model`: Optional[Graph]; the model to use for emitting the rules. If None, the
#   a default model is retrieved from the model stack (see utils.get_model).
#

DEFAULT_OPTIONS = {
    'graph_type': 'labeled',
    'semantics': 'shortest_paths',
    'max_path_length': None,
    'group': 'for_any',
    'selector': 'all',
    'path_count': None,
    'search_strategy': 'from_both_sides',
    'search_radius': 'bounded',
    'source': None,
    'target': None,
    'pathfinder_lib_version': '0.7.0',
    'force_transition_pruning': False,
    'suppress_groundedness_test': False,
    'model' : None
}


# -----------------------------------------------------------------------------------------
# The user-facing PyRel pathfinder functions, `find_paths` and `conn`, accept the following
# keyword _params_:
# * `max_path_length`: Optional[int] (default: None); the maximum length of the paths to be
#   computed. If max_path_length os None, the shortest paths are computed only.
# * `limit`: Optional[int] (default: None); whether all paths should be returned (None) or
#   only the first k paths.
# * `from_source` and `from_target`: Optional[bool] (default: False); whether the search
#   should be done from the source nodes or target nodes respectively. Only one of
#   `from_source` and `from_target` can be set to True. If both are False, the search is
#   done from both sides.
# * `for_each_source`: Optional[bool] (default: False); whether the search should be done
#   for each source node separately. If False, the search is done for any pair of source and
#   target nodes. This option is only supported for the shortest path semantics; When walks
#   semantics is selected (by using `max_path_length`), this option is ignored.
# * `unbounded`: Optional[bool] (default: False); whether the search should be
#   unbounded or bounded.
# * `source`: Optional[Type] or Optional[Callable]; the source node relation specification.
# * `target`: Optional[Type] or Optional[Callable]; the target node relation specification.
# * `force_transition_pruning`: Optional[bool] (default: False); whether the FA transition
#   pruning should be forced if the FA is too big (>50 states).
# * `suppress_groundedness_test`: bool; if True, we will not raises an error when the input
#   automaton is ungrounded; default is False.
# * `pathfinder_lib_version`: str; the version of the Pathfinder library to use.
#   (default "0.7.0")
# ----------------------------------------------------------------------------------------

PARAM_NAMES = [
    'max_path_length',
    'limit',
    'from_source',
    'from_target',
    'for_each_source',
    'unbounded',
    'source',
    'target',
    'force_transition_pruning',
    'suppress_groundedness_test',
    'pathfinder_lib_version'
]


def normalized_options(params):

    logger.info("Normalizing parameters...")
    for k, v in params.items():
        logger.info(f"  {k}: {v}")
        if k not in PARAM_NAMES:
            warn(PathfinderParameterWarning(
                f"Unknown parameter '{k}' ignored."
            ))

    # pathfinder_lib_version (grab)
    pathfinder_lib_version = params.get('pathfinder_lib_version',
                                        DEFAULT_OPTIONS['pathfinder_lib_version'])
    assert pathfinder_lib_version in ["0.7.0"], "`pathfinder_lib_version` parameter is an invalid library version"

    # graph_type
    graph_type = "labeled"

    # max_path_length (grab)
    max_path_length = None
    if 'max_path_length' in params:
        max_path_length = params['max_path_length']
        if not isinstance(max_path_length, Instance):
            assert type(max_path_length) is int and max_path_length >= 0, "`max_path_length` parameter must be a non-negative integer"


    # semantics (grab)
    if max_path_length is None:
        semantics = 'shortest_paths'
    else:
        semantics = 'walks'

    # path_count (grab)
    path_count = None
    if 'limit' in params:
        path_count = params['limit']
        if not isinstance(path_count, Instance):
            assert type(path_count) is int and path_count > 0, "`limit` parameter must be a positive integer"


    # selector (grab)
    if path_count is None:
        selector = 'all'
    elif path_count == 1:
        selector = 'single'
    else:
        selector = "limit"


    # group (grab)
    group = 'any_pair'
    assert 'for_each_source' not in params or type(params['for_each_source']) is bool, "`for_each_source` parameter must be a boolean"
    if 'for_each_source' in params and params['for_each_source']:
        group = 'for_each_source'
    # group (check)
    if group == 'for_each_source' and semantics == 'walks':
        warn(PathfinderParameterWarning(
            "The option `for_each_source=True` is ignored when "
            "the option `max_path_length` is used."
        ))
        group = 'any_pair'
    if group == 'for_each_source' and selector in ['single', 'limit']:
        warn(PathfinderParameterWarning(
            "The option `for_each_source=True` is ignored when "
            "the option `limit` is used."
        ))
        group = 'any_pair'


    # search_strategy (grab)
    search_strategy = 'from_both_sides'
    assert 'from_source' not in params or type(params['from_source']) is bool, "`from_source` parameter must be a boolean"
    assert 'from_target' not in params or type(params['from_target']) is bool, "`from_target` parameter must be a boolean"
    if 'from_source' in params and params['from_source']:
        search_strategy = 'from_source'
    elif 'from_target' in params and params['from_target']:
        search_strategy = 'from_target'
    # search_strategy (check)
    if group == 'for_each_source' and search_strategy != 'from_source':
        warn(PathfinderParameterWarning(
            "The parameter `for_each_source=True` forces the parameter `from_source=True`. "
            "Parameters selecting other search strategy, like `from_target=True`, are ignored."
        ))
        search_strategy = 'from_source'
    if (group == 'any_pair' and search_strategy == 'from_source' and
        'from_target' in params and params['from_target']):
        warn(PathfinderParameterWarning(
            "The parameter `from_source=True` supersedes the parameter `from_target=True`. "
            "The parameter `from_target=True` is ignored."
        ))


    # search_radius (grab)
    search_radius = 'bounded'
    assert 'unbounded' not in params or type(params['unbounded']) is bool, "`unbounded` parameter must be a boolean"
    if 'unbounded' in params and params['unbounded']:
        search_radius = 'unbounded'
    # search_radius (check)
    if search_radius == 'unbounded' and semantics == 'walks':
        warn(PathfinderParameterWarning(
            "The parameter `unbounded=True` is ignored when "
            "the parameter `max_path_length` is used."
        ))
        search_radius = 'bounded'
    if search_radius == 'unbounded' and search_strategy == 'from_both_sides':
        warn(PathfinderParameterWarning(
            "The parameter `unbounded=True` has effect only when used with one of the parameters "
            "`from_source=True` or `from_target=True; The parameter `unbounded=True` is ignored."
        ))
        search_radius = 'bounded'


    # source and target (grab)
    source = params.get("source", None)
    target = params.get("target", None)
    # source and target (check)
    if source is not None and not isinstance(source, (Type, Callable)):
        warn(PathfinderParameterWarning(
            "Ignoring parameter `source`: must be a Type or a function"
        ))
        source, target = None, None

    if target is not None and not isinstance(target, (Type, Callable)):
        warn(PathfinderParameterWarning(
            "Ignoring parameter `source`: must be a Type or a lambda expression"
        ))
        source, target = None, None

    # force_transition_pruning (grab)
    force_transition_pruning = params.get("force_transition_pruning", False)
    assert type(force_transition_pruning) is bool, "`force_transition_pruning` parameter must be a boolean"

    # suppress_groundedness_test (grab)
    suppress_groundedness_test = params.get("suppress_groundedness_test", False)
    assert type(suppress_groundedness_test) is bool, "`suppress_groundedness_test` parameter must be a boolean"

    # model (grab)
    model = params.get("model", None)
    assert model is None or isinstance(model, Graph), "`model` parameter must be a Graph instance"

    return {
        'graph_type': graph_type,
        'semantics': semantics,
        'group': group,
        'selector': selector,
        'search_strategy': search_strategy,
        'search_radius': search_radius,
        'source': source,
        'target': target,
        'max_path_length': max_path_length,
        'path_count': path_count,
        'pathfinder_lib_version': pathfinder_lib_version,
        'force_transition_pruning': force_transition_pruning,
        'suppress_groundedness_test': suppress_groundedness_test,
        'model': model
    }
