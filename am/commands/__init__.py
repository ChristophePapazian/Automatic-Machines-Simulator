# coding: utf-8

def load_commands():
    """
    Dynamically load commands from the current directory
    """
    from os.path import dirname, basename, join, splitext
    import glob
    import importlib
    for mod in glob.glob(join(dirname(__file__), "[!_]*")):
        importlib.import_module(f"am.commands.{splitext(basename(mod))[0]}")


COMMANDS = {}


def cmd(*args):
    def inner(fct):
        COMMANDS[fct.__name__] = args, fct
        return fct

    return inner
