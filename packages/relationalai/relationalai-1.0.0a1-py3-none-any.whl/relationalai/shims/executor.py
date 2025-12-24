
#------------------------------------------------------
# VERY UNSTABLE API TO EXECUTE FRONTEND PROGRAMS USING V0 EXECUTORS
#------------------------------------------------------
from functools import lru_cache
import json
from v0.relationalai import debugging
from v0.relationalai.semantics.lqp.executor import LQPExecutor
from v0.relationalai.semantics.rel.executor import RelExecutor
from v0.relationalai.semantics.metamodel import ir as v0, factory as v0_factory
from v0.relationalai.semantics.metamodel.visitor import collect_by_type
from v0.relationalai.semantics.snowflake import Table as v0Table
from v0.relationalai.clients.snowflake import Provider as v0Provider
from v0.relationalai.clients.config import Config

# from ..config import Config
from ..config.shims import DRY_RUN
from ..semantics import Model, Fragment
from ..semantics.metamodel import metamodel as mm
from ..semantics.metamodel.typer import Typer
from ..semantics.metamodel.metamodel_analyzer import Normalize
from .mm2v0 import Translator

DEBUG=False
PRINT_RESULT=False
TYPER_DEBUGGER=False

# DEBUG=True
# PRINT_RESULT=True
# TYPER_DEBUGGER=True

def execute(query: Fragment, model: Model|None = None, executor=None, export_to="", update=False):
    if not executor:
        # use_lqp = Config().reasoner.rule.use_lqp
        use_lqp = bool(Config().get("reasoner.rule.use_lqp", True))
        executor = "lqp" if use_lqp else "rel"
    mm_model = model.to_metamodel() if model else None
    mm_query = query.to_metamodel()
    assert isinstance(mm_query, mm.Node)
    return execute_mm(mm_query, mm_model, executor, export_to=export_to, update=update, model=model)

def execute_mm(mm_query: mm.Task, mm_model: mm.Model|None = None, executor="lqp", export_to="", update=False, model: Model|None = None):
    # perform type inference
    typer = Typer()
    # normalize the metamodel
    normalizer = Normalize()
    # translate the metamodel into a v0 query
    translator = Translator()

    # for typer debugging
    debugger_msgs = []

    try:
        #------------------------------------------------------
        # Model processing
        #------------------------------------------------------
        v0_model = None
        if mm_model:
            # type inference
            debugger_msgs.append(json.dumps({ 'id': 'model', 'content': str(mm_model)}))
            with debugging.span("compile", metamodel=mm_model) as span:
                span["compile_type"] = "model_v1"
                mm_model = typer.infer_model(mm_model)
                span["typed_mm"] = str(mm_model)
                debugger_msgs.append(json.dumps({ 'id': 'typed_model', 'content': str(mm_model)}))
                assert(typer.model_net is not None)
                debugger_msgs.append(json.dumps({ 'id': 'model_net', 'content': str(typer.model_net.to_mermaid())}))
                # normalization
                mm_model = mm_model.mut(root=normalizer.normalize(mm_model.root)) # type: ignore
                assert isinstance(mm_model, mm.Model)
                if DEBUG:
                    print("V1 Model:")
                    print(mm_model)
                # translation
                v0_model = translator.translate_model(mm_model)
                if DEBUG:
                    print("Translated v0 Model:")
                    print(v0_model)

        #------------------------------------------------------
        # Query processing
        #------------------------------------------------------
        # type inference
        debugger_msgs.append(json.dumps({ 'id': 'query', 'content': str(mm_query)}))
        with debugging.span("compile", metamodel=mm_query) as span:
            span["compile_type"] = "query_v1"
            mm_query = typer.infer_query(mm_query)
            span["typed_mm"] = str(mm_query)
            debugger_msgs.append(json.dumps({ 'id': 'typed_query', 'content': str(mm_query)}))
            assert(typer.last_net is not None)
            debugger_msgs.append(json.dumps({ 'id': 'query_net', 'content': str(typer.last_net.to_mermaid())}))
            # normalization
            mm_query = normalizer.normalize(mm_query)  # type: ignore
            assert isinstance(mm_query, mm.Task)
            if DEBUG:
                print("V1 Query:")
                print(mm_query)
            # translation
            v0_query = translator.translate_query(mm_query)
            if DEBUG:
                print("Translated v0 Query:")
                print(v0_query)
            assert isinstance(v0_query, v0.Task)

        if v0_model is None:
            # there was no model, so create one from the elements refered to by the query
            v0_model = v0_factory.model(
                collect_by_type(v0.Engine, v0_query),
                collect_by_type(v0.Relation, v0_query),
                v0_factory._collect_reachable_types(collect_by_type(v0.Type, v0_query)),
                v0_factory.logical([])
            )
    finally:
        if TYPER_DEBUGGER:
            with open("typer_debug.jsonl", "w") as f:
                for msg in debugger_msgs:
                    f.write(msg)
                    f.write('\n')

    if DRY_RUN:
        results = []
    else:
        # create snowflake tables for all the tables that have been used
        ts = [v0Table(t.name) for t in translator.used_tables if not t.uri.startswith("dataframe://")]
        for t in ts:
            t._lazy_init()
            v0Table._used_sources.add(t)

        export_table = None
        if export_to:
            export_table = v0Table(export_to)

        # get an executor and execute
        executor = _get_executor(executor, model.name if model else "")
        with debugging.span("query", tag=None, export_to=export_to) as query_span:
            if isinstance(executor, (LQPExecutor, RelExecutor)):
                results = executor.execute(v0_model, v0_query, export_to=export_table, update=update)
            else:
                results = executor.execute(v0_model, v0_query)
            query_span["results"] = results
        if DEBUG or PRINT_RESULT:
            print(results)
    return results

@lru_cache()
def _get_executor(name: str, database: str = "ttb_test"):
    if name == "duckdb":
        from v0.relationalai.semantics.sql.executor.duck_db import DuckDBExecutor
        return DuckDBExecutor()
    elif name == "lqp":
        return LQPExecutor(database)
    elif name == "rel":
        return RelExecutor(database)
    elif name == "snowflake":
        from v0.relationalai.semantics.sql.executor.snowflake import SnowflakeExecutor
        return SnowflakeExecutor(database="TEST_DB", schema="PUBLIC")
    else:
        raise ValueError(f"Unknown executor: {name}")

def get_provider():
    return v0Provider()
