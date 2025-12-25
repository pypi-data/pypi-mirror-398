import retracesoftware.functional as functional
import retracesoftware_utils as utils
from retracesoftware.proxy.proxytype import Proxy

from retracesoftware.proxy.serializer import serializer

import types
import os
import sys
import functools

def format_kwargs(kwargs):
    result = []
    for k, v in kwargs.items():
        result.extend([f"{k} = ", v])

    return tuple(result)

class CallTracer:

    ignore = set([('abc', '__subclasscheck__'),
                  ('threading', '_shutdown'),
                  ('typing', 'inner')])
    
    def __init__(self, writer, thread_state):
        self.writer = writer
        self.thread_state = thread_state

    def on_result(self, result):
        if type(result) in [str]:
            self.writer(result)
        else:
            self.writer(str(type(result)))

    def on_error(self, exc_type, exc_value, exc_traceback):
        pass

    def __call__(self, frame):
        if self.thread_state.value == 'internal':
            with self.thread_state.select('disabled'):
                func = frame.function
                        
                key = (func.__module__, func.__name__)

                if key not in CallTracer.ignore and func.__name__ != '__hash__':
                    self.writer(f'{func.__module__}.{func.__name__}')
                    return self
        else:
            return lambda *args, **kwargs: self(*args, **kwargs)
    
class Tracer:

    def __init__(self, config, writer):
        self.config = config
        serialize = serializer
        # functional.walker(self.serialize)
        self.writer = functional.mapargs(transform = serialize, function = writer)

    def systrace(self, frame, event, arg):
        try:
            if event in ['line', 'call']:
                print(f'In systrace: {event} {frame.f_code.co_filename}:{frame.f_lineno}')
                self.writer(event, frame.f_code.co_filename, frame.f_code.co_name, frame.f_lineno)

            elif event == 'return':
                print(f'In systrace: {event}')
                self.writer(event)
                # self.writer(event, self.serialize(arg))

            elif event == 'exception':
                print(f'In systrace: {event}')
                self.writer(event)
            else:
                print(f'In systrace: {event}')

            return self.systrace
        except:
            print(f'systrace RAISED ERROR!')
            raise

    # def trace_calls(self, thread_state):
    #     if 'tracecalls' in self.config:
    #         # def on_call(frame):

    #         #     func = frame.function
                
    #         #     key = (func.__module__, func.__name__)

    #         #     ignore = set([('abc', '__subclasscheck__'),
    #         #                   ('threading', '_shutdown')])

    #         #     if key in ignore:
    #         #         print('About to throw!!!')
    #         #         raise Exception()

    #         #     objtype = None

    #         #     if 'self' in frame.locals:
    #         #         this = frame.locals['self']
    #         #         objtype = type(this)

    #         #     # if objtype:
    #         #     #     print(f'Called!!!!: {func.__module__}.{objtype.__name__}.{func.__name__}')
    #         #     # else:
    #         #     #     print(f'Called!!!!: {func.__module__}.{func.__name__}')

    #         #     qualname = (func.__module__, objtype, func.__name__)

    #         #     self.writer(f'{func.__module__}.{func.__name__}')

    #         #     # if func.__name__ == '_path_stat':
    #         #     #     utils.sigtrap('_path_stat start')

    #         #     return qualname

    #         # def on_result(qualname, res):
    #         #     mod, obj, func = qualname

    #         #     # if obj:
    #         #     #     print(f'Returning!!!!: {mod}.{obj}.{func}')
    #         #     # else:
    #         #     #     print(f'Returning!!!!: {mod}.{func}')

    #         #     # if func == '_path_stat':
    #         #     #     utils.sigtrap('_path_stat res')

    #         #     if func != '__hash__':
    #         #         ignore = set(('typing', 'inner'))

    #         #         if qualname not in ignore:
    #         #             if type(res) in [str, int]:
    #         #                 self.writer(res)
    #         #             else:
    #         #                 self.writer(str(type(res)))

    #         # def on_call_disabled(frame):
    #         #     func = frame.function
    #         #     print(f'disabled: {func.__module__}.{func.__name__}')
            
    #         callback = CallTracer(writer = self.writer, thread_state = thread_state)
    #         utils.intercept_frame_eval(callback)
                                       
    # def serialize(self, obj):
    #     try:
    #         if obj is None: return None

    #         cls = functional.typeof(obj)

    #         if issubclass(cls, Proxy):
    #             return str(cls)
            
    #         if issubclass(cls, (int, str)):
    #             return obj

    #         return str(cls)
            
    #         # if issubclass(cls, Proxy):
    #         #     return f'<Proxy>'

    #         # if issubclass(cls, types.TracebackType):
    #         #     return '<traceback>'
            
    #         # elif issubclass(cls, utils.wrapped_function):
    #         #     return utils.unwrap(obj).__name__
            
    #         # elif hasattr(obj, '__module__') and hasattr(obj, '__name__'):
    #         #     return f'{obj.__module__}.{obj.__name__}'
    #         # # elif isinstance(obj, type):
    #         # #     return f'{obj.__module__}.{obj.__name__}'
    #         # else:
    #         #     return '<other>'
    #         #     # return f'instance type: {str(self.serialize(type(obj)))}'
    #     except:
    #         print("ERROR in tracer serialize!!!!")
    #         os._exit(1)

    def log(self, name, message):
        if name in self.config:
            self.writer(name, message)
         
    def checkpoint(self, obj):
        self.writer(obj)

    # def stacktrace(self):
    #     self.writer('stacktrace', utils.stacktrace())

    def _write_call(self, name, *args, **kwargs):
        # self.stacktrace()
        if len(args) > 0:
            funcname = args[0].__name__
            # if funcname == '__del__':
            #     utils.sigtrap('FOO')

            self.writer(name, funcname, args[1:], kwargs)
        else:
            utils.sigtrap('FOO')
            breakpoint()

    def __call__(self, name, func = None):
        if name in self.config:
            if name.endswith('.call'):
                f = functools.partial(self._write_call, name)
                return functional.firstof(f, func) if func else f
            
            elif name.endswith('.result'):
                def write_result(obj):
                    self.writer(name, obj)
                    return obj
                
                return functional.sequence(func, write_result) if func else write_result
            
            elif name.endswith('.error'):
                def write_error(*args):
                    self.writer(name, args)
            
                return functional.firstof(write_error, func) if func else write_error

            elif name.endswith('.event'):
                def write_event(*args, **kwargs):
                    self.writer(name)

                return functional.firstof(write_event, func) if func else write_event
        
            elif name.endswith('.wrap'):
                def wrapper(*args, **kwargs):
                    self.writer(name, 'enter')
                    try:
                        return func(*args, **kwargs)
                    finally:
                        self.writer(name, 'exit')

                return wrapper
            
            # elif name.endswith('.stack'):
            #     def write_event(*args, **kwargs):
            #         self.writer(name, utils.stacktrace())

            #     return functional.firstof(write_event, func) if func else write_event


        return func


    def write(self, name):
        if name in self.config:
            return functional.partial(self.writer, name)

    def write_call(self, name, func = None):

        def writer(*args, **kwargs):
            self.writer(name, *(args + format_kwargs(kwargs)))

        if name in self.config:
            return functional.firstof(writer, func) if func else writer
        else:
            return func

    def write_result(self, name, func):
        
        writer = functional.partial(self.writer, name)
            
        if name in self.config:
            return functional.sequence(func, functional.side_effect(writer))
        else:
            return func

    def event(self, name):
        return functional.always(lambda: self.writer(name))

    def event_before(self, name, func = None):
        if name in self.config:
            # def foo(*args, **kwargs):
            #     print("GRRRRR!!!!!")

            # return functional.firstof(foo, func)
            return functional.firstof(self.event(name), func)
        else:
            return func

    def event_after(self, name, func):
        if name in self.config:
            return functional.sequence(func, functional.side_effect(self.event(name)))
        else:
            return func
