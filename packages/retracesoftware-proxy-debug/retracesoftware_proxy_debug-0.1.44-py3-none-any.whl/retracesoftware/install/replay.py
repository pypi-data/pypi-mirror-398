from retracesoftware.proxy import *

from retracesoftware.install import globals

import os, json, re, glob
from pathlib import Path
from datetime import datetime
from retracesoftware.install.config import env_truthy

def recordings(pattern):
    # Turn strftime placeholders into '*' for globbing
    # (very simple replacement: %... -> *)
    glob_pattern = re.sub(r"%[a-zA-Z]", "*", pattern)

    base_pattern = os.path.basename(pattern)

    # Find all matching files
    for path in glob.glob(glob_pattern):
        try:
            name = os.path.basename(path)
            datetime.strptime(name, base_pattern)
            yield path
        except:
            pass

def latest_from_pattern(pattern: str) -> str | None:
    """
    Given a strftime-style filename pattern (e.g. "recordings/%Y%m%d_%H%M%S_%f"),
    return the path to the most recent matching file, or None if no files exist.
    """
    # Derive the datetime format from the pattern (basename only)
    base_pattern = os.path.basename(pattern)

    def parse_time(path: str):
        name = os.path.basename(path)
        return datetime.strptime(name, base_pattern)

    # Find the latest by parsed timestamp
    return max(recordings(pattern), key=parse_time)

def replay_system(thread_state, immutable_types, config):

    verbose = env_truthy('RETRACE_VERBOSE', False)
    recording_path = Path(latest_from_pattern(config['recording_path']))

    # print(f"replay running against path: {recording_path}")

    globals.recording_path = globals.RecordingPath(recording_path)

    assert recording_path.exists()
    assert recording_path.is_dir()

    with open(recording_path / "env", "r", encoding="utf-8") as f:
        os.environ.update(json.load(f))

    with open(recording_path / "tracing_config.json", "r", encoding="utf-8") as f:
        tracing_config = json.load(f)

    with open(recording_path / "mainscript", "r", encoding="utf-8") as f:
        mainscript = f.read()

    call_trace_file = recording_path / "call_trace.txt"

    if call_trace_file.exists():
        class CallTracer:
            def __init__(self):
                self.file = open(call_trace_file, 'r')

            def __call__(self, obj):
                recording = json.loads(self.file.readline())
                if obj != recording:
                    breakpoint()

            def close(self):
                self.file.close()

            # def on_call(self, function_name):
            #     recording = self.file.readline()
            #     if f'call: {function_name}\n' != recording:
            #         breakpoint()

            #     assert f'call: {function_name}\n' == recording

            # def on_return(self, function_name):
            #     recording = self.file.readline()
            #     if f'return: {function_name}\n' != recording:
            #         breakpoint()

            #     assert f'return: {function_name}\n' == recording

        call_tracer = CallTracer()
    else:
        call_tracer = None

    return ReplayProxySystem(thread_state = thread_state, 
                                immutable_types = immutable_types,
                                tracing_config = tracing_config,
                                mainscript = mainscript,
                                path = recording_path / 'trace.bin',
                                tracecalls = env_truthy('RETRACE_ALL', False),
                                verbose = verbose,
                                magic_markers = env_truthy('RETRACE_MAGIC_MARKERS', False))
