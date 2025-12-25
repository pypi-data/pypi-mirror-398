import retracesoftware.functional as functional
import retracesoftware.utils as utils
from retracesoftware.proxy.thread import start_new_thread_wrapper
import threading
import importlib
from retracesoftware.install.typeutils import modify, WithFlags, WithoutFlags
import enum

from retracesoftware.install.typeutils import modify
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Callable
import functools

def simple_phase(names, func):
    """
    Simplest phase type
    """
    return {name: func for name in names}

def simple_patch_phase(names, func):
    """
    Simplest phase type
    """
    def side_effect(obj):
        func(obj)
        return obj

    return {name: side_effect for name in names}

Transform = Callable[[Any], Any]
Config = Any

Updater = Dict[str, Transform]

Phase = Callable[[Config], Updater]

Patcher = Dict[str, Phase]

def update_class(cls : type, actions : Updater):
    ...

def type_attributes(patcher, config):
    result = {}

    for typename, action_attrs in config.items():

        def patch_type(cls):
            with modify(cls):
                for action, attrs in action_attrs.items():
                    update_class(cls, patcher[action](attrs))
            return cls
        
        result[typename] = patch_type
    
    return result

def create_patcher(system) -> Patcher:
    patcher = {}

    def simple_patcher(func): lambda config: {name: func for name in config}

    patcher.update({
        'type_attributes': functools.partial(type_attributes, patcher),
        'disable': simple_patcher(system.disable),
        'patch_types': simple_patcher(system.patch_type),

    })
    return patcher

class TypeAttributesPhase(Phase):

    def __init__(self, patcher):
        super().__init__('type_attributes')
        self.patcher = patcher

    def patch_with_config(self, config, cls):
        # print(f'TypeAttributesPhase: {config} {cls}')
        if not isinstance(cls, type):
            raise Exception("TODO")

        with modify(cls):
            for phase_name,values in config.items():
                for attribute_name,func in self.patcher.find_phase(phase_name)(values).items():
                    utils.update(cls, attribute_name, func)

        return cls

class Phase:
    def __init__(self, system):
        self.system = system

        def simple_phase(func): return lambda names: {name: func for name in names}

        self.phases = {
            'disable': simple_phase(system.disable),
            'type_attributes': lambda config: simple_phase(config, system.disable)
        }

    def type_attributes(self, config, cls):
        with modify(cls):
            for action_name, attribute_names in config.items():
                for attribute_name, func in self(action_name, attribute_names).items():
                    utils.update(cls, attribute_name, func)

        return cls
    
    def __call__(self, name, config):
        match name:
            case 'disable':
                return {name: self.system.disable for name in config}
            case 'type_attributes':
                return {cls: partial(self.type_attributes, actions) for cls, actions in config.items()}


phases = {
    'disable': lambda system, config: simple_phase(config, system.disable),
    'type_attributes': lambda system, config: simple_phase(config, system.disable)
}

class Phase(ABC):
    """
    A phase is function when called with system and config yields map of name->func
    A patch phase 
    A phase has... keys... and action
    """
    def __init__(self, name):
        self.name = name

    def patch(self, obj):
        return obj

    def patch_with_config(self, config, obj):
        return obj

    @abstractmethod
    def apply(self, name : str, value : Any) -> Any:
        pass

    @abstractmethod
    def __call__(self, namespace : Dict[str, Any]) -> None:
        for name, value in namespace.items():
            if 

    def __call__(self, config):
        if isinstance(config, str):
            return {config: self.patch}
        elif isinstance(config, list):
            return {key: self.patch for key in config}
        elif isinstance(config, dict):
            return {key: lambda obj: self.patch_with_config(value, obj) for key,value in config.items()}
        else:
            raise Exception(f'Unhandled config type: {config}')



class Proxy(Phase):
    
    def proxy()
    def __call__(self, name : str, value : Any) -> None:
        if name in self.targets


class Patch(Phase):

    def __init__(self, targets, action):
        self.targets = targets

    def select(self, name : str) -> bool:
        pass
    
    def __call__(self, name : str, value : Any) -> None:
        if name in self.targets

class SimplePhase(Phase):
    def __init__(self, name, patch):
        super().__init__(name)
        self.patch = patch

class DisablePhase(Phase):
    def __init__(self, thread_state):
        super().__init__('disable')
        self.thread_state = thread_state

    def patch(self, obj):
        print(f'Disabling: {obj}')
        return self.thread_state.wrap('disabled', obj)

class TryPatchPhase(Phase):
    def __init__(self, patcher):
        super().__init__('try_patch')
        self.patcher = patcher

    def patch(self, obj):
        try:
            return self.patcher(obj)
        except:
            return obj

class PatchTypesPhase(Phase):
    def __init__(self, patcher):
        super().__init__('patch_types')
        self.patcher = patcher
    
    def patch(self, obj):
        if not isinstance(obj, type):
            raise Exception("TODO")

        self.patcher(obj)
        return obj

class BindPhase(Phase):
    def __init__(self, bind):
        super().__init__('bind')
        self.bind = bind

    def patch(self, obj):
        # print(f'In BindPhase: {obj} {isinstance(obj, type)}')
        if issubclass(obj, enum.Enum):
            for member in obj:
                # print(f'binding member: {member}')
                # utils.sigtrap(member)
                self.bind(member)
        else:
            self.bind(obj)

        return obj

class ImmutableTypePhase(Phase):

    def __init__(self, types):
        super().__init__('immutable')
        self.types = types

    def patch(self, obj):
        if not isinstance(obj, type):
            raise Exception("TODO")

        self.types.add(obj)
        return obj

class PatchThreadPhase(Phase):
    def __init__(self, thread_state, on_exit):
        super().__init__('patch_start_new_thread')
        self.thread_state = thread_state
        self.on_exit = on_exit

    def patch(self, obj):
        return start_new_thread_wrapper(thread_state = self.thread_state, 
                                        on_exit = self.on_exit,
                                        start_new_thread = obj)

def resolve(path):
    module, sep, name = path.rpartition('.')
    if module == None: module = 'builtins'
    
    return getattr(importlib.import_module(module), name)

class WrapPhase(Phase):
    def __init__(self):
        super().__init__('wrap')

    def patch_with_config(self, wrapper, obj):
        return resolve(wrapper)(obj)

class PatchClassPhase(Phase):
    def __init__(self):
        super().__init__('patch_class')

    def patch_with_config(self, config, cls):

        patchers = utils.map_values(resolve, config)

        assert cls is not None

        with WithoutFlags(cls, "Py_TPFLAGS_IMMUTABLETYPE"):
            for name,func in patchers.items():                
                utils.update(cls, name, func)

        return cls

class ProxyWrapPhase(Phase):
    def __init__(self):
        super().__init__('wrap_proxy')

    def patch_with_config(self, config, cls):

        patchers = utils.map_values(resolve, config)
        
        def patch(proxytype):
            for name,func in patchers.items():
                utils.update(proxytype, name, func)

        cls.__retrace_patch_proxy__ = patch

        return cls
        # return resolve(wrapper)(obj)

class TypeAttributesPhase(Phase):

    def __init__(self, patcher):
        super().__init__('type_attributes')
        self.patcher = patcher

    def patch_with_config(self, config, cls):
        # print(f'TypeAttributesPhase: {config} {cls}')
        if not isinstance(cls, type):
            raise Exception("TODO")

        with modify(cls):
            for phase_name,values in config.items():
                for attribute_name,func in self.patcher.find_phase(phase_name)(values).items():
                    utils.update(cls, attribute_name, func)

        return cls

class PerThread(threading.local):
    def __init__(self):
        self.internal = utils.counter()
        self.external = utils.counter()

class PatchHashPhase(Phase):

    def __init__(self, thread_state):
        super().__init__('patch_hash')

        per_thread = PerThread()
        
        self.hashfunc = thread_state.dispatch(
            functional.constantly(None),
            internal = functional.repeatedly(functional.partial(getattr, per_thread, 'internal')),
            external = functional.repeatedly(functional.partial(getattr, per_thread, 'external')))

    def patch(self, obj):
        if not isinstance(obj, type):
            raise Exception("TODO")

        utils.patch_hash(cls = obj, hashfunc = self.hashfunc)
        return obj
