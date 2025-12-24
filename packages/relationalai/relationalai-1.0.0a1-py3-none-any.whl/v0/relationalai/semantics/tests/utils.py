from itertools import count
from v0.relationalai.semantics.metamodel import ir, types, util
from v0.relationalai.semantics.internal import internal as b
from v0.relationalai.semantics.snowflake import Table

def reset_state():
    """
    Reset global state for consistent test snapshots.

    When we execute a pyrel program we accumulate some state, such as custom decimals, and
    we increase the counter for object ids. This function resets those counters and other
    state to a known baseline to ensure that test snapshots are consistent if we run the
    test alone vs in a suite of tests.
    """
    # reset the global id counters
    ir._global_id = count(10000)
    b._global_id = count(10000)
    b._global_roots = util.ordered_set()

    # Used to generate error source IDs
    b.errors.ModelError.error_locations.clear()

    # reset the ErrorConcept state, so that Error.new() always generates the same IR
    b.ErrorConcept._error_props.clear()
    b.ErrorConcept._relation = None
    b.ErrorConcept._overloads.clear()

    # cleanup relationships declared on global concepts
    concepts_to_cleaanup = [b.Concept.builtins["Error"], b.Concept.builtins["Any"]]
    keep = ["shape", "builtins", "globals"]
    for concept in concepts_to_cleaanup:
        for attr in list(concept._relationships.keys()):
            if attr not in keep:
                del concept._relationships[attr]
        concept.globals.clear()

    # caches of custom decimals
    for k in list(types._decimal_types.keys()):
        if types._decimal_types[k] != types.Decimal:
            del types._decimal_types[k]
    for k in list(b.Concept.builtins):
        if k.startswith("Decimal(") and b.Concept.builtins[k] is not b.Decimal:
            del b.Concept.builtins[k]

    # clear any cached Table sources
    Table._used_sources.clear()