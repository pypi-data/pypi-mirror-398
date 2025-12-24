import os
import re
from nicegui import ui
import json

from v0.relationalai.debugging import DEBUG_LOG_FILE

#--------------------------------------------------
# Terminal nodes
#--------------------------------------------------

TERMINAL_NODES = [
    "query"
]

#--------------------------------------------------
# Debug log helpers
#--------------------------------------------------

class SpanNode:
    def __init__(self, id, type, parent_id, start_timestamp, attrs=None):
        self.id = id
        self.type = type
        self.parent_id = parent_id
        self.start_timestamp = start_timestamp
        self.end_timestamp = None
        self.elapsed = None
        self.start_attrs = attrs or {}
        self.end_attrs = {}
        self.children = []

    def add_end_data(self, end_timestamp, elapsed, end_attrs=None):
        self.end_timestamp = end_timestamp
        self.elapsed = elapsed
        if end_attrs:
            # Merge end_attrs into attrs
            self.end_attrs.update(end_attrs)

    def add_child(self, child):
        self.children.append(child)

    def __str__(self, level=0):
        indent = "  " * level
        result = f"{indent}{self.type} ({self.id}):\n"
        result += f"{indent}  elapsed: {self.elapsed:.6f}s\n"

        if self.start_attrs or self.end_attrs:
            result += f"{indent}  start attributes:\n"
            for key, value in self.start_attrs.items():
                # Truncate long values for display
                if isinstance(value, str) and len(value) > 100:
                    value = value[:97] + "..."
                result += f"{indent}    {key}: {value}\n"
            result += f"{indent}  end attributes:\n"
            for key, value in self.end_attrs.items():
                # Truncate long values for display
                if isinstance(value, str) and len(value) > 100:
                    value = value[:97] + "..."
                result += f"{indent}    {key}: {value}\n"

        if self.children:
            result += f"{indent}  children:\n"
            for child in self.children:
                result += child.__str__(level + 2)

        return result

def parse_jsonl_to_tree(jsonl_content):
    lines = jsonl_content.strip().split('\n')
    nodes_by_id = {}
    root_nodes = []

    for line in lines:
        data = json.loads(line)
        event_type = data["event"]

        if event_type == "span_start":
            span = data["span"]
            node = SpanNode(
                id=span["id"],
                type=span["type"],
                parent_id=span["parent_id"],
                start_timestamp=span["start_timestamp"],
                attrs=span.get("attrs", {})
            )
            nodes_by_id[node.id] = node

            # Link to parent if exists
            if node.parent_id and node.parent_id in nodes_by_id:
                nodes_by_id[node.parent_id].add_child(node)
            elif node.parent_id is None:
                root_nodes.append(node)

        elif event_type == "span_end":
            node_id = data["id"]
            if node_id in nodes_by_id:
                nodes_by_id[node_id].add_end_data(
                    end_timestamp=data["end_timestamp"],
                    elapsed=data.get("elapsed", 0),
                    end_attrs=data.get("end_attrs", {})
                )

    return root_nodes

#--------------------------------------------------
# UI
#--------------------------------------------------

last_mod_time = None
current_json_objects = []
active_ix = None
active_item = None

# this is more than toggles now that we accept regex for passes
toggles = {
    "dsl": False,
    "metamodel": False,
    "rel": False,
    "lqp": False,
    "sql": False,
    "passes": False,
    "pass_regex": None,
    "type_graph": False,
    "expand_all": False
}

checkboxes = {}

opened = set()

def toggle_open(span_id):
    global opened
    if span_id in opened:
        opened.remove(span_id)
    else:
        opened.add(span_id)
    sidebar.refresh()
    details.refresh()

def to_ms(t):
    if not t:
        return "..."
    return f"{t*1000:,.0f}"

def format_time(t):
    if not t:
        return "..."
    if t > 1:
        return f"{t:.1f}s"
    elif t > 0.001:
        return f"{t*1000:.1f}ms"
    elif t > 0.0005:
        return f"{t*1000:.2f}ms"
    else:
        return f"{t*1000000:.0f}us"

def header(text):
    return ui.label(text).style("font-size: 1.3em; font-weight: bold;")

def replace_long_brace_contents(code_str):
    def replacement(match):
        string = match.group(0)
        if len(string) > 300:
            # Extract the first 50 and last 30 characters from the string within brackets
            return '{' + string[1:51] + '...' + string[-31:-1] + '}'
        else:
            # If the string is not longer than 300 characters, return it unchanged
            return string

    # This regex matches sequences of characters wrapped in { }
    brace_content_regex = r'\{[\s\S]*?\}'

    # Use the sub method to replace the matched strings with the result of the replacement function
    return re.sub(brace_content_regex, replacement, code_str)


def code(c, language="python"):
    # do not wrap text when outputting Rel
    if language != "rel":
        c = replace_long_brace_contents(c)
    # use python's syntax highlighting for Rel as well
    if language == "rel":
        language = "ruby"
    if language == "lqp":
        language = "clojure"
    c = re.sub(r"→", "->", c)
    c = re.sub(r"⇑", "^", c)
    return ui.code(c, language=language).style("border:none; margin:0; padding-right: 30px; ").classes("w-full")

def code_with_header(header, c, language="python"):
    header = f"# --- {header} {'-' * (40 - len(header))}"
    c = header + "\n\n" + c.strip()
    return code(c, language=language)

def span_code(span:SpanNode):
    if span.type == "rule":
        if span.start_attrs.get("source"):
            code(span.start_attrs["source"]).on("click", lambda: toggle_open(span.id)).style("cursor: pointer;")
        if not toggles["expand_all"] and span.id not in opened:
            return
        with ui.column().style("gap:0px; padding-left: 30px; "):
            if toggles["dsl"]:
                code_with_header("dsl", span.start_attrs["dsl"])
            if toggles["metamodel"] and "metamodel" in span.end_attrs:
                code_with_header("metamodel", span.end_attrs["metamodel"])
    elif span.type == "query":
        if span.start_attrs.get("source"):
            code(span.start_attrs["source"]).on("click", lambda: toggle_open(span.id)).style("cursor: pointer;")
        if not toggles["expand_all"] and span.id not in opened:
            return
        with ui.column().style("gap:0px; padding-left: 30px; "):
            if toggles["dsl"]:
                code_with_header("dsl", span.start_attrs["dsl"])
            for child in span.children:
                span_code(child)
    elif span.type == "compile" and span.end_attrs.get("compile_type") == "model":
        if toggles["metamodel"]:
            code_with_header("model metamodel", span.start_attrs["metamodel"])
        for child in span.children:
            span_code(child)
        if toggles["rel"]:
            code_with_header("rel model", span.end_attrs.get("rel", '// No Rel was emitted.'), language="rel")
        if toggles["lqp"]:
            code_with_header("lqp model", span.end_attrs.get("lqp", ';; No LQP was emitted.'), language="lqp")
        if toggles["sql"]:
            code_with_header("sql model", span.end_attrs.get("sql", '-- No SQL was emitted.'), language="sql")
    elif span.type == "compile" and span.end_attrs.get("compile_type") == "query":
        if toggles["metamodel"]:
            code_with_header("metamodel", span.start_attrs["metamodel"])
        for child in span.children:
            span_code(child)
        if toggles["rel"]:
            code_with_header("rel query", span.end_attrs.get("rel", '// No Rel was emitted.'), language="rel")
        if toggles["lqp"]:
            code_with_header("lqp query", span.end_attrs.get("lqp", ';; No LQP was emitted.'), language="lqp")
        if toggles["sql"]:
            code_with_header("sql query", span.end_attrs.get("sql", '-- No SQL was emitted.'), language="sql")
    elif span.type == "passes":
        type_graph_shown = False
        if toggles["passes"]:
            previous_code = None
            for child in span.children:
                if toggles["pass_regex"] and not re.match(toggles["pass_regex"], child.type):
                    continue
                current_code = ""
                if "metamodel" in child.end_attrs:
                    current_code = child.end_attrs["metamodel"]
                    if current_code == previous_code:
                        current_code = ""
                    else:
                        previous_code = current_code
                code_element = code_with_header(child.type + f' ({format_time(child.elapsed)})', current_code)
                code_element.props(f'id="pass-{child.id}"')
                code_element.style("scroll-margin-top: 40px;")
                if child.type == "InferTypes" and toggles["type_graph"]:
                    # show the type graph inline with InferTypes
                    type_graph_shown = True
                    for child2 in child.children:
                        if child2.end_attrs.get("type_graph"):
                            ui.mermaid(child2.end_attrs['type_graph'], {"maxEdges":10000}).style("display:flex; padding:0px 0px 0px 15px; gap:30px; overflow: auto;")
        # show the type graph if it was not shown inline above
        if toggles["type_graph"] and not type_graph_shown:
            for child in span.children:
                if child.type == "InferTypes":
                    for child2 in child.children:
                        if child2.end_attrs.get("type_graph"):
                            ui.mermaid(child2.end_attrs['type_graph'], {"maxEdges":10000}).style("display:flex; padding:0px 0px 0px 15px; gap:30px; overflow: auto;")
    else:
        for child in span.children:
            span_code(child)

@ui.refreshable
def details():
    with ui.column().style("gap:2px; margin-left: 230px;"):
        for root in current_json_objects:
            span_code(root)


def handle_attributes(attrs):
    if attrs.get("file"):
        ui.label(f"{attrs['file']}: {attrs['line']}")
    if attrs.get("source"):
        code(attrs["source"])
    if attrs.get("txn_id"):
        ui.label(f"txn_id: {attrs['txn_id']}")
    if attrs.get("name"):
        ui.label(f"{attrs['name']}")
    if attrs.get("code"):
        code(attrs["code"])
    if attrs.get("dsl"):
        code(attrs["dsl"])
    if attrs.get("metamodel"):
        code(attrs["metamodel"])
    if attrs.get("rel"):
        code(attrs["rel"], language="rel")
    if attrs.get("sql"):
        code(attrs["sql"], language="sql")
    if attrs.get("results"):
        vals = attrs['results']
        if len(vals):
            keys = [k for k in vals[0].keys()]
            columns = [{'name': k, 'label': k, 'field': k, "align": "left"} for k in keys]
            ui.table(columns=columns, rows=vals)

def handle_body(span: SpanNode):
    if span.children and span.type not in ["rule_batch"]:
        for child in span.children:
            span_ui(child, True)

def span_ui(span: SpanNode, is_pass: bool=False):
    def jump_to_pass():
        global toggles
        checkboxes["passes"].set_value(True)
        toggles["passes"] = True
        sidebar.refresh()
        details.refresh()
        ui.navigate.to(f"#pass-{span.id}")

    with ui.column().classes("w-full").style("padding:0px 0px 0px 15px; gap:2px; "):
        with ui.row().classes("w-full").style("padding-left:5px; flex-wrap:nowrap; margin:0; background: #2c2c2c") as me:
            name = span.type
            if name == "create_v2":
                name += " ➚"
            ui.label(name).style("padding:0; margin:0; color: #DDD;")
            ui.space()
            ui.label(f"{to_ms(span.elapsed)}").style("padding-right: 5px; color:#999;")
            if span.type == "create_v2":
                txn_id = span.end_attrs.get("txn_id")
                me.on("click", lambda: ui.navigate.to(f"https://171608476159.observeinc.com/workspace/41759331/log-explorer?datasetId=41832558&filter-rai_transaction_id={txn_id}", new_tab=True))
                me.style("cursor: pointer;")
            elif is_pass:
                me.on("click", lambda: jump_to_pass())
                me.style("cursor: pointer;")
        handle_body(span)


@ui.refreshable
def sidebar():
    with ui.column().style("min-width: 270px; max-width: 270px; margin-top: 50px; height: calc(100vh - 60px); overflow-x: hidden; overflow-y: auto; position: fixed; top: 0; left: 0; z-index: 1000;"):
        for root in current_json_objects:
            span_ui(root)


def poll():
    global last_mod_time, active_item
    global current_json_objects
    # Check the last modification time of the file
    try:
        mod_time = os.path.getmtime(DEBUG_LOG_FILE)
        if last_mod_time is None or mod_time > last_mod_time:
            last_mod_time = mod_time
            # File has changed, read and parse the new content
            with open(DEBUG_LOG_FILE, 'r') as file:
                content = file.read()
                if content:
                    new_tree = parse_jsonl_to_tree(content)
                    # Update the current JSON objects
                    current_json_objects = new_tree

                    if active_ix is not None and len(current_json_objects) > active_ix:
                        active_item = current_json_objects[active_ix]
                    # Refresh the UI with the new objects
                    sidebar.refresh()
                    details.refresh()
    except FileNotFoundError:
        pass

def toggle(key):
    global toggles
    toggles[key] = not toggles[key]
    sidebar.refresh()
    details.refresh()

def set_toggle_value(key, value):
    global toggles
    toggles[key] = value
    sidebar.refresh()
    details.refresh()

def main(host="0.0.0.0", port=8080):
    global checkboxes
    global toggles
    ui.dark_mode(None)
    with ui.column():
        with ui.row().style("flex-wrap: nowrap; position: fixed; top: 0; left: 0; right: 0; z-index: 1000; background: #3c3c3c; color: #DDD;"):
            ui.switch('expand all', value=toggles["expand_all"], on_change=lambda: toggle("expand_all"))
            checkboxes["dsl"] = ui.checkbox('dsl', on_change=lambda: toggle("dsl"))
            checkboxes["metamodel"] = ui.checkbox('metamodel', on_change=lambda: toggle("metamodel"))
            checkboxes["passes"] = ui.checkbox('passes', on_change=lambda: toggle("passes")).props('id=passes_box')
            checkboxes["rel"] = ui.checkbox('rel', on_change=lambda: toggle("rel"))
            checkboxes["lqp"] = ui.checkbox('lqp', on_change=lambda: toggle("lqp"))
            checkboxes["sql"] = ui.checkbox('sql', on_change=lambda: toggle("sql"))
            checkboxes["type_graph"] = ui.checkbox('type graph', on_change=lambda: toggle("type_graph"))
            ui.input(label='Filter passes by regex', on_change=lambda e: set_toggle_value("pass_regex", e.value)
                     ).props('clearable input-style="color: white" input-class="font-mono" flat dense')
        with ui.row().style("flex-wrap: nowrap; margin-top: 30px;"):
            with ui.column() as c:
                sidebar()
            with ui.column() as c:
                c.style("padding-left: 2em;")
                details()

        # Scroll to top button
        ui.button("↑", on_click=lambda: ui.run_javascript("window.scrollTo({top: 0, behavior: 'smooth'})")).style(
            "position: fixed; "
            "bottom: 20px; "
            "right: 20px; "
            "z-index: 1001; "
            "width: 50px; "
            "height: 50px; "
            "border-radius: 50%; "
            "background: #4a4a4a; "
            "color: white; "
            "border: 2px solid #666; "
            "font-size: 20px; "
            "font-weight: bold; "
            "cursor: pointer; "
            "box-shadow: 0 2px 10px rgba(0,0,0,0.3);"
        ).props("title='Scroll to top'")

    ui.timer(1, poll)
    ui.run(reload=False, host=host, port=port)

if __name__ in {"__main__", "__mp_main__"}:
    main()
