import os
import re
from nicegui import ui
import json
import dataclasses


#--------------------------------------------------
# Data
#--------------------------------------------------
last_mod_time = None
current_content: dict[str, str] = dict()

def parse_file(jsonl_content):
    content = dict()
    lines = jsonl_content.strip().split('\n')
    for line in lines:
        data = json.loads(line)
        content[data['id']] = data['content']
    return content

def poll():
    global last_mod_time
    global current_content
    # Check the last modification time of the file
    try:
        mod_time = os.path.getmtime('typer_debug.jsonl')
        if last_mod_time is None or mod_time > last_mod_time:
            last_mod_time = mod_time
            # File has changed, read and parse the new content
            with open('typer_debug.jsonl', 'r') as file:
                content = file.read()
                if content:
                    current_content = parse_file(content)
                    view.refresh()
    except FileNotFoundError:
        pass

#--------------------------------------------------
# UI
#--------------------------------------------------

@ui.refreshable
def view():
    with ui.column():
        # model
        with ui.row():
            with ui.column():
                ui.label("Model").style("font-weight: bold;")
                code(current_content.get('model', ''), language='metamodel')
            with ui.column():
                ui.label("Typed Model").style("font-weight: bold;")
                code(current_content.get('typed_model', ''), language='metamodel')
        # typer
        with ui.row():
            ui.label("Type Propagation Network").style("font-weight: bold;")
            ui.mermaid(current_content.get('model_net', ''),
                       {"maxEdges":10000}
            ).style("display:flex; padding:0px 0px 0px 15px; gap:30px; overflow: auto;").on('error', lambda e: print(e.args['message']))
        # query
        with ui.row():
            with ui.column():
                ui.label("Query").style("font-weight: bold;")
                code(current_content.get('query', ''), language='rel')
            with ui.column():
                ui.label("Typed Query").style("font-weight: bold;")
                code(current_content.get('typed_query', ''), language='rel')

        # typer
        with ui.row():
            ui.label("Type Propagation Network").style("font-weight: bold;")
            ui.mermaid(current_content.get('query_net', ''), {"maxEdges":10000}).style("display:flex; padding:0px 0px 0px 15px; gap:30px; overflow: auto;")

def code(c, language="python"):
    if language == "rel":
        language = "ruby"
    if language == "lqp":
        language = "clojure"
    c = re.sub(r"→", "->", c)
    c = re.sub(r"⇑", "^", c)
    return ui.code(c, language=language).style("border:none; margin:0; padding-right: 30px; ").classes("w-full")

def main(host="0.0.0.0", port=8082):
    global checkboxes
    global toggles
    ui.dark_mode(True)
    view()

    ui.timer(1, poll)
    ui.run(reload=False, host=host, port=port)

if __name__ in {"__main__", "__mp_main__"}:
    main()
