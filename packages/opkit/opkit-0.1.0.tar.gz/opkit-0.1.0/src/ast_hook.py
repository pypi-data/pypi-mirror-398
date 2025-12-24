"""
Import hook for AST transformation and sitecustomize management
"""

import sys
import importlib.abc
import importlib.util
from pathlib import Path
import sysconfig
from .transform import transform_operators

class OpkitLoader(importlib.abc.SourceLoader):
    """Loader that transforms source before compilation"""
    
    def __init__(self, fullname, path):
        self.fullname = fullname
        self.path = path
    
    def get_filename(self, fullname):
        return self.path
    
    def get_data(self, path):
        with open(path, 'rb') as f:
            return f.read()
    
    def exec_module(self, module):
        # Read source
        source = self.get_data(self.path).decode('utf-8')
        
        # Transform operators
        transformed = transform_operators(source)
        
        # Compile and execute
        code = compile(transformed, self.path, 'exec')
        exec(code, module.__dict__)


class OpkitImportHook(importlib.abc.MetaPathFinder):
    """Import hook that intercepts all imports"""
    
    def find_spec(self, fullname, path, target=None):
        """Find and transform user modules, skipping stdlib and opkit internals."""
        skip_prefixes = (
            '_', 'encodings', 'importlib', 'sys', 'os', 'builtins',
            'numpy', 'pandas', 'collections', 'abc', 'typing', 'io', 're',
            'warnings', 'platform',
            'runtime_ops', 'numpy_ops', 'pandas_ops', 'ast_hook', 'transform', 'ipython_extension'
        )

        # Early exit for opkit itself and known prefixes
        if fullname == 'opkit' or fullname.startswith('opkit.'):
            return None
        if fullname.startswith(skip_prefixes):
            return None

        # Use sys.path if path is None
        search_paths = path or sys.path
        stdlib_path = Path(sysconfig.get_paths().get('stdlib', '')).resolve()

        def is_stdlib(p: Path) -> bool:
            rp = p.resolve()
            return bool(stdlib_path) and (rp == stdlib_path or stdlib_path in rp.parents)

        mod_rel = fullname.replace('.', '/')
        for entry in search_paths:
            entry_path = Path(entry)

            # Check for package
            pkg_path = entry_path / mod_rel / '__init__.py'
            if pkg_path.exists() and not is_stdlib(pkg_path):
                return importlib.util.spec_from_loader(fullname, OpkitLoader(fullname, str(pkg_path)))

            # Check for module
            mod_path = entry_path / f"{mod_rel}.py"
            if mod_path.exists() and not is_stdlib(mod_path):
                return importlib.util.spec_from_loader(fullname, OpkitLoader(fullname, str(mod_path)))

        return None


def install():
    """Install sitecustomize.py stub for automatic activation"""
    import site
    import os
    
    # Find site-packages
    site_packages = site.getsitepackages()[0]
    sitecustomize_path = os.path.join(site_packages, 'sitecustomize.py')
    
    # Simple stub that just imports opkit
    stub = """# opkit auto-activation
try:
    import opkit
except ImportError:
    pass
"""
    
    if os.path.exists(sitecustomize_path):
        with open(sitecustomize_path, 'r') as f:
            existing = f.read()
        
        if 'opkit' in existing:
            print("✓ opkit already installed")
            return
        
        # Append to existing file
        code = existing + "\n" + stub
    else:
        code = stub
    
    with open(sitecustomize_path, 'w') as f:
        f.write(code)
    
    print(f"✓ opkit installed to {sitecustomize_path}")
    print("  Custom operators now work in scripts, REPL, and imported modules!")
    print("  Restart Python for changes to take effect.")


def uninstall():
    """Remove opkit from sitecustomize.py"""
    import site
    import os
    
    site_packages = site.getsitepackages()[0]
    sitecustomize_path = os.path.join(site_packages, 'sitecustomize.py')
    
    if not os.path.exists(sitecustomize_path):
        print("✓ Nothing to uninstall")
        return
    
    with open(sitecustomize_path, 'r') as f:
        content = f.read()
    
    # Check if opkit is in the file
    if 'opkit' not in content:
        print("✓ opkit not found in sitecustomize.py")
        return
    
    # Remove the opkit auto-activation block
    lines = content.split('\n')
    new_lines = []
    skip_count = 0
    
    for i, line in enumerate(lines):
        if 'opkit auto-activation' in line:
            # Skip this comment and the next 4 lines (try:/import opkit/except/pass)
            skip_count = 5
            continue
        
        if skip_count > 0:
            skip_count -= 1
            continue
        
        new_lines.append(line)
    
    new_content = '\n'.join(new_lines).strip()
    
    if new_content:
        with open(sitecustomize_path, 'w') as f:
            f.write(new_content + '\n')
        print("✓ opkit removed from sitecustomize.py")
    else:
        os.remove(sitecustomize_path)
        print("✓ sitecustomize.py removed (was empty after removing opkit)")
    
    print("  Restart Python for changes to take effect.")