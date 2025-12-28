import importlib
import inspect
import pkgutil


def find_classes(package, target: type):
    classes = set()

    # walk_packages recursively goes into subpackages
    for module_info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        _, module_name, is_pkg = module_info

        module = importlib.import_module(module_name)

        # scan classes in this module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                obj.__module__ == module.__name__
                and issubclass(obj, target)
                and obj is not target
            ):
                classes.add(obj)

    return classes
