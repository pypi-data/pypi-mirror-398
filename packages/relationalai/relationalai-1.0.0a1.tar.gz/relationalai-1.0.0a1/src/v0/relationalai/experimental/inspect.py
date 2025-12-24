from pandas import DataFrame
import rich
from rich.table import Table
from rich import box
from rich.console import Console
from v0.relationalai.environments.base import SourceInfo
from v0.relationalai.metamodel import Namer
from v0.relationalai.std import rel
from v0.relationalai.environments import runtime_env
from v0.relationalai.dsl import to_var

_watch_info = {}

def watch(*args):
    ix = len(_watch_info)
    namer = Namer()
    _watch_info[ix] = {"loc": runtime_env.get_source(), "args": [namer.get(to_var(a)) for a in args]}
    rel.output.__pyrel_debug_watch.add(ix, *args)

def _watch_table(df:DataFrame):
    # Create a table
    table = Table(show_header=True, box=box.ROUNDED, padding=(0, 1))
    for k in df.columns:
        table.add_column(k)

    for row in df.itertuples(index=False):
        table.add_row(*[str(p) for p in row])

    console = Console()
    width = console.measure(table).maximum
    rich.print(table)
    row_str = f"{len(df)} rows"
    rich.print(f"[dim white]{row_str:>{width-1}}")

def _print_watch_frame(result_frame:DataFrame):
    first_col = result_frame.columns[0]
    for ix, group in result_frame.groupby(first_col):
        source_info:SourceInfo = _watch_info[ix]["loc"]
        line = source_info.source.split("\n")[source_info.line - source_info.source_start_line]
        print()
        rich.print(f"[yellow bold]{line.strip()}")
        rich.print(f"[dim white]{source_info.file}:{source_info.line}")
        print()
        group = group.drop(first_col, axis=1)
        group.columns = _watch_info[ix]["args"]
        group.reset_index(drop=True, inplace=True)
        _watch_table(group)
