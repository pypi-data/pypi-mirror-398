#pyright: reportPrivateImportUsage=false
from __future__ import annotations
import io
import os
import re
import sys
import requests
import rich
import click
import functools
import pytz

from v0.relationalai.util.constants import TOP_LEVEL_PROFILE_NAME
from .. import Resources
from rich.table import Table
from typing import Callable, Dict, Any
from ..clients import config
from click.core import Context
from rich.console import Console
from rich import box as rich_box
from collections import defaultdict
from packaging.version import Version
from ..clients.config import ConfigFile
from datetime import datetime, timedelta
from click.formatting import HelpFormatter
from ..clients.client import ResourcesBase
from v0.relationalai.tools.constants import GlobalProfile
from v0.relationalai.tools.cli_controls import divider
from v0.relationalai.util.format import humanized_bytes, humanized_duration

#--------------------------------------------------
# Helpers
#--------------------------------------------------

@functools.cache
def get_config(profile:str|Dict[str, Any]|None = None):
    return config.Config(profile or GlobalProfile.get())

@functools.cache
def get_resource_provider(platform:str|None=None, _cfg:config.Config|None = None) -> ResourcesBase:
    cfg = _cfg or get_config()
    provider = Resources(config=cfg)
    return provider

def unexpand_user_path(path):
    """Inverse of os.path.expanduser"""
    home_dir = os.path.expanduser('~')
    if path.startswith(home_dir):
        return '~' + path[len(home_dir):]
    return path

def account_from_url(account_or_url:str):
    regex = r"https://app.snowflake.com/([^/]+)/([^/]+)/?.*"
    match = re.match(regex, account_or_url)
    if match:
        org = match.group(1)
        account = match.group(2)
        return f"{org}-{account}"
    elif "app.snowflake.com" in account_or_url or "https://" in account_or_url:
        raise ValueError("URL not of the form https://app.snowflake.com/[org]/[account]")
    else:
        return account_or_url

def supports_platform(*platform_names: str):
    def decorator(cmd: click.Command):
        setattr(cmd, "__available_platforms", platform_names)
        cb = cmd.callback
        assert cb
        def checked(*args, **kwargs):
            assert cmd.name
            assert_command_available(cmd.name, command_available(cmd))
            return cb(*args, **kwargs)

        cmd.callback = checked
        return cmd
    return decorator

def command_available(cmd: click.Command) -> bool:
    available_platforms = getattr(cmd, "__available_platforms", ())
    platform = get_config().get("platform", "")
    return not available_platforms or not platform or platform in available_platforms

def assert_command_available(name: str, available: bool, plural=False):
    if not available:
        platform = get_config().get("platform", "")
        rich.print(f"[yellow]{name} {'are' if plural else 'is'} not available for {platform}")
        divider()
        sys.exit(1)

def coming_soon():
    rich.print("[yellow]This isn't quite ready yet, but it's coming soon!")
    divider()
    sys.exit(1)

def issue_top_level_profile_warning():
    rich.print("[yellow]Warning: Using a top-level profile is not recommended")
    rich.print("[yellow]Consider naming the profile by adding \\[profile.<name>] to your raiconfig.toml file\n")
    rich.print("[yellow]Example:")
    rich.print("[yellow]\\[profile.default]")
    rich.print("[yellow]platform = \"snowflake\"")
    rich.print("[yellow]account = ...")
    divider()

def ensure_config(profile:str|None=None) -> config.Config:
    cfg = get_config(profile)
    if not cfg.file_path:
        rich.print("[yellow bold]No configuration file found.")
        rich.print("To create one, run: [green bold]rai init[/green bold]")
        divider()
        sys.exit(1)
    return cfg

def latest_version(package_name):
    """Get the current version of a package on PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        version = data['info']['version']
        return version
    else:
        return None

def is_latest_cli_version():
    from .. import __version__
    latest_ver_str = latest_version("relationalai")
    latest_ver = Version(latest_ver_str) if latest_ver_str else Version("0.0.0")
    version = Version(__version__)
    return version >= latest_ver, version, latest_ver

#--------------------------------------------------
# Validation
#--------------------------------------------------

EMPTY_STRING_REGEX = re.compile(r'^\S+$')
ENGINE_NAME_REGEX = re.compile(r'^[a-zA-Z]\w{2,}$')
COMPUTE_POOL_REGEX = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')
PASSCODE_REGEX = re.compile(r'^(\d{6})?$')
ENGINE_NAME_ERROR = "Min 3 chars, start with letter, only letters, numbers, underscores allowed."
UUID = re.compile('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')

def validate_engine_name(name:str) -> tuple[bool, str|None]:
    if not ENGINE_NAME_REGEX.match(name):
        return False, ENGINE_NAME_ERROR
    return True, None

#--------------------------------------------------
# Tables
#--------------------------------------------------

def get_color_by_state(state: str) -> str:
    if state and isinstance(state, str):
        state_lower = state.lower()
        if state_lower in ("aborted", "quarantined"):
            return "red"
        elif state_lower == "completed":
            return "white"
        elif state_lower in ("running", "cancelling", "syncing", "pending", "processing"):
            return "bold yellow"
        elif state_lower == "suspended":
            return "dim"
        else:
            return ""
    return ""

def format_value(value) -> str:
    if value is None:
        return "N/A"
    elif isinstance(value, (int, float)):
        return f"{value}"
    elif isinstance(value, list):
        return ", ".join(map(str, value))
    elif isinstance(value, bool):
        return f"{value}"
    elif isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(value, timedelta):
        return humanized_duration(int(value.total_seconds() * 1000))
    else:
        return str(value)

def format_row(key: str, value) -> dict:
    result = {}
    result[key] = value
    if "status" or "state" in key.lower():
        result["style"] = get_color_by_state(value)
    if key == "query_size" and isinstance(value, int):
        result[key] = humanized_bytes(value)
    else:
        result[key] = format_value(value)
    return result

def show_dictionary_table(dict, format_fn:Callable|None=None):
    table = Table(show_header=True, border_style="dim", header_style="bold", box=rich_box.SIMPLE_HEAD)
    table.add_column("Field")
    table.add_column("Value")
    for key, value in dict.items():
        if format_fn:
            row = format_fn(key, value)
            table.add_row(key, row.get(key), style=row.get("style"))
        else:
            table.add_row(key, value)
    rich.print(table)

#--------------------------------------------------
# Custom help printer
#--------------------------------------------------


class RichGroup(click.Group):
    def format_help(self, ctx: Context, formatter: HelpFormatter) -> None:
        is_latest, current_ver, latest_ver = is_latest_cli_version()

        global PROFILE
        # @NOTE: I couldn't find a sane way to access the --profile option from here, so insane it is.
        if "--profile" in sys.argv:
            ix = sys.argv.index("--profile") + 1
            if ix < len(sys.argv):
                PROFILE = sys.argv[ix]

        profile = get_config().profile
        if profile == TOP_LEVEL_PROFILE_NAME:
            profile = "[yellow bold]None[/yellow bold]" if not get_config().get("platform", "") else "[ROOT]"

        sio = io.StringIO()
        console = Console(file=sio, force_terminal=True)
        divider(console)
        console.print(f"[bold]Welcome to [green]RelationalAI[/bold] ({current_ver})!")
        console.print()
        if not is_latest:
            console.print(f"[yellow]A new version of RelationalAI is available: {latest_ver}[/yellow] ")
            console.print()
        console.print("rai [magenta]\\[options][/magenta] [cyan]command[/cyan]")

        console.print()
        console.print(f"[magenta]--profile[/magenta][dim] - which config profile to use (current: [/dim][cyan]{profile}[/cyan][dim])")

        unavailable_commands = []
        groups = defaultdict(list)
        for command in self.commands.keys():
            if ":" in command:
                group, _, _ = command.rpartition(":")
                groups[group].append(command)
            else:
                groups[""].append(command)

        console.print()
        for command in groups[""]:
            console.print(f"[cyan]{command}[/cyan][dim] - {self.commands[command].help}")

        for group, commands in groups.items():
            if not group:
                continue

            empty = True
            for command in commands:
                if command_available(self.commands[command]):
                    if empty:
                        empty = False
                        console.print()

                    console.print(f"[cyan]{command}[/cyan][dim] - {self.commands[command].help}")
                else:
                    unavailable_commands.append(command)

        if unavailable_commands:
            platform = get_config().get("platform", "")
            console.print()
            console.print(f"[yellow]Not available on {platform}[/yellow]")
            console.print()
            for command in unavailable_commands:
                console.print(f"[dim yellow]{command} - {self.commands[command].help}")

        divider(console)
        formatter.write(sio.getvalue())
        sio.close()

def filter_profiles_by_platform(config:ConfigFile, platform:str):
    filtered_config = {}
    for profile, props in config.get_combined_profiles().items():
        if profile == TOP_LEVEL_PROFILE_NAME:
            continue
        if props.get("platform") == platform or (
            props.get("platform") is None
            and platform == "azure"
        ):
            filtered_config[profile] = props
    return filtered_config

#--------------------------------------------------
# Imports list
#--------------------------------------------------

def show_imports(imports, showId=False):
    ensure_config()
    if len(imports):
        table = Table(show_header=True, border_style="dim", header_style="bold", box=rich_box.SIMPLE_HEAD)
        cols = {"#": "index"}
        if showId and len(imports) and "id" in imports[0]:
            cols["ID"] = "id"
        if len(imports) and "name" in imports[0]:
            cols["Name"] = "name"
        if len(imports) and "model" in imports[0]:
            cols["Model"] = "model"
        if len(imports) and "created" in imports[0]:
            cols["Created"] = "created"
        if len(imports) and "creator" in imports[0]:
            cols["Creator"] = "creator"
        if len(imports) and "batches" in imports[0]:
            cols["Batches"] = "batches"
        if len(imports) and "status" in imports[0]:
            cols["Status"] = "status"
        if len(imports) and "errors" in imports[0]:
            cols["Errors"] = "errors"

        for label in cols.keys():
            table.add_column(label)

        for index, imp in enumerate(imports):
            imp["index"] = f"{index+1}"
            style = get_color_by_state(imp["status"])
            if imp["created"]:
                imp["created"] = format_value(imp["created"])
            table.add_row(*[imp.get(attr, None) for attr in cols.values()], style=style)
        rich.print(table)
    else:
        rich.print("[yellow]No imports found")

#--------------------------------------------------
# Transactions
#--------------------------------------------------

def show_transactions(transactions, limit):
    if len(transactions):
        table = Table(show_header=True, border_style="dim", header_style="bold", box=rich_box.SIMPLE_HEAD)
        table.add_column("#")
        table.add_column("ID")
        table.add_column("Schema")
        table.add_column("Engine")
        table.add_column("State")
        table.add_column("Created")
        table.add_column("Duration", justify="right")

        added = 0
        for i, txn in enumerate(transactions):
            if added >= limit:
                break

            state = txn.get("state", "")
            duration = txn.get("duration")
            created_on = txn.get("created_on")

            if isinstance(created_on, int):
                created_on = datetime.fromtimestamp(created_on / 1000, tz=pytz.utc)
            if duration is None:
                duration = (datetime.now(created_on.tzinfo) - created_on).total_seconds() * 1000

            table.add_row(
                f"{i+1}",
                txn.get("id"),
                txn.get("database", ""),
                txn.get("engine", ""),
                state,
                created_on.strftime("%Y-%m-%d %H:%M:%S"),
                humanized_duration(int(duration)),
                style=get_color_by_state(state)
            )
            added += 1
        rich.print(table)
    else:
        rich.print("[yellow]No transactions found")

def show_engines(engines):
    if len(engines):
        table = Table(show_header=True, border_style="dim", header_style="bold", box=rich_box.SIMPLE_HEAD)
        table.add_column("#")
        table.add_column("Name")
        table.add_column("Size")
        table.add_column("State")
        for index, engine in enumerate(engines):
            table.add_row(f"{index+1}", engine.get("name"), engine.get("size"), engine.get("state"))
        rich.print(table)

def exit_with_error(message:str):
    rich.print(message, file=sys.stderr)
    exit_with_divider(1)

def exit_with_divider(exit_code:int=0):
    divider()
    sys.exit(exit_code)
