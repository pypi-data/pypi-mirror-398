if __name__ == "__main__":
    import sysconfig
    import pathlib

    # 'purelib' is the name of the directory where non-platform-specific modules are installed.
    file = pathlib.Path(sysconfig.get_paths()["purelib"]) / 'retrace.pth'
    file.write_text('import retracesoftware.autoenable;', encoding='utf-8')

    print(f'Retrace autoinstall enabled by creating: {file}')
else:
    import os

    def is_true(name):
        if name in os.environ:
            return os.environ[name].lower() in {'true', '1', 't', 'y', 'yes'}
        else:
            return False
            
    def is_running_retrace():
        return sys.orig_argv[1] == '-m' and sys.orig_argv[2].startswith('retracesoftware')
    
    # only do anything is the RETRACE env variable is set
    if is_true('RETRACE'):
        import sys

        if not is_running_retrace():
            
            new_argv = [sys.orig_argv[0], '-m', 'retracesoftware']

            if is_true('RETRACE_VERBOSE'):
                new_argv.append('--verbose')

            if 'RETRACE_RECORDING_PATH' in os.environ:
                new_argv.append('--recording')
                new_argv.append(os.environ['RETRACE_RECORDING_PATH'])

            if is_true('RETRACE_STACKTRACES'):
                new_argv.append('--stacktraces')

            if is_true('RETRACE_SHUTDOWN'):
                new_argv.append('--trace_shutdown')

            if is_true('RETRACE_MAGIC_MARKERS'):
                new_argv.append('--magic_markers')

            if is_true('RETRACE_TRACE_INPUTS'):
                new_argv.append('--trace_inputs')

            new_argv.append('--')
            new_argv.extend(sys.orig_argv[1:])
            
            # print(f'Running: {new_argv}')
            os.execv(sys.executable, new_argv)
