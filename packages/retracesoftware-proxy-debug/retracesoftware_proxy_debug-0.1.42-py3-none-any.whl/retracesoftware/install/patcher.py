import enum
from retracesoftware.install.typeutils import modify
from retracesoftware.install.replace import update
import threading
import sys
import retracesoftware.utils as utils
import retracesoftware.functional as functional
import importlib

def resolve(path):
    module, sep, name = path.rpartition('.')

    if module is None:
        module = 'builtins'
    
    return getattr(importlib.import_module(module), name)

def replace(replacements, coll):
    return map(lambda x: replacements.get(x, x), coll)
        
def patch_class(transforms, cls):
    with modify(cls):
        for attr,transform in transforms.items():
            utils.update(cls, attr, resolve(transform))

    return cls

class PerThread(threading.local):
    def __init__(self):
        self.internal = utils.counter()
        self.external = utils.counter()

def create_patcher(system):

    patcher = {}

    def foreach(func): return lambda config: {name: func for name in config}
    def selector(func): return lambda config: {name: functional.partial(func, value) for name, value in config.items()}

    def simple_patcher(func): return foreach(functional.side_effect(func))

    def type_attributes(transforms, cls):
        with modify(cls):
            for action, attrs in transforms.items():
                for attr,func in patcher[action](attrs).items():
                    utils.update(cls, attr, func)
        return cls

    def bind(obj):
        if issubclass(obj, enum.Enum):
            for member in obj:
                system.bind(member)
        else:
            system.bind(obj)

    def add_immutable_type(obj):
        if not isinstance(obj, type):
            raise Exception("TODO")
        system.immutable_types.add(obj)
        return obj

    per_thread = PerThread()
        
    hashfunc = system.thread_state.dispatch(
        functional.constantly(None),
        internal = functional.repeatedly(functional.partial(getattr, per_thread, 'internal')),
        external = functional.repeatedly(functional.partial(getattr, per_thread, 'external')))

    def patch_hash(obj):
        if not isinstance(obj, type):
            raise Exception("TODO")

        utils.patch_hash(cls = obj, hashfunc = hashfunc)
        return obj
    
    patcher.update({
        'type_attributes': selector(type_attributes),
        'patch_class': selector(patch_class),
        'disable': foreach(system.disable_for),
        'patch_types': simple_patcher(system.patch_type),
        'proxy': foreach(system),
        'bind': simple_patcher(bind),
        'wrap': lambda config: {name: resolve(action) for name,action in config.items() },
        'immutable': simple_patcher(add_immutable_type),
        'patch_hash': simple_patcher(patch_hash),
    })
    return patcher

def patch_namespace(patcher, config, namespace, update_refs):
    for phase_name, phase_config in config.items():
        if phase_name in patcher:
            for name,func in patcher[phase_name](phase_config).items():
                if name in namespace:
                    # print(f"patching: {name}")

                    value = namespace[name]
                    new_value = func(value)

                    if value is not new_value:
                        namespace[name] = new_value

                        if update_refs:
                            update(value, new_value)
        else:
            print(phase_name)
            utils.sigtrap('FOO1')
    
def patch_module(patcher, config, namespace, update_refs):
    if '__name__' in namespace:
        name = namespace['__name__']
        if name in config:
            patch_namespace(patcher, config = config[name], namespace=namespace, update_refs=update_refs)

def patch_imported_module(patcher, checkpoint, config, namespace, update_refs):
    if '__name__' in namespace:
        name = namespace['__name__']
        checkpoint(f"importing module: {name}")

        if name in config:
            # print(f"Patching imported module: {name}")
            # checkpoint(f"Patching imported module: {name}")
            patch_namespace(patcher, config = config[name], namespace=namespace, update_refs=update_refs)
