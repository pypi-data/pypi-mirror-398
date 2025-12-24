import sys
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec
import os
from .transpiler import transpile

class VoltaImporter(MetaPathFinder, Loader):
    def find_spec(self, fullname, path, target=None):
        # We only handle imports that correspond to .vpy files
        if path is None:
            # Top level import?
            # We need to map fullname to file path
            # Simple assumption: look in current dir or sys.path
            pass
            
        # Look for .vpx file in path
        if path:
            for entry in path:
                # entry is a directory
                parts = fullname.split(".")
                py_path = os.path.join(entry, parts[-1] + ".vpx")
                if os.path.exists(py_path):
                     return ModuleSpec(fullname, self, origin=py_path)
        else:
            # Check cwd/sys.path for top level
            parts = fullname.split(".")
            fname = parts[-1] + ".vpx"
            for p in sys.path:
                py_path = os.path.join(p, fname)
                if os.path.exists(py_path):
                     return ModuleSpec(fullname, self, origin=py_path)
                     
        return None

    def create_module(self, spec):
        return None # Default creation

    def exec_module(self, module):
        with open(module.__spec__.origin, "r") as f:
            source = f.read()
        
        # Transpile
        try:
            transpiled = transpile(source)
        except Exception as e:
            raise SyntaxError(f"Failed to transpile Volta JSX in {module.__spec__.origin}: {e}")

        # Inject imports needed (h) if not present?
        transpiled = "from volta import h\n" + transpiled
        
        # Compile and Exec
        code = compile(transpiled, module.__spec__.origin, mode="exec")
        exec(code, module.__dict__)

def install():
    sys.meta_path.insert(0, VoltaImporter())
