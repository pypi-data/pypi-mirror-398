import retracesoftware.functional as functional
import retracesoftware_utils as utils

from retracesoftware.proxy.proxytype import ExtendingProxy

# from retracesoftware.proxy.proxytype import ExtendingProxy

# unproxy_execute = functional.mapargs(starting = 1, 
#                                      transform = functional.walker(utils.try_unwrap), 
#                                      function = functional.apply)

def adapter(function,
            proxy_input,
            proxy_output,
            on_call = None,
            on_result = None,
            on_error = None):

    # function = functional.apply

    if on_call: function = utils.observer(on_call = on_call, function = function)

    #functional.observer(on_call = on_call, function = function)

    function = functional.mapargs(starting = 1, transform = proxy_input, function = function)

    function = functional.sequence(function, proxy_output)

    if on_result or on_error:
        function = utils.observer(on_result = on_result, on_error = on_error, function = function)

    return function

def adapter_pair(int, ext):
    return (
        adapter(
            function = ext.apply,
            proxy_input = int.proxy,
            proxy_output = ext.proxy,
            on_call = ext.on_call,
            on_result = ext.on_result,
            on_error = ext.on_error),
        adapter(
            function = int.apply,
            proxy_input = ext.proxy,
            proxy_output = int.proxy,
            on_call = int.on_call,
            on_result = int.on_result,
            on_error = int.on_error))
