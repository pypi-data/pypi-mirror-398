from __future__ import annotations
import asyncio
import json
from pathlib import Path
import time
from typing import Any, Callable, Coroutine, Protocol, Union, cast
import webbrowser

import aiohttp
from websockets.exceptions import ConnectionClosed
from aiohttp import web

import v0.relationalai
from v0.relationalai.clients.client import ResourcesBase
from v0.relationalai.debugging import encode_log_message

MAX_MSG_SIZE = 4*4194304 # 16MB
PROJECT_ROOT = Path(v0.relationalai.__file__).resolve()

# This is weird and dynamic because the frontend directory is in different
# places depending on whether you're running with `-e`, or install a package.
max_ancestor_steps = 3
FRONTEND_PATH = PROJECT_ROOT
while not (FRONTEND_PATH / "frontend").exists() and max_ancestor_steps > 0:
    FRONTEND_PATH = FRONTEND_PATH.parent
    max_ancestor_steps -= 1

HTTP_DIST_DIR = FRONTEND_PATH / "frontend" / "debugger" / "dist"

# The maximum number of messages to be sent at once when catching a new client up
MAX_BATCH_SIZE = 500

_resources: ResourcesBase|None = None

def get_resources() -> ResourcesBase:
    if not _resources:
        raise Exception("Unable to acquire resources")

    return _resources

def is_program_event(msg):
    if msg.get("event") != "span_start":
        return False
    span = msg.get("span")
    if not span or span.get("type") != "program":
        return False

    return True

#------------------------------------------------------------------------------
# Program Connections
#------------------------------------------------------------------------------

connected_program = None

async def handle_program(req: web.Request):
    ws = web.WebSocketResponse(max_msg_size=MAX_MSG_SIZE)
    await ws.prepare(req)

    global connected_program
    if connected_program:
        print("Refusing to connect to new program until previous one finishes.")
        await ws.close()

    connected_program = ws
    program_id:str|None = None
    print("Program connected")
    err = None
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                await broadcast(msg.data)
                if program_id is None:
                    try:
                        parsed = json.loads(msg.data)
                        if is_program_event(parsed):
                            program_id = parsed["span"]["id"]
                    except Exception:
                        ...
                    # parse and look for the program id
                    ...
            elif msg.type == aiohttp.WSMsgType.ERROR:
                err = ws.exception()
                if err:
                    if "Decompressed message size" in str(err):
                        await broadcast_error("Failed to send large message from program", err)
                    else:
                        raise err
            else:
                err = Exception("Unknown message type", msg.type)
                raise err
    finally:
        print("Program disconnected")
        await broadcast_event("program_disconnected", id=program_id, cause=err)
        connected_program = None

    return ws

#------------------------------------------------------------------------------
# Browser Client Connections
#------------------------------------------------------------------------------

connected_clients: set[web.WebSocketResponse] = set()

async def handle_client(req: web.Request):
    ws = web.WebSocketResponse(max_msg_size=MAX_MSG_SIZE)
    close_reason = None
    try:
        await ws.prepare(req)
        connected_clients.add(ws)
        print("Client connected")

        for i in range(0, len(buffered_broadcasts), MAX_BATCH_SIZE):
            chunk = ",".join(buffered_broadcasts[i:i + MAX_BATCH_SIZE])
            await ws.send_str(f"[{chunk}]")

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                await handle_client_action(msg.data, ws)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                err = ws.exception()
                if err:
                    raise err
            else:
                raise Exception("Unknown message type", msg.type)

    except ConnectionClosed:
        ...
    except ConnectionResetError as e:
        close_reason = e
    finally:
        if ws in connected_clients:
            if close_reason:
                print(f"Client disconnected with reason: {close_reason}")
            else:
                print("Client disconnected")
            connected_clients.remove(ws)

    return ws

class NoSuchActionError(KeyError):
    def __init__(self, action: str|None):
        super().__init__(f"Got action request from client for non-existent action of type '{action}'")

async def handle_client_action(msg: Any, ws: web.WebSocketResponse):
    parsed = None
    action_type = None
    try:
        parsed = json.loads(msg)
        action_type = parsed.get("type")
        action = client_actions.get(action_type)
        if not action:
            raise NoSuchActionError(action_type)
        kwargs = {k: v for k, v in parsed.items() if k != "type" and k != "rpc_id"}
        res = action(ws, **kwargs) or {}

    except Exception as e:
        print("Error:", str(e))
        res = {"error": str(e)}

    if parsed:
        if asyncio.iscoroutine(res):
            res = await res

        res = cast(dict, res)
        res["event"] = "rpc_response"
        res["rpc_id"] = parsed.get("rpc_id")

        def dump_json(v):
            return json.dumps(v, default=encode_log_message)

        try:
            await ws.send_json([res], None, dumps=dump_json)
        except ConnectionResetError:
            print(f"[WARN] client disconnected with open RPC request '{action_type}'")

#------------------------------------------------------------------------------
# Browser Client Actions
#------------------------------------------------------------------------------

MaybeDict = Union[dict, None]
ClientActionReturn = Union[Coroutine[Any, Any, MaybeDict], MaybeDict]

class ClientAction(Protocol):
    def __call__(self, ws: web.WebSocketResponse, **kwargs: Any) -> ClientActionReturn:
        ...

client_actions: dict[str, ClientAction] = {}

def client_action(name: str|None = None):
    def decorator(fn: Callable[..., ClientActionReturn]):
        client_actions[name or fn.__name__] = fn

    return decorator

@client_action()
def clear(_):
    buffered_broadcasts.clear()

@client_action()
def list_transactions(_, **kwargs):
    return {"transactions": get_resources().list_transactions(**kwargs)}

@client_action()
def list_imports(_, **kwargs):
    if get_resources().platform == "snowflake":
        imports = get_resources().list_imports(**kwargs)
    else:
        imports = []
    return {"imports": imports}

@client_action()
def get_imports_status(_, **kwargs):
    return {"imports_status": get_resources().get_imports_status(**kwargs)}

#------------------------------------------------------------------------------
# Event Log
#------------------------------------------------------------------------------

buffered_broadcasts = []

async def broadcast(message):
    buffered_broadcasts.append(message)
    if connected_clients:
        tasks = {asyncio.create_task(client.send_str(f"[{message}]")): client for client in connected_clients}
        done, _ = await asyncio.wait(tasks.keys())
        for task in done:
            try:
                task.result()
            except ConnectionResetError:
                client = tasks[task]
                if client in connected_clients:
                    print("f[WARN] client disconnected mid-send.")
                    connected_clients.remove(client)

def broadcast_event(type: str, quiet = True, **kwargs):
    if not quiet:
        print(f"[SEND] {type}", kwargs)
    return broadcast(json.dumps({"event": type, "origin": "debug-server", **kwargs}))

def broadcast_error(msg: str, err: BaseException):
    print(f"[WARN] {msg}")
    return broadcast_event("error", quiet=True, message=msg, cause=str(err), stack=str(err.__traceback__))

#------------------------------------------------------------------------------
# Server
#------------------------------------------------------------------------------

async def serve_index(_):
    return web.FileResponse(HTTP_DIST_DIR / "index.html")

runner: web.AppRunner|None = None
async def run_server(host: str, port: int):
    global runner
    if runner:
        await runner.shutdown()

    app = web.Application()
    app.router.add_get("/ws/program", handle_program)
    app.router.add_get("/ws/client", handle_client)
    app.router.add_get("/", serve_index)
    app.router.add_static("/", HTTP_DIST_DIR, show_index=False)  # Serving static files from DIR
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    url = f"http://{host}:{port}"
    time.sleep(0.25)
    print(f"Server started at {url}")
    webbrowser.open(url)

    return runner

def start_server(host: str, port: int|None = None, profile:str|None = None):
    global _resources
    _resources = v0.relationalai.Resources(profile)

    if port is None:
        try:
            config_port = _resources.config.get("debug.port", 8080)
            if isinstance(config_port, int):
                port = config_port
            else:
                raise Exception("Invalid value specified for `debug.port`, expected `int`.")
        except AttributeError:
            port = 8080

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_server(host, port))
    loop.run_forever()


def stop_server():
    global runner
    if not runner:
        return

    loop = asyncio.get_running_loop()
    loop.run_until_complete(broadcast(json.dumps({"event": "debug_server_closed"})))
    loop.run_until_complete(runner.shutdown())
    runner = None
