import retracesoftware.stream as stream
from retracesoftware.run import install, run_with_retrace, ImmutableTypes, thread_states
import argparse
import sys
from pathlib import Path
from retracesoftware.proxy.thread import thread_id
from retracesoftware.proxy.replay import ReplayProxySystem
import retracesoftware.utils as utils
import json
from retracesoftware.stackdifference import on_stack_difference

def parse_args():
    parser = argparse.ArgumentParser(
        prog=f"python -m {sys.argv[0]}",
        description="Run a Python module with debugging, logging, etc."
    )

    parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='Enable verbose output'
    )

    parser.add_argument(
        '--timeout',   # or '-r'
        type = int,      # ensures it's a string (optional, but safe)
        default = 60,    # default value if not provided
        help = 'the directory to place the recording files'
    )

    parser.add_argument(
        '--recording',   # or '-r'
        type = str,      # ensures it's a string (optional, but safe)
        default = '.',    # default value if not provided
        help = 'the directory to place the recording files'
    )

    return parser.parse_args()

def load_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    # import debugpy

    # port = 1977
    # debugpy.listen(("127.0.0.1", port))
    # debugpy.wait_for_client()

        # self.reader = stream.reader(path, 
        #                             thread = thread_id,
        #                             timeout_seconds = 60,
        #                             verbose = verbose,
        #                             on_stack_difference = thread_state.wrap('disabled', on_stack_difference),
        #                             magic_markers = magic_markers)

    # return ReplayProxySystem(thread_state = thread_state, 
    #                             immutable_types = immutable_types,
    #                             tracing_config = tracing_config,
    #                             mainscript = mainscript,
    #                             path = recording_path / 'trace.bin',
    #                             tracecalls = env_truthy('RETRACE_ALL', False),
    #                             verbose = verbose,
    #                             magic_markers = env_truthy('RETRACE_MAGIC_MARKERS', False))

    args = parse_args()    
    path = Path(args.recording)

    if not path.exists():
        raise Exception(f"Recording path: {path} does not exist")

    settings = load_json(path / "settings.json")

    thread_state = utils.ThreadState(*thread_states)

    with stream.reader(path = path / 'trace.bin',
                       thread = thread_id, 
                       timeout_seconds = args.timeout,
                       verbose = args.verbose,
                       on_stack_difference = thread_state.wrap('disabled', on_stack_difference),
                       magic_markers = settings['magic_markers']) as reader:

        tracing_config = {}

        system = ReplayProxySystem(
            reader = reader,
            thread_state = thread_state,
            immutable_types = ImmutableTypes(), 
            tracing_config = tracing_config,
            tracecalls = settings['trace_inputs'])

        install(system)

        run_with_retrace(system, settings['argv'])

        # install(system)

        # run_with_retrace(system, args.rest[1:])

        # runpy.run_module('foo', run_name="__main__", alter_sys=False)

if __name__ == "__main__":
    main()