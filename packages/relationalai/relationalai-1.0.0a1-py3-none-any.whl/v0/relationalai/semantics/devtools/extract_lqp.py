# This script runs a QB program and captures the Snowflake requests made to the RAI Native App.
# The output is a JSON file containing information about the requests that can be used to run
# the same queries on a local RAI server.

import argparse
import os
import json
from contextlib import contextmanager

from v0.relationalai.clients.snowflake import Resources as snowflake_api
from v0.relationalai.semantics.internal import internal
from typing import Dict, Optional

def main():
    parser = argparse.ArgumentParser(description="Extract LQP requests to run locally")
    parser.add_argument("--program", type=str, help="Path to the QB program to run", required=True)
    parser.add_argument("--outdir", type=str, help="Path to the output directory", required=True)

    args = parser.parse_args()
    program = args.program
    outdir = args.outdir

    if not os.path.isfile(program):
        raise ValueError(f"Program path {program} is not a file")
    if not os.path.isdir(outdir):
        raise ValueError(f"Output path {outdir} is not a directory")

    extract_rai_calls(program, outdir)

@contextmanager
def instrumented_exec_rai_app(captured_calls, call_counter):
    """Context manager to instrument _exec_rai_app method for capturing RAI calls."""
    # Store the original method
    original_exec_rai = snowflake_api._exec_rai_app

    def _instrumented_exec_rai_app(
        self,
        database: str,
        engine,
        raw_code: str,
        inputs: Dict,
        readonly=True,
        nowait_durable=False,
        request_headers=None,
        bypass_index=False,
        language: str = "rel",
        query_timeout_mins: Optional[int] = None,
    ):
        result = original_exec_rai(
            self,
            database=database,
            engine=engine,
            raw_code=raw_code,
            inputs=inputs,
            readonly=readonly,
            nowait_durable=nowait_durable,
            request_headers=request_headers,
            bypass_index=bypass_index,
            language=language,
            query_timeout_mins=query_timeout_mins,
        )

        call_counter[0] += 1
        exec_call_json = {
            "call_type": "raicode",
            "id": call_counter[0],
            "database": database,
            "inputs": inputs,
            "readonly": readonly,
            "nowait_durable": nowait_durable,
            "language": language,
            "timeout_mins": query_timeout_mins,
            "raw_code": raw_code,
        }
        captured_calls.append(exec_call_json)
        return result

    # Apply the monkey patch
    snowflake_api._exec_rai_app = _instrumented_exec_rai_app

    try:
        yield
    finally:
        # Restore the original method
        snowflake_api._exec_rai_app = original_exec_rai

def extract_rai_calls(qb_prog_path: str, outdir: str):
    """Extract RAI calls by instrumenting _exec_rai_app and executing the QB program."""
    exec_calls = []
    call_counter = [0]  # Use list for mutable reference in closure

    with instrumented_exec_rai_app(exec_calls, call_counter):
        with internal.with_overrides(**{
            'dry_run': False,
            'reasoner.rule.use_lqp': True,
        }):
            with open(qb_prog_path) as f:
                # Compile with the correct filename
                code = compile(f.read(), qb_prog_path, "exec")
                exec(code)

    # Write results to file
    final_json = json.dumps(exec_calls, default=str)
    out_path = os.path.join(outdir, "lqp_requests.json")
    with open(out_path, "w") as f:
        f.write(final_json)
    print(f"Wrote {len(exec_calls)} exec calls to {out_path}")

if __name__ == "__main__":
    main()
