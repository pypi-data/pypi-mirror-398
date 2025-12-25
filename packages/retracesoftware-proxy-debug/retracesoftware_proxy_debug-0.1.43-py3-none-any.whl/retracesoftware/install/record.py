from retracesoftware.proxy import *

import retracesoftware.functional as functional
import retracesoftware_utils as utils
import retracesoftware.stream as stream

from retracesoftware.install.tracer import Tracer
from retracesoftware.install import globals
from retracesoftware.install.config import env_truthy
from retracesoftware.install.patchfindspec import patch_find_spec

import os
import sys
from datetime import datetime
import json
from pathlib import Path
import shutil

# class ThreadSwitch:
#     def __init__(self, id):
#         self.id = id

#     def __repr__(self):
#         return f'ThreadSwitch<{self.id}>'

#     def __str__(self):
#         return f'ThreadSwitch<{self.id}>'

def code_workspace():
    return {
        'folders': [
            {'path': '../..', 'name': 'Application'},
            {'path': '.', 'name': 'Recording'}
        ]
    }

def write_files(recording_path):
    with open(recording_path / 'env', 'w') as f:
        json.dump(dict(os.environ), f, indent=2)

    with open(recording_path / 'exe', 'w') as f:
        f.write(sys.executable)

    with open(recording_path / 'cwd', 'w') as f:
        f.write(os.getcwd())

    with open(recording_path / 'cmd', 'w') as f:
        json.dump(sys.orig_argv, f, indent=2)

    with open(recording_path / 'replay.code-workspace', 'w') as f:
        json.dump(code_workspace(), f, indent=2)
    
def create_recording_path(path):
    expanded = datetime.now().strftime(path.format(pid = os.getpid()))
    os.environ['RETRACE_RECORDING_PATH'] = expanded
    return Path(expanded)

def tracing_level(config):
    return os.environ.get('RETRACE_DEBUG', config['default_tracing_level'])

# def tracing_config(config):
#     level = os.environ.get('RETRACE_DEBUG', config['default_tracing_level'])
#     return config['tracing_levels'].get(level, {})

def merge_config(base, override):
    if isinstance(base, dict) and isinstance(override, dict):
        ...
    else:
        return override



def dump_as_json(path, obj):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)

def record_system(thread_state, immutable_types, config):

    recording_path = create_recording_path(config['recording_path'])
    recording_path.mkdir(parents=True, exist_ok=True)

    globals.recording_path = globals.RecordingPath(recording_path)

    write_files(recording_path)

    tracing_config = config['tracing_levels'].get(tracing_level(config), {})

    dump_as_json(path = recording_path / 'tracing_config.json', obj = tracing_config)

    def write_main_path(path):
        with open(recording_path / 'mainscript', 'w') as f:
            f.write(path)

    run_path = recording_path / 'run'
    run_path.mkdir(parents=True, exist_ok=False)

    shutil.copy2(sys.argv[0], run_path)

    python_path = recording_path / 'pythonpath'
    python_path.mkdir(parents=True, exist_ok=False)

    vscode = recording_path / '.vscode'
    vscode.mkdir(parents=True, exist_ok=False)

    # launch_json = {
    #     # // Use IntelliSense to learn about possible attributes.
    #     # // Hover to view descriptions of existing attributes.
    #     # // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    #     "version": "0.2.0",
    #     "configurations": [
    #         {
    #             "name": "Python Debugger: Python File",
    #             "type": "debugpy",
    #             "request": "launch",
    #             "cwd": "${workspaceFolder}/run",
    #             "env": {
    #                 "RETRACE_MODE": "replay"
    #             },
    #             "python": sys.executable,
    #             "program": sys.argv[0]
    #         }
    #     ]
    # }

    # dump_as_json(vscode / 'launch.json', launch_json)

    workspace = {
        "folders": [{ 'path': '.' }],
        "settings": {
            # This is the one that works reliably in .code-workspace files
            # "python.defaultInterpreterPath":
            "python.defaultInterpreterPath": sys.executable,
            # "python.interpreterInfo": {
            #     "run": {"path": sys.executable}
            # }
        },
        "launch": {
            "version": "0.2.0",
            "configurations": [
                {
                    "justMyCode": False,
                    "name": "Python Debugger: Python File",
                    "type": "debugpy",
                    "request": "launch",
                    "cwd": "${workspaceFolder}/run",
                    "env": {
                        "RETRACE_RECORDING_PATH": "..",
                        "RETRACE_MODE": "replay"
                    },
                    # "python": ["${command:python.interpreterPath}"],
                    "python": sys.executable,
                    # "python": sys.executable,
                    "program": sys.argv[0]
                }
            ]
        },
    }

    dump_as_json(recording_path / 'replay.code-workspace', workspace)

    copy_source = thread_state.wrap('disabled', patch_find_spec(cwd = Path(os.getcwd()), run_path = run_path, python_path = python_path))

    for finder in sys.meta_path:
        finder.find_spec = functional.sequence(finder.find_spec, functional.side_effect(copy_source))

    return RecordProxySystem(thread_state = thread_state,
                             immutable_types = immutable_types, 
                             tracing_config = tracing_config,
                             write_main_path = write_main_path,
                             path = recording_path / 'trace.bin',
                             tracecalls = env_truthy('RETRACE_ALL', False),
                             verbose = env_truthy('RETRACE_VERBOSE', False),
                             stacktraces = env_truthy('RETRACE_STACKTRACES', False),
                             magic_markers = env_truthy('RETRACE_MAGIC_MARKERS', False))
