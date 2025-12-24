import os
import re
from nicegui import ui
import json

from v0.relationalai.debugging import DEBUG_LOG_FILE


last_mod_time = None
current_json_objects = []
active_ix = None
active_item = None

def set_item(ix):
    global active_item, active_ix
    if active_ix != ix:
        active_ix = ix
        active_item = current_json_objects[ix]
        my_stuff.refresh()
        details.refresh()

def format_time(t):
    if t > 1:
        return f"{t:.1f}s"
    elif t > 0.001:
        return f"{t*1000:.1f}ms"
    elif t > 0.0001:
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


def code(c):
    c = replace_long_brace_contents(c)
    return ui.code(c).style("padding-right: 30px").classes("w-full")


@ui.refreshable
def details():
    if active_item:
        if active_item['event'] == "compilation":
            header(f"{active_item['source']['file']}: {active_item['source']['line']}")
            # with ui.row():
            code(active_item["source"]["block"] or active_item["emitted"])
            code(f"{active_item['emitted']}")
            header("IR")
            code(f"{active_item['task']}")
            header("Rewritten")
            code(f"{active_item['passes'][-1]['task']}")
            header("Passes")
            for p in active_item['passes']:
                with ui.column().classes("w-full"):
                    with ui.row():
                        ui.label(p['name'])
                        ui.label(f"({p['elapsed']*1000000:.0f} us)")
                    code(p['task'])
        elif active_item['event'] == "time":
            ui.label(f"{active_item['type']} | {format_time(active_item['elapsed'])} | {active_item['results']['count']}")
            vals = active_item['results']['values']
            if len(vals):
                keys = [k for k in vals[0].keys()]
                columns = [{'name': k, 'label': k, 'field': k, "align": "left"} for k in keys]
                ui.table(columns=columns, rows=vals)
            if "code" in active_item:
                header("Code")
                code(active_item["code"])
            # ui.label(f"{active_item['results']['values']}").style('white-space: pre;')

@ui.refreshable
def my_stuff():
    total_time = 0
    with ui.column():

        for (ix, obj) in enumerate(current_json_objects):
            me = None

            if obj['event'] == "compilation":
                me = code(obj["source"]["block"] or obj["emitted"])
                total_time += obj["emit_time"]
                for p in obj['passes']:
                    total_time += p['elapsed']
            elif obj['event'] == "time":
                total_time += obj['elapsed']
                with ui.row() as me:
                    me.style("padding: 5px 10px; border: 1px solid #544; border-radius: 5px; background:#322;")
                    ui.label(f"{obj['type']}")
                    ui.label(format_time(obj['elapsed']))
                    if obj.get('results'):
                        ui.label(f"{obj['results']['count']}")
            elif obj['event'] == "transaction_created":
                with ui.row() as me:
                    me.style("padding: 5px 10px; border: 1px solid #544; border-radius: 5px; background:#322;")
                    ui.label("transaction")
                    ui.label(obj["txn_id"])
            elif obj.get('type'):
                total_time += obj.get('elapsed', 0)
                with ui.row() as me:
                    me.style("padding: 5px 10px; border: 1px solid #544; border-radius: 5px; background:#322;")
                    ui.label(f"{obj['type']}")
                    ui.label(format_time(obj.get('elapsed', 0)))
                    if obj.get('results'):
                        ui.label(f"{obj['results']['count']}")
            elif 'span' not in obj['event'] and obj['event'] != "profile_events":
                with ui.row() as me:
                    me.style("padding: 5px 10px; border: 1px solid #544; border-radius: 5px; background:#322;")
                    ui.label(f"{obj['event']}")

            if me:
                me.classes("w-full")
                me.on("click", lambda ix=ix: set_item(ix))
                if ix != active_ix:
                    me.style('opacity: 0.5')
        with ui.row() as me:
            me.style("padding: 5px 10px; border: 1px solid #445; border-radius: 5px; background:#223; opacity: 0.5;")
            me.classes("w-full")
            if total_time > 1:
                ui.label(f"Total time: {total_time:.1f}s")
            else:
                ui.label(f"Total time: {total_time * 1000:.0f}ms")


def poll():
    global last_mod_time, active_item
    global current_json_objects
    # Check the last modification time of the file
    try:
        mod_time = os.path.getmtime(DEBUG_LOG_FILE)
        if last_mod_time is None or mod_time > last_mod_time:
            last_mod_time = mod_time
            # File has changed, read and parse the new content
            new_objects = []
            with open(DEBUG_LOG_FILE, 'r') as file:
                for line in file:
                    try:
                        # Parse each JSON object and add it to the list
                        obj = json.loads(line)
                        new_objects.append(obj)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON: {e}")
            # Update the current JSON objects
            current_json_objects = new_objects
            if active_ix is not None and len(current_json_objects) > active_ix:
                active_item = current_json_objects[active_ix]
            # Refresh the UI with the new objects
            my_stuff.refresh()
            details.refresh()
    except FileNotFoundError:
        pass

def main(host="0.0.0.0", port=8080):
    ui.dark_mode().enable()
    with ui.row():
        with ui.column() as c:
            c.style("cursor: pointer;")
            my_stuff()
        with ui.column() as c:
            c.style("padding-left: 2em;")
            details()

    ui.timer(1, poll)
    ui.run(reload=False, host=host, port=port)

if __name__ == "__main__":
    main()
