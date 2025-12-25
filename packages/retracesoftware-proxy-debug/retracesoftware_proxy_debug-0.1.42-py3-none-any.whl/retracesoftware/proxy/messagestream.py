from ast import dump
from math import e
import retracesoftware.stream as stream
import retracesoftware_utils as utils
from retracesoftware.proxy.startthread import thread_id
import gc
import sys
import itertools
import threading

class ResultMessage:
    def __init__(self, result):
        self.result = result

    def __str__(self):
        return f'ResultMessage({self.result})'

    def __repr__(self):
        return f'ResultMessage({self.result})'

class ErrorMessage:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __call__(self):
        utils.raise_exception(self.type, self.value)

class CallMessage:
    def __init__(self, func, args, kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        try:
            self.func(*self.args, **self.kwargs)
        except BaseException:
            pass
        return None

class CheckpointMessage:
    def __init__(self, value):
        self.value = value

class GCStartMessage:
    def __init__(self, value):
        self.value = value

    def __call__(self):
        gc.collect(self.value)

def next_message(source):
    message = source()

    if message == 'CALL':
        return CallMessage(source(), source(), source())
    elif message == 'RESULT':
        return ResultMessage(source())
    elif message == 'ERROR':
        return ErrorMessage(source(), source())
    elif message == 'CHECKPOINT':
        return CheckpointMessage(source())
    elif message == 'ON_START_COLLECT':
        return GCStartMessage(source())
    else:
        return message

def all_elements_same(t):
    return len(set(t)) <= 1

def first(coll): return coll[0]

def common_prefix(*colls):
    return list(map(first, itertools.takewhile(all_elements_same, zip(*colls))))

def print_stack(stack):
    for filename, lineno in stack:
        print(f'{filename}:{lineno}', file = sys.stderr)

def on_stack_difference(previous, record, replay):

    common = common_prefix(previous, record, replay) if previous else common_prefix(record, replay)
        
    if common:
        print('Common root:')
        print_stack(common)

    if previous:
        print('\nlast matching:')
        print_stack(previous[len(common):])

    print('\nrecord:')
    print_stack(record[len(common):])

    print('\nreplay:')
    print_stack(replay[len(common):])

    utils.sigtrap(None)

class MessageStream:

    def __init__(self, thread_state, source, skip_weakref_callbacks, verbose):
        self.source = stream.per_thread(source = source, thread = thread_id, timeout = 1000)
        self.verbose = verbose

        self.excludes = set([
            MessageStream.__call__,
            MessageStream.bind,
            MessageStream.checkpoint,
            MessageStream.on_stack,
            MessageStream.read_required,
            MessageStream.result.__wrapped__,
            stream.stack,
        ])

        self.threadlocal = threading.local()
        self.thread_state = thread_state
        self.stack_messages = set([])
        self.skip_weakref_callbacks = skip_weakref_callbacks

    def on_stack(self, record):        
        replay = stream.stack(self.excludes)

        if replay != record:
            on_stack_difference(self.threadlocal.stacktrace, record, replay)

        self.threadlocal.stacktrace = record

    def dump_and_exit(self):
        with self.thread_state.select('disabled'):
            if hasattr(self.threadlocal, 'stacktrace'):
                print('Last matching stacktrace:')
                print_stack(self.threadlocal.stacktrace)

            print('Current stacktrace:')
            print_stack(stream.stack(set()))
            utils.sigtrap(None)

    def checkpoint(self, obj):
        if self.verbose:
            print(f'checkpointing: {obj}')

        next = self()

        if isinstance(next, CheckpointMessage):
            if obj != next.value:
                print(f'CHECKPOINT, expected: {obj} but got {next.value}', file=sys.stderr)
                self.dump_and_exit()
        else:
            print(f'expected CHECKPOINT message but got {next}', file=sys.stderr)
            self.dump_and_exit()
        
    def bind(self, obj):

        next = self()

        if isinstance(next, stream.Bind):
            next.value(obj)
        else:
            print(f'expected BIND message but got {next}', file=sys.stderr)
            self.dump_and_exit()

    def read_required(self, required):
        next = self()

        if next != required:
            print(f'expected {required} message but got {next}', file=sys.stderr)
            self.dump_and_exit()

    def consume_to(self, to):
        message = next_message(self.source)
        while message != to:
            message = next_message(self.source)

    def __call__(self):
        with self.thread_state.select('disabled'):
            while True:
                message = next_message(self.source)

                if isinstance(message, CallMessage):
                    message()
                elif isinstance(message, stream.Stack):
                    self.on_stack(message.value)                
                elif isinstance(message, GCStartMessage):
                    message()
                    self.read_required('ON_END_COLLECT')
                elif self.skip_weakref_callbacks and message == 'ON_WEAKREF_CALLBACK_START':
                    self.consume_to('ON_WEAKREF_CALLBACK_END')
                else:
                    return message

    @utils.striptraceback
    def result(self):

        message = self()

        if isinstance(message, ResultMessage):
            return message.result
        elif isinstance(message, ErrorMessage):
            message()
        else:
            print(f'expected RESULT or ERROR message but got {message}', file=sys.stderr)
            self.dump_and_exit()
