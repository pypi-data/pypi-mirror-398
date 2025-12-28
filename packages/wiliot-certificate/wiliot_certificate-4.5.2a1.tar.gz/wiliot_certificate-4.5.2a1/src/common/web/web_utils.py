from __future__ import annotations
from flask import render_template, request
import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List
import os, platform, shutil, subprocess, shlex
from certificate.cert_defines import *
from certificate.cert_prints import *
from certificate.wlt_types import *

##### Defines #####

CREATE_NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010)
CFG_STRS = [
    WLT_SERVER,
    LAT,
    LNG,
    WIFI_VERSION,
    BLE_VERSION,
    GW_API_VERSION,
    SERIALIZATION_FORMAT
]
# App names
FDM = "FDM"
CERT_WEB = "CERTIFICATE WEB"

# Defines to update jinja_env globals
GLOBAL_DEFINES_TO_UPDATE = {k:v for k,v in ag.__dict__.items() if 'GROUP_ID' in k or 'API_VERSION_LATEST' in k}

TestSchema = Dict[str, Any]
ModuleSchema = Dict[str, Any]
hex_str2int = lambda x: int(x,16)
txt2html = lambda txt : str(txt).replace(" ", "&nbsp").replace("\n", "<br>").replace("\\r\\n", "<br>").replace("//", "<br>//").lstrip("b").strip('"')
def num_to_str(id):
    return str(id).zfill(2)

##### Template Handling Functions #####

def utils_data_structs(app):
    title="Enums & Packet Sructures"
    wlt_types_html = "wlt_types.html"
    return render_template('index.html',
                           app=app, title=title, wlt_types_html=wlt_types_html)

def utils_parser(app):
    title = "Packet Parser"
    output = ""
    received_payload = request.args.get('payload')
    received_payload = received_payload.upper() if received_payload else received_payload
    if received_payload:
        wlt_pkt = WltPkt(received_payload)
        if wlt_pkt.pkt != None:
            output += f"<br>Raw Packet:<br>{received_payload}<br><br>Parsed Packet:<br>{wlt_pkt}"
        else:
            output += "<br>Unable to parse received payload!"
    print(f"output: {output}")
    return render_template('parser.html',
                            app=app, title=title, output=txt2html(output))

def utils_generator(app):
    title = "Packet Generator"
    output = ""
    def parse_int_input(x, default=0):
        x = str(x).strip()
        if x.startswith('0x') or x.startswith('0X'):
            return int(x, 16)
        try:
            return int(x)
        except ValueError:
            return default
    
    def build_and_dump_pkt(pkt_type):
        pkt_template = getattr(ag, pkt_type)()
        pkt_params = {
            k: parse_int_input(request.args.get(f"{pkt_type}_{k}"), pkt_template.__dict__.get(k, 0))
            for k in pkt_template.__dict__.keys()
        }
        pkt = getattr(ag, pkt_type)(**pkt_params)
        try:
            return pkt.dump()
        except Exception as e:
            return f"<br>Error encoding {pkt_type} (bit structure error): {str(e)}<br>"
    
    # Build packet types dictionary
    dont_generate_strs = ["Cfg", "SideInfo"]
    wlt_pkt_types = {
        'Hdr': ag.Hdr(),
        'DataHdr': ag.DataHdr(),
        **{cls.__name__: cls() for cls in ag.WLT_PKT_TYPES if not any([dg in cls.__name__ for dg in dont_generate_strs])}
    }
    
    # Categorize packets and extract API versions
    import re
    pkt_metadata = {}
    for pkt_name in list(wlt_pkt_types.keys())[2:]:  # Skip Hdr and DataHdr
        # Determine category
        if pkt_name.startswith('Unified'):
            category = 'Unified'
        elif pkt_name.startswith('Module'):
            category = 'Module'
        elif pkt_name.startswith('Action'):
            category = 'Action'
        elif pkt_name.startswith('Brg2Brg'):
            category = 'Brg2Brg'
        elif pkt_name.startswith('Brg2Gw'):
            category = 'Brg2Gw'
        elif pkt_name.startswith('Sensor'):
            category = 'Sensor'
        else:
            category = 'Other'
        
        # Extract API version
        version_match = re.search(r'V(\d+)$', pkt_name)
        api_version = version_match.group(1) if version_match else None
        
        pkt_metadata[pkt_name] = {
            'category': category,
            'api_version': api_version
        }
    
    # Get unique categories and API versions for filters
    categories = sorted(set(m['category'] for m in pkt_metadata.values()))
    api_versions = sorted(set(m['api_version'] for m in pkt_metadata.values() if m['api_version']), 
                         key=lambda x: int(x) if x else 0, reverse=True)
    
    wanted_pkt_type = request.args.get('radios')
    if wanted_pkt_type:
        # Determine header type and build header
        hdr_type = 'DataHdr' if 'Unified' in wanted_pkt_type else 'Hdr'
        output += build_and_dump_pkt(hdr_type)
        output += build_and_dump_pkt(wanted_pkt_type)
    
    # Get filter values to preserve them
    filter_category = request.args.get('filter_category', '')
    filter_version = request.args.get('filter_version', '')
    
    # Get all form values to preserve them (convert MultiDict to regular dict, taking first value)
    form_values = {k: v for k, v in request.args.items()}
    
    print(output)
    return render_template('generator.html',
                            app=app, title=title, output=txt2html(output),
                            pkt_types=wlt_pkt_types, pkt_types_list=list(wlt_pkt_types.keys())[2:],
                            pkt_metadata=pkt_metadata, categories=categories, api_versions=api_versions,
                            wanted_pkt_type=wanted_pkt_type, form_values=form_values,
                            filter_category=filter_category, filter_version=filter_version)

def utils_tag2brg(app):
    title = "Tag to Bridge Packet Converter"
    output = ""
    # Get the inputs
    payload = request.args.get('payload')
    payload = payload.upper() if payload else payload

    brg_id = request.args.get('brg_id')
    brg_id = brg_id.upper() if brg_id else brg_id
    rssi = request.args.get('rssi')
    tbc = request.args.get('tbc')
    nfpkt = request.args.get('nfpkt')
    brg_latency = request.args.get('brg_latency')

    if payload and brg_id and rssi and tbc and nfpkt and brg_latency:
        try:
            if len(payload) < 37 * 2:
                raise Exception("The payload should be of size 37 bytes!")
            
            hdr = ag.DataHdr(group_id_minor=hex_str2int(payload[20:24]), group_id_major=ag.GROUP_ID_UNIFIED_PKT_V1, pkt_type=hex_str2int(payload[24:26]))
    
            # Convert inputs to appropriate types
            rssi = int(rssi)
            tbc = int(tbc)
            nfpkt = int(nfpkt)
            brg_latency = int(brg_latency)

            # Create the bridge packet
            brg_pkt = ag.UnifiedEchoPktV1(
                nonce_n_unique_id=hex_str2int(payload[26:46]),
                tbc=tbc,
                rssi=rssi,
                brg_latency=brg_latency,
                nfpkt=nfpkt,
                mic=hex_str2int(payload[52:58]),
                data=hex_str2int(payload[58:74])
            )

            output += "Bridge Packet:<br>"
            output += brg_id
            output += hdr.dump()
            output += brg_pkt.dump()
        except Exception as e:
            output = f"Error processing packet: {str(e)}"
    else:
        output = "Please fill in all required fields"

    return render_template('tag2brg.html',
                         app=app, title=title,
                         output=txt2html(output))

##### Utility Functions #####

def action_to_field(a: argparse.Action) -> Dict[str, Any]:
    # field name = dest
    name = a.dest

    # Basic widget inference
    choices = list(a.choices) if getattr(a, "choices", None) else None
    is_multi = a.nargs in ("+", "*")  # '+' = at least one, '*' = zero or more
    is_flag = isinstance(a, (argparse._StoreTrueAction, argparse._StoreFalseAction))
    
    html_type = "checkbox" if is_flag else "text"
    widget = "input"
    if choices and is_multi:
        widget, html_type = "checkbox_group", "checkbox"
    elif choices:
        widget, html_type = "select", "text"

    default = None if a.default is argparse.SUPPRESS else a.default

    # Extract URL from help text if present
    help_text = (a.help or "").strip()
    help_link = None
    if help_text:
        # Match URLs (http:// or https:// followed by non-whitespace characters)
        url_pattern = r'https?://[^\s]+'
        url_match = re.search(url_pattern, help_text)
        if url_match:
            help_link = url_match.group(0)
            # Remove URL from help text to avoid duplication
            help_text = re.sub(url_pattern, '', help_text).strip()
    return {
        "name": name,
        "label": (a.help or name).split('.')[0].strip().title(),
        "help": help_text,
        "help_link": help_link,
        "required": bool(getattr(a, "required", False)) or (not a.option_strings),
        "default": default,
        "choices": choices,
        "nargs": a.nargs,
        "type": html_type,
        "widget": widget,
        "is_flag": is_flag,
        "option_strings": a.option_strings,
    }

def parser_to_schema(parser: argparse.ArgumentParser) -> Dict[str, Any]:
    fields: List[Dict[str, Any]] = []
    for a in parser._actions:
        if argparse.SUPPRESS in a.help: continue
        if isinstance(a, (argparse._HelpAction, argparse._VersionAction)):
            continue
        fields.append(action_to_field(a))
    return {
        "title": parser.prog or "CLI",
        "description": parser.description or "",
        "fields": fields,
    }

def open_in_terminal(base_cmd: list[str], preferred: str = "auto"):
    """
    base_cmd: e.g. ["wlt-cert-cli", "--gw", "SIM", "--brg", "XYZ", ...]
    preferred: terminal choice ("auto", "terminal", "iterm", "cmd", "powershell", "gnome-terminal", etc.)
    Returns Popen handle (may be None-like if osascript exits immediately).
    """
    system = platform.system()
    _as_quote_for_applescript = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')

    if system == "Windows":
        term = preferred.lower()
        # On Windows, use subprocess.list2cmdline for proper Windows command line formatting
        import subprocess as sp
        cmd_line = sp.list2cmdline(base_cmd)
        if term in ("auto", "cmd"):
            return subprocess.Popen(["cmd.exe", "/k", cmd_line], creationflags=CREATE_NEW_CONSOLE)
        if term == "powershell":
            return subprocess.Popen(["powershell.exe", "-NoExit", "-Command", cmd_line], creationflags=CREATE_NEW_CONSOLE)
        # Default to cmd
        return subprocess.Popen(["cmd.exe", "/k", cmd_line], creationflags=CREATE_NEW_CONSOLE)
    
    # For non-Windows systems, use shlex.join (POSIX-safe)
    cmd_str = shlex.join(base_cmd)

    if system == "Darwin":  # macOS
        term = preferred.lower()
        shell = os.environ.get("SHELL", "/bin/zsh")
        # Run in login shell (loads PATH/env) and keep window open
        inner = f'{shell} -lc {shlex.quote(cmd_str + f"; exec {shell}")}'

        if term in ("auto", "terminal"):
            scpt_activate = 'tell application "Terminal" to activate'
            scpt_run = 'tell application "Terminal" to do script "{}"'.format(
                _as_quote_for_applescript(inner)
            )
            return subprocess.Popen(["osascript", "-e", scpt_activate, "-e", scpt_run])

        if term in ("iterm", "iterm2"):
            scpt = (
                'tell application "iTerm"\n'
                '  if (count of windows) = 0 then create window with default profile\n'
                '  tell current session of current window to write text "{}"\n'
                '  activate\n'
                'end tell'.format(_as_quote_for_applescript(inner))
            )
            return subprocess.Popen(["osascript", "-e", scpt])

        # fallback to Terminal
        scpt_activate = 'tell application "Terminal" to activate'
        scpt_run = 'tell application "Terminal" to do script "{}"'.format(
            _as_quote_for_applescript(inner)
        )
        return subprocess.Popen(["osascript", "-e", scpt_activate, "-e", scpt_run])

    # Linux / Unix
    term = preferred
    def have(x): return shutil.which(x) is not None
    if term == "auto":
        for t in ("gnome-terminal", "konsole", "xfce4-terminal", "xterm"):
            if have(t):
                term = t
                break
    if term == "gnome-terminal":
        return subprocess.Popen(["gnome-terminal", "--", "bash", "-lc", cmd_str + "; exec bash"])
    if term == "konsole":
        return subprocess.Popen(["konsole", "-e", "bash", "-lc", cmd_str + "; exec bash"])
    if term == "xfce4-terminal":
        return subprocess.Popen(["xfce4-terminal", "--command", f"bash -lc {shlex.quote(cmd_str)}; exec bash"])
    if term == "xterm":
        return subprocess.Popen(["xterm", "-e", f"bash -lc {shlex.quote(cmd_str)}; exec bash"])

    # last resort: run without opening a new terminal
    return subprocess.Popen(base_cmd)

def _read_json_safe(p: Path) -> Dict[str, Any]:
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
    
def scan_tests_dir(root: str | Path) -> Dict[str, Any]:
    """
    Expect: <root>/<module>/<test>/{<test>.py, <test>.json}
    Returns:
      {
        "root": "<abs>",
        "modules": [
          {"name": "datapath", "path": ".../datapath", "tests": [
            {"id": "datapath/interval_test", "module": "datapath", "name": "interval_test",
             "label": "interval test", "dir": "...", "py": ".../interval_test.py",
             "json_path": ".../interval_test.json", "meta": {...}, "tooltip": "..." }
          ]},
          ...
        ],
        "id_to_py": {"datapath/interval_test": ".../interval_test.py", ...}
      }
    """
    root = Path(root).resolve()
    modules: List[ModuleSchema] = []
    id_to_py: Dict[str, str] = {}

    if not root.exists():
        return {"root": str(root), "modules": [], "id_to_py": {}}

    for mod_dir in sorted([p for p in root.iterdir() if p.is_dir()]):
        if mod_dir.name == 'ut': continue
        tests: List[TestSchema] = []
        for test_dir in sorted([p for p in mod_dir.iterdir() if p.is_dir()]):
            if test_dir.name == 'ut' or test_dir.name == 'registration_test': continue
            # prefer <dir>/<dir>.py then first *.py
            py = test_dir / (test_dir.name + ".py")
            if not py.exists():
                py = next(test_dir.glob("*.py"), None)
            # prefer <dir>/<dir>.json then first *.json
            j = test_dir / (test_dir.name + ".json")
            if not j.exists():
                j = next(test_dir.glob("*.json"), None)

            meta = _read_json_safe(j) if j else {}
            tid = f"{mod_dir.name}/{test_dir.name}"
            item = {
                "id": tid,
                "module": mod_dir.name,
                "name": test_dir.name,
                "label": meta.get('name', test_dir.name.replace("_", " ")),
                "dir": str(test_dir),
                "py": str(py) if py else "",
                "json_path": str(j) if j else "",
                "meta": meta,
                "tooltip": meta.get('purpose', ""),
            }
            tests.append(item)
            if py:
                id_to_py[tid] = str(py)

        if tests:
            modules.append({"name": mod_dir.name, "path": str(mod_dir), "tests": tests})

    return {"root": str(root), "modules": modules, "id_to_py": id_to_py}
